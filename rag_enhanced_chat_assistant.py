"""
RAG-Enhanced Chat Assistant for Power System Analysis
==================================================

This module provides an advanced Retrieval-Augmented Generation (RAG) chat assistant
specifically designed for power system data analysis. It combines the power of
LangChain for document processing and vector storage with Llama models for
intelligent conversation and analysis.

Key Features:
- Vector database integration with ChromaDB for efficient similarity search
- Database schema understanding and intelligent query generation
- Context-aware responses based on power system domain knowledge
- Statistical analysis capabilities with natural language interface
- Real-time data retrieval and analysis
- Power system specific terminology and knowledge base

Architecture:
1. Database Integration Layer - SQLite connection and schema understanding
2. Vector Store Layer - ChromaDB for document embeddings and similarity search  
3. RAG Pipeline - Document retrieval, context building, and response generation
4. LLM Integration - Llama model interface for natural language processing
5. Analysis Engine - Power system specific calculations and insights

Author: Power System Analysis Team
Date: September 2025
Version: 1.0 - LangChain RAG Implementation
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import json
import asyncio
from pathlib import Path

# LangChain imports
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

# Database and analysis imports
from sqlalchemy import create_engine, text
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PowerSystemRAGAssistant:
    """
    Advanced RAG-based chat assistant for power system analysis.
    
    This class provides intelligent conversation capabilities with deep integration
    into power system databases, enabling users to ask complex questions about
    power flow analysis, contingency scenarios, SLR/DLR cases, and system statistics.
    """
    
    def __init__(self, db_path: str = "data.db", llama_api_url: str = None, llama_api_key: str = None):
        """
        Initialize the RAG-enhanced chat assistant.
        
        Args:
            db_path: Path to the SQLite database containing power system data
            llama_api_url: URL endpoint for Llama API service
            llama_api_key: API key for Llama service authentication
        """
        self.db_path = db_path
        self.llama_api_url = llama_api_url or os.getenv("LLAMA_API_URL", "http://localhost:8000")
        self.llama_api_key = llama_api_key or os.getenv("LLAMA_API_KEY")
        
        # Initialize database connection
        self.engine = create_engine(f"sqlite:///{db_path}")
        
        # Initialize embeddings and vector store
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        self.retriever = None
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Initialize conversation chain
        self.rag_chain = None
        
        # Power system knowledge base
        self.power_system_knowledge = self._build_power_system_knowledge()
        
        # Initialize the RAG system
        self._initialize_rag_system()
    
    def _build_power_system_knowledge(self) -> Dict[str, str]:
        """
        Build a comprehensive knowledge base of power system concepts and terminology.
        
        Returns:
            Dictionary mapping power system terms to their explanations
        """
        return {
            "power_flow_analysis": """
            Power flow analysis calculates the steady-state electrical quantities (voltages, currents, power flows) 
            in a power system under normal operating conditions. Key parameters include:
            - VM: Voltage magnitude per unit
            - VA: Voltage angle in degrees  
            - PG: Real power generation in MW
            - QG: Reactive power generation in MVAR
            - PD: Real power demand in MW
            - QD: Reactive power demand in MVAR
            - PF: Real power flow in MW
            - QF: Reactive power flow in MVAR
            - MVA: Apparent power flow magnitude
            """,
            
            "contingency_analysis": """
            Contingency analysis evaluates system behavior when components fail or are removed from service.
            Common contingencies include:
            - N-1 contingencies: Single component outages
            - N-2 contingencies: Double component outages
            - Generator outages
            - Transmission line outages
            - Transformer outages
            Analysis includes voltage violations, thermal overloads, and stability concerns.
            """,
            
            "slr_analysis": """
            Static Load Relief (SLR) analysis determines the minimum load curtailment needed
            to relieve system violations after contingencies. Key aspects:
            - Load shedding optimization
            - Voltage constraint management
            - Thermal constraint management
            - LOAD_INI: Initial load before adjustment
            - LOAD_NEW: Final load after SLR
            - LOAD_ADJ: Load adjustment (shed amount)
            """,
            
            "dlr_analysis": """
            Dynamic Line Rating (DLR) analysis evaluates the benefits of using real-time
            transmission line ratings based on weather conditions. Benefits include:
            - Increased transmission capacity utilization
            - Reduced curtailment of renewable generation
            - Enhanced system flexibility
            - RATE: Line rating in MVA
            - Enhanced_rating: Dynamic rating based on conditions
            """,
            
            "voltage_analysis": """
            Voltage analysis monitors bus voltages throughout the system:
            - BASE_KV: Base voltage level in kV
            - VM: Per-unit voltage magnitude (typically 0.95-1.05 acceptable range)
            - VA: Voltage angle in degrees
            - Voltage violations occur when VM falls outside acceptable limits
            - High voltage: VM > 1.05 pu
            - Low voltage: VM < 0.95 pu
            """,
            
            "thermal_analysis": """
            Thermal analysis monitors power flow limits on transmission elements:
            - MVA: Apparent power flow magnitude
            - RATE: Thermal rating limit in MVA  
            - VIO: Violation percentage (MVA/RATE * 100)
            - Overload occurs when MVA > RATE
            - Critical overloads: VIO > 100%
            - Emergency ratings may allow temporary overloads
            """
        }
    
    def _initialize_rag_system(self):
        """
        Initialize the RAG system with database schema and power system knowledge.
        """
        try:
            logger.info("Initializing RAG system...")
            
            # Create documents from database schema and knowledge
            documents = self._create_knowledge_documents()
            
            # Create vector store
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory="./chroma_db"
            )
            
            # Create retriever
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            # Create RAG chain
            self._create_rag_chain()
            
            logger.info("RAG system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    def _create_knowledge_documents(self) -> List[Document]:
        """
        Create LangChain documents from database schema and power system knowledge.
        
        Returns:
            List of Document objects for vector storage
        """
        documents = []
        
        # Add database schema information
        schema_info = self._get_database_schema()
        for table_name, table_info in schema_info.items():
            doc_content = f"""
            Table: {table_name}
            Description: {table_info['description']}
            Columns: {', '.join([f"{col['name']} ({col['type']})" for col in table_info['columns']])}
            Purpose: {table_info['purpose']}
            """
            documents.append(Document(
                page_content=doc_content,
                metadata={"type": "schema", "table": table_name}
            ))
        
        # Add power system knowledge
        for concept, explanation in self.power_system_knowledge.items():
            documents.append(Document(
                page_content=f"Concept: {concept}\n{explanation}",
                metadata={"type": "knowledge", "concept": concept}
            ))
        
        # Add sample queries and explanations
        sample_queries = self._get_sample_queries()
        for query_info in sample_queries:
            documents.append(Document(
                page_content=query_info["content"],
                metadata={"type": "sample_query", "category": query_info["category"]}
            ))
        
        return documents
    
    def _get_database_schema(self) -> Dict[str, Dict]:
        """
        Extract and describe database schema information.
        
        Returns:
            Dictionary containing table schemas with descriptions
        """
        schema = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                # Get column information
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [{"name": col[1], "type": col[2]} for col in cursor.fetchall()]
                
                # Add table descriptions based on naming patterns
                description, purpose = self._get_table_description(table)
                
                schema[table] = {
                    "columns": columns,
                    "description": description,
                    "purpose": purpose
                }
        
        return schema
    
    def _get_table_description(self, table_name: str) -> Tuple[str, str]:
        """
        Generate description and purpose for database tables.
        
        Args:
            table_name: Name of the database table
            
        Returns:
            Tuple of (description, purpose)
        """
        table_descriptions = {
            "BaseBusData": (
                "Contains base case bus data including voltages, generation, and load",
                "Power flow analysis, voltage monitoring, generation and load analysis"
            ),
            "BaseBranchData": (
                "Contains base case branch/line data including power flows and ratings", 
                "Thermal analysis, power flow monitoring, line utilization studies"
            ),
            "ContingencyBusData": (
                "Bus data for contingency scenarios showing system response to outages",
                "Contingency analysis, voltage stability assessment, N-1 security studies"
            ),
            "ContingencyBranchData": (
                "Branch data for contingency scenarios showing power flow redistribution",
                "Contingency analysis, thermal limit monitoring, system security assessment"
            ),
            "SLR_Cases": (
                "Static Load Relief analysis cases with load curtailment results",
                "Load shedding optimization, system reliability analysis, emergency operations"
            ),
            "SLR_Buses": (
                "Bus data for SLR scenarios showing voltage impacts of load relief",
                "Voltage analysis during load relief, bus-specific SLR impacts"
            ),
            "SLR_Load": (
                "Load adjustment data showing before/after load values in SLR analysis",
                "Load shedding analysis, demand response studies, reliability calculations"
            ),
            "DLR_Cases": (
                "Dynamic Line Rating analysis cases with enhanced rating results",
                "Transmission capacity optimization, renewable integration studies"
            ),
            "DLR_Branches": (
                "Branch data for DLR scenarios showing benefits of dynamic ratings",
                "Line utilization analysis, capacity enhancement studies, congestion relief"
            ),
        }
        
        return table_descriptions.get(table_name, (
            f"Database table containing {table_name.lower().replace('_', ' ')} information",
            "Data storage and analysis for power system operations"
        ))
    
    def _get_sample_queries(self) -> List[Dict[str, str]]:
        """
        Generate sample queries and explanations for the knowledge base.
        
        Returns:
            List of sample query information
        """
        return [
            {
                "category": "voltage_analysis",
                "content": """
                Sample Query: "What buses have voltage violations?"
                SQL: SELECT BUS_NUMBER, VM, BASE_KV FROM BaseBusData WHERE VM < 0.95 OR VM > 1.05
                Analysis: This identifies buses with voltage magnitudes outside the typical acceptable range of 0.95-1.05 per unit.
                """
            },
            {
                "category": "thermal_analysis", 
                "content": """
                Sample Query: "Which lines are overloaded?"
                SQL: SELECT From_Bus, To_Bus, MVA, RATE, (MVA/RATE*100) as Loading FROM BaseBranchData WHERE MVA > RATE
                Analysis: This finds transmission lines where power flow exceeds thermal rating.
                """
            },
            {
                "category": "contingency_analysis",
                "content": """
                Sample Query: "How does contingency affect system voltages?"
                SQL: SELECT b1.BUS_NUMBER, b1.VM as Base_VM, b2.VM as Contingency_VM, (b2.VM-b1.VM) as Voltage_Change
                FROM BaseBusData b1 JOIN ContingencyBusData b2 ON b1.BUS_NUMBER = b2.bus_number
                Analysis: Compares base case and contingency voltages to assess impact.
                """
            },
            {
                "category": "slr_analysis",
                "content": """
                Sample Query: "How much load was shed in SLR analysis?"
                SQL: SELECT BUS_NUMBER, LOAD_INI, LOAD_NEW, LOAD_ADJ FROM SLR_Load WHERE LOAD_ADJ > 0
                Analysis: Shows load curtailment at each bus during Static Load Relief operations.
                """
            },
            {
                "category": "dlr_analysis",
                "content": """
                Sample Query: "What are the benefits of dynamic line rating?"
                SQL: SELECT From_Bus, To_Bus, RATE as Static_Rating, enhanced_rating as Dynamic_Rating, 
                (enhanced_rating - RATE) as Additional_Capacity FROM DLR_Cases dc JOIN DLR_Branches db ON dc.contingency_case_id = db.contingency_case_id
                Analysis: Compares static and dynamic ratings to quantify capacity benefits.
                """
            }
        ]
    
    def _create_rag_chain(self):
        """
        Create the RAG chain for question answering.
        """
        # Create prompt template
        prompt_template = """
        You are an expert power systems engineer with deep knowledge of electrical power systems, 
        power flow analysis, contingency analysis, and system operations. Use the provided context 
        to answer questions about power system data and analysis.

        Context from power system database and knowledge base:
        {context}

        Human Question: {input}

        Please provide a comprehensive answer that:
        1. Addresses the specific question asked
        2. Uses relevant power system terminology correctly
        3. Provides numerical insights when applicable
        4. Suggests follow-up analysis if appropriate
        5. Explains any assumptions or limitations

        If the question requires database queries, suggest appropriate SQL queries.
        If the question involves calculations, show the methodology.

        Expert Response:
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Create document processing chain
        document_chain = create_stuff_documents_chain(
            llm=self._get_llm_interface(),
            prompt=prompt
        )
        
        # Create retrieval chain
        self.rag_chain = create_retrieval_chain(
            self.retriever,
            document_chain
        )
    
    def _get_llm_interface(self):
        """
        Create LLM interface for Llama model.
        
        Returns:
            LLM interface compatible with LangChain
        """
        class LlamaLLM(LLM):
            api_url: str
            api_key: Optional[str] = None
            
            def __init__(self, api_url: str, api_key: str = None, **kwargs):
                super().__init__(api_url=api_url, api_key=api_key, **kwargs)
            
            @property
            def _llm_type(self) -> str:
                return "llama"
            
            def _call(
                self,
                prompt: str,
                stop: Optional[List[str]] = None,
                run_manager: Optional[CallbackManagerForLLMRun] = None,
                **kwargs: Any,
            ) -> str:
                """Send request to Llama API and return response."""
                try:
                    headers = {"Content-Type": "application/json"}
                    if self.api_key:
                        headers["Authorization"] = f"Bearer {self.api_key}"
                    
                    payload = {
                        "prompt": prompt,
                        "max_tokens": 1000,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                    
                    response = requests.post(
                        f"{self.api_url}/v1/completions",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        return response.json().get("choices", [{}])[0].get("text", "")
                    else:
                        logger.error(f"Llama API error: {response.status_code}")
                        return "I'm having trouble connecting to the AI service. Please try again later."
                        
                except Exception as e:
                    logger.error(f"Error calling Llama API: {e}")
                    return "I encountered an error while processing your request. Please try again."
        
        return LlamaLLM(api_url=self.llama_api_url, api_key=self.llama_api_key)
    
    def query_database(self, sql_query: str) -> pd.DataFrame:
        """
        Execute SQL query against the power system database.
        
        Args:
            sql_query: SQL query string to execute
            
        Returns:
            pandas DataFrame with query results
        """
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql_query(text(sql_query), conn)
                return result
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return pd.DataFrame()
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive power system statistics.
        
        Returns:
            Dictionary containing system statistics
        """
        stats = {}
        
        try:
            # Bus statistics
            bus_stats = self.query_database("""
                SELECT 
                    COUNT(*) as total_buses,
                    AVG(VM) as avg_voltage,
                    MIN(VM) as min_voltage,
                    MAX(VM) as max_voltage,
                    COUNT(CASE WHEN VM < 0.95 THEN 1 END) as low_voltage_buses,
                    COUNT(CASE WHEN VM > 1.05 THEN 1 END) as high_voltage_buses,
                    SUM(PG) as total_generation,
                    SUM(PD) as total_load
                FROM BaseBusData
            """)
            stats["bus_statistics"] = bus_stats.to_dict('records')[0] if not bus_stats.empty else {}
            
            # Branch statistics  
            branch_stats = self.query_database("""
                SELECT 
                    COUNT(*) as total_branches,
                    AVG(MVA) as avg_flow,
                    MAX(MVA) as max_flow,
                    AVG(RATE) as avg_rating,
                    COUNT(CASE WHEN MVA > RATE THEN 1 END) as overloaded_lines,
                    AVG(MVA/RATE * 100) as avg_loading_percent
                FROM BaseBranchData WHERE RATE > 0
            """)
            stats["branch_statistics"] = branch_stats.to_dict('records')[0] if not branch_stats.empty else {}
            
            # SLR statistics
            slr_stats = self.query_database("""
                SELECT 
                    COUNT(*) as total_slr_cases,
                    SUM(LOAD_ADJ) as total_load_shed,
                    AVG(LOAD_ADJ) as avg_load_shed,
                    MAX(LOAD_ADJ) as max_load_shed
                FROM SLR_Load WHERE LOAD_ADJ > 0
            """)
            stats["slr_statistics"] = slr_stats.to_dict('records')[0] if not slr_stats.empty else {}
            
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            
        return stats
    
    def chat(self, question: str) -> Dict[str, Any]:
        """
        Main chat interface for interacting with the RAG assistant.
        
        Args:
            question: User's question about the power system
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Get response from RAG chain
            if self.rag_chain:
                response = self.rag_chain.invoke({"input": question})
                
                # Extract relevant database statistics if needed
                stats = None
                if any(keyword in question.lower() for keyword in ["statistics", "summary", "overview", "count"]):
                    stats = self.get_system_statistics()
                
                return {
                    "response": response.get("answer", "I couldn't generate a response."),
                    "context_sources": [doc.metadata for doc in response.get("context", [])],
                    "statistics": stats,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "response": "RAG system not properly initialized. Please check the setup.",
                    "error": "RAG system not available"
                }
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "response": "I encountered an error processing your question. Please try again.",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def suggest_queries(self, topic: str = None) -> List[str]:
        """
        Suggest relevant queries based on topic or general power system analysis.
        
        Args:
            topic: Optional topic to focus suggestions on
            
        Returns:
            List of suggested query strings
        """
        suggestions = {
            "voltage": [
                "What buses have voltage violations?",
                "Show me the voltage profile across all buses",
                "Which buses have the lowest voltages?",
                "What's the average system voltage?"
            ],
            "thermal": [
                "Which transmission lines are overloaded?",
                "What's the loading on critical transmission paths?",
                "Show me lines operating near their thermal limits",
                "What's the overall system loading?"
            ],
            "contingency": [
                "How do contingencies affect system voltages?",
                "What are the most severe contingency impacts?",
                "Which contingencies cause the most violations?",
                "Compare base case vs contingency performance"
            ],
            "slr": [
                "How much load shedding is required?",
                "Which buses require load curtailment?",
                "What's the total load shed across all scenarios?",
                "Show SLR results by voltage level"
            ],
            "dlr": [
                "What are the benefits of dynamic line rating?",
                "Which lines benefit most from DLR?",
                "How much additional capacity does DLR provide?",
                "Compare static vs dynamic ratings"
            ]
        }
        
        if topic and topic.lower() in suggestions:
            return suggestions[topic.lower()]
        else:
            # Return a mix from all categories
            all_suggestions = []
            for category_suggestions in suggestions.values():
                all_suggestions.extend(category_suggestions[:2])  # Take first 2 from each category
            return all_suggestions


# Utility functions for integration with existing chat interface
def create_rag_assistant(db_path: str = "data.db") -> PowerSystemRAGAssistant:
    """
    Create and initialize a RAG assistant instance.
    
    Args:
        db_path: Path to the power system database
        
    Returns:
        Initialized PowerSystemRAGAssistant instance
    """
    return PowerSystemRAGAssistant(db_path=db_path)


def test_rag_system():
    """
    Test function to verify RAG system functionality.
    """
    try:
        print("Testing RAG system initialization...")
        assistant = create_rag_assistant()
        
        print("Testing basic chat functionality...")
        response = assistant.chat("What information is available in the power system database?")
        print(f"Response: {response['response']}")
        
        print("Testing system statistics...")
        stats = assistant.get_system_statistics()
        print(f"Statistics keys: {list(stats.keys())}")
        
        print("Testing query suggestions...")
        suggestions = assistant.suggest_queries("voltage")
        print(f"Voltage suggestions: {suggestions}")
        
        print("RAG system test completed successfully!")
        
    except Exception as e:
        print(f"RAG system test failed: {e}")


if __name__ == "__main__":
    test_rag_system()