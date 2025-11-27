#!/usr/bin/env python3
"""
Power System RAG (Retrieval-Augmented Generation) Implementation
Advanced AI assistant with database knowledge integration
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any
import json
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

class PowerSystemRAG:
    """
    RAG system specifically designed for IEEE 118-bus power system analysis
    Combines database retrieval with AI generation for intelligent responses
    """
    
    def __init__(self, db_path: str = 'data.db'):
        """Initialize RAG system with power system database"""
        self.db_path = db_path
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Power system knowledge base
        self.power_system_knowledge = self._build_knowledge_base()
        self.knowledge_embeddings = self._compute_knowledge_embeddings()
        
        # Query templates for different analysis types
        self.query_templates = {
            'voltage_analysis': """
                SELECT BUS_NUMBER, VM, VA, BASE_KV, PD, QD 
                FROM BaseBusData 
                WHERE base_case_id = 0 AND ({condition})
                ORDER BY {order_by} 
                LIMIT {limit}
            """,
            'loading_analysis': """
                SELECT From_Bus, To_Bus, MVA, RATE, PF, QF,
                       CASE WHEN RATE > 0 THEN (MVA/RATE*100) ELSE 0 END as loading_pct
                FROM BaseBranchData 
                WHERE base_case_id = 0 AND ({condition})
                ORDER BY {order_by} 
                LIMIT {limit}
            """,
            'generator_analysis': """
                SELECT BUS_NUMBER, KV_LEVEL, GEN_INI, GEN_NEW, GEN_ADJ
                FROM SLR_Generator 
                WHERE {condition}
                ORDER BY {order_by} 
                LIMIT {limit}
            """,
            'contingency_analysis': """
                SELECT s.From_Bus, s.To_Bus, s.MVA as SLR_MVA, d.MVA as DLR_MVA,
                       s.RATE as SLR_Rating, d.RATE as DLR_Rating,
                       s.VIO as SLR_Violation, d.VIO as DLR_Violation
                FROM SLR_Branches s
                JOIN DLR_Branches d ON s.From_Bus = d.From_Bus AND s.To_Bus = d.To_Bus
                WHERE {condition}
                ORDER BY {order_by} 
                LIMIT {limit}
            """
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _build_knowledge_base(self) -> List[Dict]:
        """Build comprehensive power system knowledge base"""
        knowledge_base = [
            {
                "topic": "voltage_violations",
                "description": "Bus voltage outside acceptable limits (0.95-1.05 p.u.)",
                "keywords": ["voltage", "violation", "low voltage", "high voltage", "bus voltage", "voltage magnitude"],
                "query_type": "voltage_analysis",
                "condition": "VM < 0.95 OR VM > 1.05",
                "order_by": "ABS(VM - 1.0) DESC"
            },
            {
                "topic": "overloaded_lines",
                "description": "Transmission lines exceeding thermal capacity (>100% loading)",
                "keywords": ["overload", "thermal limit", "line loading", "capacity", "MVA", "thermal rating"],
                "query_type": "loading_analysis", 
                "condition": "RATE > 0 AND (MVA/RATE) > 1.0",
                "order_by": "(MVA/RATE) DESC"
            },
            {
                "topic": "high_loading_lines",
                "description": "Lines operating at high capacity (>90% loading)",
                "keywords": ["high loading", "stressed lines", "near capacity", "90%", "heavy loading"],
                "query_type": "loading_analysis",
                "condition": "RATE > 0 AND (MVA/RATE) > 0.9",
                "order_by": "(MVA/RATE) DESC"
            },
            {
                "topic": "low_voltage_buses",
                "description": "Buses with voltage below 0.95 p.u.",
                "keywords": ["low voltage", "voltage drop", "under voltage", "0.95"],
                "query_type": "voltage_analysis",
                "condition": "VM < 0.95",
                "order_by": "VM ASC"
            },
            {
                "topic": "high_voltage_buses", 
                "description": "Buses with voltage above 1.05 p.u.",
                "keywords": ["high voltage", "over voltage", "voltage rise", "1.05"],
                "query_type": "voltage_analysis",
                "condition": "VM > 1.05", 
                "order_by": "VM DESC"
            },
            {
                "topic": "heavy_load_buses",
                "description": "Buses with high power demand",
                "keywords": ["heavy load", "high demand", "load centers", "power demand", "MW"],
                "query_type": "voltage_analysis",
                "condition": "PD > 50",
                "order_by": "PD DESC"
            },
            {
                "topic": "generator_buses",
                "description": "Buses with power generation",
                "keywords": ["generator", "generation", "power plant", "generator bus"],
                "query_type": "voltage_analysis", 
                "condition": "PG > 0",
                "order_by": "PG DESC"
            },
            {
                "topic": "slr_dlr_comparison",
                "description": "Comparison between Static and Dynamic Line Ratings",
                "keywords": ["SLR", "DLR", "static rating", "dynamic rating", "comparison", "efficiency"],
                "query_type": "contingency_analysis",
                "condition": "s.base_case_id = 42 AND s.contingency_case_id = 123",
                "order_by": "(d.RATE - s.RATE) DESC"
            },
            {
                "topic": "voltage_angle_differences",
                "description": "Large voltage angle differences indicating system stress",
                "keywords": ["angle", "phase angle", "stability", "voltage angle", "system stress"],
                "query_type": "voltage_analysis",
                "condition": "ABS(VA) > 15",
                "order_by": "ABS(VA) DESC"
            },
            {
                "topic": "system_summary",
                "description": "Overall power system statistics and health",
                "keywords": ["system overview", "summary", "statistics", "total", "overall", "system health"],
                "query_type": "voltage_analysis",
                "condition": "1=1",
                "order_by": "BUS_NUMBER"
            }
        ]
        return knowledge_base
    
    def _compute_knowledge_embeddings(self) -> np.ndarray:
        """Compute embeddings for knowledge base entries"""
        texts = []
        for kb_item in self.power_system_knowledge:
            # Combine topic, description, and keywords for embedding
            text = f"{kb_item['topic']} {kb_item['description']} {' '.join(kb_item['keywords'])}"
            texts.append(text)
        
        embeddings = self.embedding_model.encode(texts)
        return embeddings
    
    def _semantic_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Find most relevant knowledge base entries using semantic similarity"""
        query_embedding = self.embedding_model.encode([query])
        
        # Compute cosine similarity
        similarities = cosine_similarity(query_embedding, self.knowledge_embeddings)[0]
        
        # Get top-k most similar entries
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        relevant_knowledge = []
        for idx in top_indices:
            if similarities[idx] > 0.3:  # Similarity threshold
                knowledge_item = self.power_system_knowledge[idx].copy()
                knowledge_item['similarity'] = float(similarities[idx])
                relevant_knowledge.append(knowledge_item)
        
        return relevant_knowledge
    
    def _execute_database_query(self, knowledge_item: Dict, limit: int = 10) -> pd.DataFrame:
        """Execute database query based on knowledge item"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query_template = self.query_templates[knowledge_item['query_type']]
            query = query_template.format(
                condition=knowledge_item['condition'],
                order_by=knowledge_item['order_by'],
                limit=limit
            )
            
            self.logger.info(f"Executing query: {query}")
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Database query error: {e}")
            return pd.DataFrame()
    
    def _format_data_for_ai(self, data: pd.DataFrame, knowledge_item: Dict) -> str:
        """Format retrieved data for AI consumption"""
        if data.empty:
            return f"No data found for {knowledge_item['topic']}"
        
        formatted_text = f"\n**{knowledge_item['topic'].upper()} DATA:**\n"
        formatted_text += f"Description: {knowledge_item['description']}\n"
        formatted_text += f"Records found: {len(data)}\n\n"
        
        # Format data based on query type
        if knowledge_item['query_type'] == 'voltage_analysis':
            formatted_text += "Bus Analysis:\n"
            for _, row in data.head(5).iterrows():
                formatted_text += f"• Bus {int(row['BUS_NUMBER'])}: {row['VM']:.3f} p.u., Load: {row['PD']:.1f} MW, Base: {row['BASE_KV']:.0f} kV\n"
                
        elif knowledge_item['query_type'] == 'loading_analysis':
            formatted_text += "Line Loading Analysis:\n"
            for _, row in data.head(5).iterrows():
                loading = row.get('loading_pct', 0)
                formatted_text += f"• Line {int(row['From_Bus'])}-{int(row['To_Bus'])}: {loading:.1f}% loading, {row['MVA']:.1f}/{row['RATE']:.1f} MVA\n"
                
        elif knowledge_item['query_type'] == 'contingency_analysis':
            formatted_text += "SLR vs DLR Comparison:\n"
            for _, row in data.head(5).iterrows():
                improvement = row['DLR_Rating'] - row['SLR_Rating']
                formatted_text += f"• Line {int(row['From_Bus'])}-{int(row['To_Bus'])}: SLR {row['SLR_Rating']:.1f} MVA → DLR {row['DLR_Rating']:.1f} MVA (+{improvement:.1f})\n"
        
        if len(data) > 5:
            formatted_text += f"... and {len(data) - 5} more records\n"
        
        # Add statistical summary
        if knowledge_item['query_type'] == 'voltage_analysis' and 'VM' in data.columns:
            formatted_text += f"\nVoltage Statistics: Min: {data['VM'].min():.3f}, Max: {data['VM'].max():.3f}, Avg: {data['VM'].mean():.3f} p.u.\n"
        elif knowledge_item['query_type'] == 'loading_analysis' and 'loading_pct' in data.columns:
            formatted_text += f"\nLoading Statistics: Min: {data['loading_pct'].min():.1f}%, Max: {data['loading_pct'].max():.1f}%, Avg: {data['loading_pct'].mean():.1f}%\n"
        
        return formatted_text
    
    def _detect_question_intent(self, question: str) -> Dict:
        """Analyze question to determine intent and parameters"""
        question_lower = question.lower()
        
        intent_patterns = {
            'count': ['how many', 'count', 'number of', 'total'],
            'find': ['find', 'show', 'list', 'which', 'what'],
            'compare': ['compare', 'difference', 'vs', 'versus', 'better'],
            'analyze': ['analyze', 'analysis', 'pattern', 'trend'],
            'explain': ['explain', 'why', 'how', 'what causes', 'reason']
        }
        
        detected_intent = 'find'  # default
        for intent, patterns in intent_patterns.items():
            if any(pattern in question_lower for pattern in patterns):
                detected_intent = intent
                break
        
        # Extract numerical limits if mentioned
        limit = 10  # default
        limit_match = re.search(r'top\s+(\d+)|first\s+(\d+)|(\d+)\s+most', question_lower)
        if limit_match:
            limit = int(next(filter(None, limit_match.groups())))
        
        return {
            'intent': detected_intent,
            'limit': min(limit, 50)  # Cap at 50 records
        }
    
    def retrieve_and_generate(self, user_question: str, current_viz_type: str = 'network') -> Tuple[str, str]:
        """
        Main RAG function: retrieve relevant data and generate AI response
        Returns: (ai_response, visualization_command)
        """
        
        # Step 1: Semantic search for relevant knowledge
        relevant_knowledge = self._semantic_search(user_question, top_k=2)
        
        if not relevant_knowledge:
            return self._fallback_response(user_question), None
        
        # Step 2: Detect question intent
        intent_info = self._detect_question_intent(user_question)
        
        # Step 3: Retrieve data from database
        retrieved_data = []
        for knowledge_item in relevant_knowledge:
            data = self._execute_database_query(knowledge_item, intent_info['limit'])
            if not data.empty:
                formatted_data = self._format_data_for_ai(data, knowledge_item)
                retrieved_data.append(formatted_data)
        
        # Step 4: Build context for AI
        context = "\n".join(retrieved_data) if retrieved_data else "No specific data retrieved."
        
        # Step 5: Check for visualization commands
        viz_command = self._detect_visualization_command(user_question, relevant_knowledge)
        
        # Step 6: Generate AI response with context
        ai_response = self._generate_contextual_response(user_question, context, current_viz_type, intent_info)
        
        return ai_response, viz_command
    
    def _detect_visualization_command(self, question: str, knowledge: List[Dict]) -> str:
        """Detect if user wants to change visualization based on retrieved knowledge"""
        question_lower = question.lower()
        
        viz_mappings = {
            'voltage': ['voltage', 'bus voltage', 'voltage analysis'],
            'loading': ['loading', 'line loading', 'overload', 'capacity'],
            'violations': ['violation', 'overloaded', 'exceeded', 'limit'],
            'comparison': ['slr', 'dlr', 'compare', 'comparison'],
            'network': ['network', 'topology', 'system', 'overview']
        }
        
        # Check direct visualization keywords
        for viz_type, keywords in viz_mappings.items():
            if any(keyword in question_lower for keyword in keywords):
                return viz_type
        
        # Check based on retrieved knowledge topics
        if knowledge:
            primary_topic = knowledge[0]['topic']
            if 'voltage' in primary_topic:
                return 'voltage'
            elif 'loading' in primary_topic or 'overload' in primary_topic:
                return 'loading'
            elif 'slr_dlr' in primary_topic:
                return 'comparison'
        
        return None
    
    def _generate_contextual_response(self, question: str, context: str, current_viz: str, intent: Dict) -> str:
        """Generate AI response using retrieved context"""
        try:
            from openai import OpenAI
            
            # Enhanced system prompt with RAG context
            system_prompt = f"""You are an expert power systems engineer analyzing the IEEE 118-bus test system. 
            
You have access to real-time database information and should use this data to provide accurate, evidence-based responses.

Current visualization: {current_viz}
User intent: {intent['intent']}

RETRIEVED DATA CONTEXT:
{context}

Guidelines:
1. Use the retrieved data to support your answers
2. Cite specific numbers and examples from the data
3. Explain what the data means in power systems context
4. Suggest actionable insights based on the evidence
5. If asked about visualizations, recommend appropriate charts
6. Keep responses concise but informative
"""

            client = OpenAI(
                api_key="sk-4UJCbpRTNTx-lvO_4bxNdQ",
                base_url="https://ai-incubator-api.pnnl.gov"
            )
            
            response = client.chat.completions.create(
                model="claude-3-7-sonnet-20250219-v1-birthright",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                stream=False
            )
            
            return f"🔍 **RAG-Enhanced Response:**\n\n{response.choices[0].message.content.strip()}"
            
        except Exception as e:
            self.logger.error(f"AI generation error: {e}")
            return self._format_direct_response(context, intent)
    
    def _format_direct_response(self, context: str, intent: Dict) -> str:
        """Fallback response using only retrieved data"""
        if not context or context == "No specific data retrieved.":
            return "🔍 I couldn't find specific data for your question. Try asking about voltage levels, line loadings, or system statistics."
        
        response = f"🔍 **Data-Based Analysis** (Intent: {intent['intent']}):\n\n"
        response += context
        response += "\n\n💡 This analysis is based on your IEEE 118-bus database."
        
        return response
    
    def _fallback_response(self, question: str) -> str:
        """Fallback when no relevant knowledge is found"""
        return f"🔍 I understand you're asking about '{question}'. Let me search the database for relevant information. Try asking about specific topics like 'voltage violations', 'overloaded lines', or 'system statistics'."

# Global RAG instance
power_rag = None

def initialize_rag():
    """Initialize the RAG system"""
    global power_rag
    if power_rag is None:
        power_rag = PowerSystemRAG('data.db')
    return power_rag

def get_rag_response(user_message: str, current_viz_type: str = 'network') -> Tuple[str, str]:
    """Get RAG-enhanced response for user questions"""
    rag_system = initialize_rag()
    return rag_system.retrieve_and_generate(user_message, current_viz_type)

if __name__ == "__main__":
    # Test the RAG system
    rag = PowerSystemRAG()
    
    test_questions = [
        "Which buses have voltage violations?",
        "Show me the most overloaded transmission lines",
        "How many lines are operating above 90% capacity?",
        "Compare SLR vs DLR performance",
        "What's the system voltage summary?"
    ]
    
    print("🔍 Testing Power System RAG")
    print("=" * 40)
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        response, viz_cmd = rag.retrieve_and_generate(question)
        print(f"🤖 Response: {response[:200]}...")
        if viz_cmd:
            print(f"📊 Suggested visualization: {viz_cmd}")
        print("-" * 40)