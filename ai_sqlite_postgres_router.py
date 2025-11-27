# ai_sqlite_postgres_router.py
import hashlib
from typing import Dict, Any, Tuple, Optional
from sqlite_postgres_manager import SQLitePostgreSQLManager
from entity_extraction import extract_case_and_entity_info

class SQLitePostgreSQLAIRouter:
    """Routes AI requests to appropriate databases and handles caching"""
    
    def __init__(self, manager: SQLitePostgreSQLManager):
        self.manager = manager
        
        # Intent detection keywords
        self.visualization_keywords = [
            'show', 'display', 'plot', 'graph', 'chart', 'visualize', 'draw',
            'network', 'voltage', 'branch', 'bus', 'generator', 'comparison',
            'analysis', 'case', 'contingency', 'dlr', 'slr', 'loading'
        ]
        
        self.qa_keywords = [
            'what', 'why', 'how', 'explain', 'define', 'meaning', 'difference',
            'help', 'understand', 'learn', 'tell me', 'describe', 'concept'
        ]
    
    def route_request(self, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Route user request to appropriate database and processing method"""
        
        # Generate query hash for caching
        query_hash = self._generate_query_hash(user_message)
        
        # Check cache first
        cached_result = self.manager.get_cached_result(query_hash)
        if cached_result:
            return 'cached', {
                'data': cached_result,
                'query_hash': query_hash
            }
        
        # Determine intent
        intent_type = self._detect_intent(user_message)
        
        if intent_type == 'visualization':
            return self._route_visualization_request(user_message, query_hash)
        elif intent_type == 'qa':
            return self._route_qa_request(user_message, query_hash)
        else:
            # Default to QA for ambiguous requests
            return self._route_qa_request(user_message, query_hash)
    
    def _detect_intent(self, user_message: str) -> str:
        """Detect whether user wants visualization or Q&A"""
        message_lower = user_message.lower()
        
        viz_score = sum(1 for keyword in self.visualization_keywords if keyword in message_lower)
        qa_score = sum(1 for keyword in self.qa_keywords if keyword in message_lower)
        
        # Additional heuristics
        if any(phrase in message_lower for phrase in ['case', 'contingency', 'bus', 'branch']):
            viz_score += 2
            
        if any(phrase in message_lower for phrase in ['what is', 'how does', 'explain', 'difference between']):
            qa_score += 2
        
        return 'visualization' if viz_score > qa_score else 'qa'
    
    def _route_visualization_request(self, user_message: str, query_hash: str) -> Tuple[str, Dict[str, Any]]:
        """Route visualization requests"""
        
        # Extract entities using existing function
        entity_info = extract_case_and_entity_info(user_message)
        
        case_id = entity_info.get('case_id', 0)
        contingency_id = entity_info.get('contingency_id')
        
        # Determine visualization type from message
        viz_type = self._determine_viz_type(user_message)
        
        return 'visualization', {
            'case_id': case_id,
            'contingency_id': contingency_id,
            'viz_type': viz_type,
            'query_hash': query_hash,
            'entity_info': entity_info
        }
    
    def _route_qa_request(self, user_message: str, query_hash: str) -> Tuple[str, Dict[str, Any]]:
        """Route Q&A requests to knowledge base"""
        
        # Extract key terms for search
        search_terms = self._extract_search_terms(user_message)
        category = self._determine_category(user_message)
        
        return 'qa', {
            'search_term': search_terms,
            'category': category,
            'query_hash': query_hash,
            'original_message': user_message
        }
    
    def _determine_viz_type(self, user_message: str) -> str:
        """Determine visualization type from user message"""
        message_lower = user_message.lower()
        
        if any(term in message_lower for term in ['network', 'topology', 'graph']):
            if any(term in message_lower for term in ['comparison', 'compare', 'vs', 'versus']):
                return 'dual_network'
            return 'network_view'
        elif any(term in message_lower for term in ['voltage', 'bus']):
            return 'voltage'
        elif any(term in message_lower for term in ['branch', 'loading', 'thermal']):
            return 'loading'
        elif any(term in message_lower for term in ['generator', 'generation']):
            return 'generators'
        elif any(term in message_lower for term in ['dlr', 'slr', 'dynamic', 'static']):
            return 'comparison'
        else:
            return 'network_view'
    
    def _extract_search_terms(self, user_message: str) -> str:
        """Extract key search terms from user message"""
        # Remove common question words and extract key terms
        stop_words = {'what', 'is', 'the', 'how', 'does', 'why', 'when', 'where', 'a', 'an', 'and', 'or', 'but'}
        
        words = user_message.lower().split()
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Return first few meaningful terms
        return ' '.join(key_terms[:3])
    
    def _determine_category(self, user_message: str) -> Optional[str]:
        """Determine knowledge base category from user message"""
        message_lower = user_message.lower()
        
        if any(term in message_lower for term in ['voltage', 'reactive', 'regulation']):
            return 'voltage_control'
        elif any(term in message_lower for term in ['transmission', 'line', 'dlr', 'slr', 'rating']):
            return 'transmission'
        elif any(term in message_lower for term in ['contingency', 'reliability', 'n-1', 'outage']):
            return 'reliability'
        elif any(term in message_lower for term in ['power flow', 'load flow', 'analysis']):
            return 'analysis'
        elif any(term in message_lower for term in ['bus', 'generator', 'load', 'slack', 'pv', 'pq']):
            return 'fundamentals'
        else:
            return None
    
    def _generate_query_hash(self, query: str) -> str:
        """Generate hash for caching"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about routing decisions"""
        # This could be enhanced to track routing patterns
        return {
            'visualization_keywords': len(self.visualization_keywords),
            'qa_keywords': len(self.qa_keywords),
            'cache_enabled': True
        }