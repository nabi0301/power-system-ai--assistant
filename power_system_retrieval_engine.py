"""
Advanced Retrieval System for Power System RAG
=============================================

This module implements sophisticated retrieval with:
- Multi-stage retrieval pipeline
- Cross-encoder re-ranking
- Query expansion and preprocessing
- Power system context optimization

Key Features:
- k=5-10 initial retrieval
- Re-ranking with cross-encoder models
- Query preprocessing for power system terms
- Contextual filtering and boosting
- Hybrid search integration

Author: Power System Analysis Team
Date: September 2025
"""

import numpy as np
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio

# Try imports for re-ranking
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logging.warning("Cross-encoder re-ranking not available")

# Import our components
from power_system_vector_db import PowerSystemVectorDB, SearchResult, SearchQuery
from power_system_embeddings_engine import PowerSystemEmbeddingsEngine

logger = logging.getLogger(__name__)

@dataclass
class RetrievalQuery:
    """Enhanced query for retrieval system"""
    original_query: str
    processed_query: str
    query_type: str  # "analysis", "troubleshooting", "data", "general"
    bus_entities: List[str]
    branch_entities: List[str]  
    power_entities: List[str]
    case_context: Optional[str] = None
    priority_areas: List[str] = None

@dataclass
class RetrievalResult:
    """Enhanced retrieval result with re-ranking"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    vector_score: float  # Original vector similarity
    rerank_score: float  # Re-ranking score
    final_score: float   # Combined final score
    relevance_explanation: str
    rank: int

class PowerSystemQueryProcessor:
    """
    Advanced query processor for power system queries.
    
    Handles:
    - Entity extraction (buses, branches, equipment)
    - Query type classification
    - Query expansion with domain terms
    - Context enrichment
    """
    
    def __init__(self):
        """Initialize query processor"""
        # Power system entity patterns
        self.bus_patterns = [
            r'bus[_\s]*(\d+)',
            r'node[_\s]*(\d+)',
            r'station[_\s]*(\d+)',
            r'substation[_\s]*(\d+)'
        ]
        
        self.branch_patterns = [
            r'line[_\s]*(\d+)',
            r'branch[_\s]*(\d+)', 
            r'transmission[_\s]*line[_\s]*(\d+)',
            r'circuit[_\s]*(\d+)'
        ]
        
        self.power_patterns = [
            r'(\d+\.?\d*)\s*(mw|megawatt|MW)',
            r'(\d+\.?\d*)\s*(mvar|megavar|MVAR)',
            r'(\d+\.?\d*)\s*(kv|kilovolt|KV)',
            r'(\d+\.?\d*)\s*(kw|kilowatt|KW)'
        ]
        
        # Query type keywords
        self.query_types = {
            'analysis': [
                'analyze', 'analysis', 'study', 'calculate', 'compute',
                'assess', 'evaluate', 'determine', 'find', 'statistics'
            ],
            'troubleshooting': [
                'problem', 'issue', 'error', 'failure', 'fault', 'alarm',
                'violation', 'outage', 'contingency', 'emergency'
            ],
            'data': [
                'show', 'display', 'list', 'get', 'retrieve', 'data',
                'table', 'values', 'records', 'information'
            ]
        }
        
        # Domain-specific expansions
        self.term_expansions = {
            'voltage': ['vm', 'voltage magnitude', 'per unit voltage', 'pu voltage'],
            'power': ['mw', 'megawatt', 'real power', 'active power'],
            'reactive': ['mvar', 'megavar', 'reactive power', 'vars'],
            'loading': ['thermal loading', 'line loading', 'percent loading'],
            'rating': ['thermal rating', 'ampacity', 'current rating'],
            'dlr': ['dynamic line rating', 'dynamic rating', 'real-time rating'],
            'slr': ['static line rating', 'static rating', 'fixed rating']
        }
    
    def process_query(self, query: str) -> RetrievalQuery:
        """
        Process and enhance a user query.
        
        Args:
            query: Original user query
            
        Returns:
            Enhanced RetrievalQuery object
        """
        logger.info(f"Processing query: {query[:100]}...")
        
        # Extract entities
        bus_entities = self._extract_buses(query)
        branch_entities = self._extract_branches(query)
        power_entities = self._extract_power_values(query)
        
        # Classify query type
        query_type = self._classify_query_type(query)
        
        # Expand and enhance query
        processed_query = self._expand_query(query)
        
        # Determine priority areas
        priority_areas = self._identify_priority_areas(query)
        
        result = RetrievalQuery(
            original_query=query,
            processed_query=processed_query,
            query_type=query_type,
            bus_entities=bus_entities,
            branch_entities=branch_entities,
            power_entities=power_entities,
            priority_areas=priority_areas
        )
        
        logger.info(f"Query processed: type={query_type}, buses={len(bus_entities)}, branches={len(branch_entities)}")
        return result
    
    def _extract_buses(self, query: str) -> List[str]:
        """Extract bus identifiers from query"""
        buses = []
        for pattern in self.bus_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                buses.append(match.group(1))
        return list(set(buses))
    
    def _extract_branches(self, query: str) -> List[str]:
        """Extract branch identifiers from query"""
        branches = []
        for pattern in self.branch_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                branches.append(match.group(1))
        return list(set(branches))
    
    def _extract_power_values(self, query: str) -> List[str]:
        """Extract power values and units from query"""
        values = []
        for pattern in self.power_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                values.append(f"{match.group(1)} {match.group(2)}")
        return values
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()
        
        type_scores = {}
        
        for query_type, keywords in self.query_types.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            type_scores[query_type] = score
        
        # Return the type with highest score
        if type_scores:
            return max(type_scores, key=type_scores.get)
        else:
            return 'general'
    
    def _expand_query(self, query: str) -> str:
        """Expand query with domain-specific terms"""
        expanded = query.lower()
        
        for term, expansions in self.term_expansions.items():
            if term in expanded:
                # Add expansion terms
                expansion_text = ' ' + ' '.join(expansions)
                expanded += expansion_text
        
        return expanded
    
    def _identify_priority_areas(self, query: str) -> List[str]:
        """Identify priority areas for enhanced retrieval"""
        areas = []
        query_lower = query.lower()
        
        area_keywords = {
            'voltage_analysis': ['voltage', 'vm', 'per unit', 'voltage magnitude'],
            'power_flow': ['power flow', 'pf', 'qt', 'real power', 'reactive'],
            'thermal_analysis': ['thermal', 'rating', 'loading', 'ampacity'],
            'contingency': ['contingency', 'outage', 'n-1', 'failure'],
            'dlr_analysis': ['dlr', 'dynamic', 'real-time', 'temperature']
        }
        
        for area, keywords in area_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                areas.append(area)
        
        return areas

class PowerSystemRetriever:
    """
    Advanced retrieval system for power system RAG.
    
    Multi-stage pipeline:
    1. Query processing and enhancement
    2. Initial vector retrieval (k=5-10)
    3. Cross-encoder re-ranking
    4. Context boosting and filtering
    5. Final result compilation
    """
    
    def __init__(
        self,
        vector_db: PowerSystemVectorDB,
        embeddings_engine: PowerSystemEmbeddingsEngine,
        rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-2-v2",
        initial_k: int = 20,
        final_k: int = 10
    ):
        """
        Initialize retriever.
        
        Args:
            vector_db: Vector database instance
            embeddings_engine: Embeddings engine
            rerank_model: Cross-encoder model for re-ranking
            initial_k: Initial retrieval count
            final_k: Final result count
        """
        self.vector_db = vector_db
        self.embeddings_engine = embeddings_engine
        self.initial_k = initial_k
        self.final_k = final_k
        
        # Initialize query processor
        self.query_processor = PowerSystemQueryProcessor()
        
        # Initialize re-ranker
        self.reranker = None
        if CROSS_ENCODER_AVAILABLE:
            try:
                self.reranker = CrossEncoder(rerank_model)
                logger.info(f"Initialized cross-encoder re-ranker: {rerank_model}")
            except Exception as e:
                logger.warning(f"Failed to load re-ranker: {e}")
        
        logger.info("PowerSystemRetriever initialized")
    
    async def retrieve(
        self,
        query: str,
        case_id: Optional[str] = None,
        bus_filter: Optional[List[str]] = None,
        k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        Main retrieval method.
        
        Args:
            query: User query
            case_id: Filter by case ID
            bus_filter: Filter by bus IDs
            k: Number of final results (defaults to self.final_k)
            
        Returns:
            List of retrieval results
        """
        if k is None:
            k = self.final_k
        
        logger.info(f"Starting retrieval for query: {query[:100]}...")
        
        # Stage 1: Query processing
        processed_query = self.query_processor.process_query(query)
        
        # Stage 2: Get query embedding
        query_embedding = await self._get_query_embedding(processed_query.processed_query)
        
        # Stage 3: Initial vector retrieval
        initial_results = await self._initial_retrieval(
            processed_query, query_embedding, case_id, bus_filter
        )
        
        if not initial_results:
            logger.warning("No initial results found")
            return []
        
        # Stage 4: Re-ranking
        reranked_results = await self._rerank_results(processed_query, initial_results)
        
        # Stage 5: Context boosting
        boosted_results = await self._apply_context_boosting(processed_query, reranked_results)
        
        # Stage 6: Final selection and ranking
        final_results = self._finalize_results(boosted_results, k)
        
        logger.info(f"Retrieval complete: {len(final_results)} final results")
        return final_results
    
    async def _get_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """Get embedding for query"""
        try:
            results = await self.embeddings_engine.embed_documents([query])
            if results and results[0].success:
                return results[0].embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
        
        return None
    
    async def _initial_retrieval(
        self,
        processed_query: RetrievalQuery,
        query_embedding: Optional[np.ndarray],
        case_id: Optional[str],
        bus_filter: Optional[List[str]]
    ) -> List[SearchResult]:
        """Initial vector-based retrieval"""
        
        # Use bus entities from query if no filter provided
        if bus_filter is None and processed_query.bus_entities:
            bus_filter = processed_query.bus_entities
        
        # Perform vector search
        results = self.vector_db.search(
            query_text=processed_query.processed_query,
            query_embedding=query_embedding,
            k=self.initial_k,
            case_id_filter=case_id,
            bus_id_filter=bus_filter,
            similarity_threshold=0.0  # Very low threshold for initial retrieval
        )
        
        logger.info(f"Initial retrieval found {len(results)} candidates")
        return results
    
    async def _rerank_results(
        self,
        processed_query: RetrievalQuery,
        results: List[SearchResult]
    ) -> List[RetrievalResult]:
        """Re-rank results using cross-encoder"""
        
        reranked = []
        
        if self.reranker is None:
            # No re-ranker available, use vector scores
            for i, result in enumerate(results):
                reranked_result = RetrievalResult(
                    chunk_id=result.chunk_id,
                    content=result.content,
                    metadata=result.metadata,
                    vector_score=result.similarity_score,
                    rerank_score=result.similarity_score,
                    final_score=result.similarity_score,
                    relevance_explanation="Vector similarity only",
                    rank=i + 1
                )
                reranked.append(reranked_result)
        else:
            # Use cross-encoder for re-ranking
            try:
                # Prepare pairs for re-ranking
                pairs = []
                for result in results:
                    pairs.append([processed_query.original_query, result.content])
                
                # Get re-ranking scores
                rerank_scores = self.reranker.predict(pairs)
                
                # Combine with vector scores
                for i, (result, rerank_score) in enumerate(zip(results, rerank_scores)):
                    # Combine vector and rerank scores (weighted average)
                    final_score = 0.3 * result.similarity_score + 0.7 * float(rerank_score)
                    
                    explanation = f"Vector: {result.similarity_score:.3f}, Rerank: {rerank_score:.3f}"
                    
                    reranked_result = RetrievalResult(
                        chunk_id=result.chunk_id,
                        content=result.content,
                        metadata=result.metadata,
                        vector_score=result.similarity_score,
                        rerank_score=float(rerank_score),
                        final_score=final_score,
                        relevance_explanation=explanation,
                        rank=i + 1
                    )
                    reranked.append(reranked_result)
                
                # Sort by final score
                reranked.sort(key=lambda x: x.final_score, reverse=True)
                
                # Update ranks
                for i, result in enumerate(reranked):
                    result.rank = i + 1
                
                logger.info("Re-ranking completed with cross-encoder")
                
            except Exception as e:
                logger.error(f"Re-ranking failed: {e}")
                # Fallback to vector scores
                return await self._rerank_results_fallback(processed_query, results)
        
        return reranked
    
    async def _rerank_results_fallback(
        self,
        processed_query: RetrievalQuery,
        results: List[SearchResult]
    ) -> List[RetrievalResult]:
        """Fallback re-ranking using simple rules"""
        reranked = []
        
        for i, result in enumerate(results):
            # Simple boosting based on query type and entities
            boost_factor = 1.0
            
            # Boost if content contains entities from query
            content_lower = result.content.lower()
            
            # Bus entity boost
            for bus_id in processed_query.bus_entities:
                if bus_id in content_lower:
                    boost_factor *= 1.2
            
            # Query type specific boosts
            if processed_query.query_type == 'analysis' and 'analysis' in content_lower:
                boost_factor *= 1.1
            elif processed_query.query_type == 'data' and 'data' in content_lower:
                boost_factor *= 1.1
            
            final_score = result.similarity_score * boost_factor
            
            reranked_result = RetrievalResult(
                chunk_id=result.chunk_id,
                content=result.content,
                metadata=result.metadata,
                vector_score=result.similarity_score,
                rerank_score=boost_factor,
                final_score=final_score,
                relevance_explanation=f"Vector + rule boost: {boost_factor:.2f}",
                rank=i + 1
            )
            reranked.append(reranked_result)
        
        # Sort by final score
        reranked.sort(key=lambda x: x.final_score, reverse=True)
        
        # Update ranks
        for i, result in enumerate(reranked):
            result.rank = i + 1
        
        return reranked
    
    async def _apply_context_boosting(
        self,
        processed_query: RetrievalQuery,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Apply context-aware boosting"""
        
        # Priority area boosting
        for result in results:
            content_lower = result.content.lower()
            metadata = result.metadata
            
            additional_boost = 1.0
            
            # Boost based on priority areas
            for area in processed_query.priority_areas:
                if area == 'voltage_analysis' and any(term in content_lower for term in ['voltage', 'vm', 'per unit']):
                    additional_boost *= 1.15
                elif area == 'thermal_analysis' and any(term in content_lower for term in ['thermal', 'loading', 'rating']):
                    additional_boost *= 1.15
                elif area == 'dlr_analysis' and 'dlr' in content_lower:
                    additional_boost *= 1.2
            
            # Metadata relevance boosting
            if processed_query.bus_entities:
                doc_bus_ids = metadata.get('bus_ids', [])
                if isinstance(doc_bus_ids, str):
                    doc_bus_ids = eval(doc_bus_ids) if doc_bus_ids.startswith('[') else [doc_bus_ids]
                
                matching_buses = set(processed_query.bus_entities) & set(str(bid) for bid in doc_bus_ids)
                if matching_buses:
                    additional_boost *= (1.1 + 0.05 * len(matching_buses))
            
            # Apply boost
            result.final_score *= additional_boost
            result.relevance_explanation += f", Context boost: {additional_boost:.2f}"
        
        # Re-sort after boosting
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Update ranks
        for i, result in enumerate(results):
            result.rank = i + 1
        
        return results
    
    def _finalize_results(self, results: List[RetrievalResult], k: int) -> List[RetrievalResult]:
        """Finalize and limit results"""
        
        # Remove duplicates by chunk_id
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result.chunk_id not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result.chunk_id)
        
        # Limit to k results
        final_results = unique_results[:k]
        
        # Final rank adjustment
        for i, result in enumerate(final_results):
            result.rank = i + 1
        
        return final_results
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics"""
        return {
            "initial_k": self.initial_k,
            "final_k": self.final_k,
            "has_reranker": self.reranker is not None,
            "vector_db_stats": self.vector_db.get_stats()
        }


# Export main classes
__all__ = [
    'PowerSystemRetriever', 'RetrievalQuery', 'RetrievalResult',
    'PowerSystemQueryProcessor'
]