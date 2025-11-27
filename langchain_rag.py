#!/usr/bin/env python3
"""
Simplified LangChain RAG System for Power System Analysis
Minimalistic implementation that can work with limited dependencies
"""

import os
import sqlite3
import pandas as pd
import logging
import sys
from typing import Dict, List, Any, Optional

# Try to import config
try:
    from config import AI_CONFIG
    if 'openai_api_key' in AI_CONFIG and AI_CONFIG['openai_api_key']:
        os.environ["OPENAI_API_KEY"] = AI_CONFIG['openai_api_key']
except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangChainRAG:
    """
    Simplified LangChain-based RAG system for power system data analysis
    This version uses minimal dependencies to ensure compatibility
    """
    
    def __init__(self, db_path: str):
        """Initialize RAG system with power system database"""
        self.db_path = db_path
        
        # Power system knowledge base
        self.power_system_knowledge = self._build_knowledge_base()
        
        logger.info("LangChain RAG system initialized in simplified mode")
        
    def _build_knowledge_base(self) -> Dict[str, str]:
        """Build power system domain knowledge base"""
        return {
            "general_power_system": """
            Power systems are networks that deliver electricity from generators 
            to loads through transmission and distribution systems. Key components include:
            - Generators (power plants, renewables)
            - Transmission lines (high voltage)
            - Buses (connection points/substations)
            - Loads (power consumers)
            Analysis typically focuses on power flow, stability, reliability, and contingencies.
            """,
            
            "ieee_118_bus": """
            The IEEE 118-bus test system represents a portion of the American Electric Power 
            System as of December 1962. It contains:
            - 118 buses
            - 186 branches (transmission lines/transformers)
            - 91 load sides
            - 54 generators
            This system is commonly used for power flow studies, contingency analysis, and 
            algorithm testing in power systems research.
            """,
            
            "power_flow": """
            Power flow analysis (load flow) determines the steady-state operating condition 
            of a power system. It calculates:
            - Bus voltages (magnitude and angle)
            - Line flows (real and reactive power)
            - System losses
            - Generator outputs
            Methods include Newton-Raphson, Fast-Decoupled, and Gauss-Seidel algorithms.
            """,
            
            "slr_dlr": """
            Static Line Rating (SLR) uses conservative fixed thermal limits for transmission lines.
            Dynamic Line Rating (DLR) adjusts limits based on real-time weather conditions.
            DLR typically allows higher capacities than SLR, especially in cool or windy conditions,
            improving grid flexibility and asset utilization.
            """,
            
            "contingency_analysis": """
            Contingency analysis evaluates system security by simulating outages (N-1 or N-2).
            It identifies potential:
            - Thermal overloads on lines
            - Voltage violations at buses
            - System stability issues
            Critical contingencies require mitigation strategies to maintain reliability.
            """,
        }
        
    def _initialize_rag_system(self):
        """Initialize the RAG system with database schema and knowledge documents"""
        try:
            # Create documents from database schema
            schema_docs = self._create_schema_documents()
            
            # Create documents from power system knowledge
            knowledge_docs = self._create_knowledge_documents()
            
            # Combine all documents
            all_docs = schema_docs + knowledge_docs
            
            # Create vector store
            self.vector_store = Chroma.from_documents(
                documents=all_docs,
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
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    def _create_schema_documents(self) -> List[Document]:
        """Create documents from database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        documents = []
        
        for table in tables:
            table_name = table[0]
            
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # Get sample data (first row)
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                sample = cursor.fetchone()
            except:
                sample = None
            
            # Create document content
            content = f"Table: {table_name}\nColumns:\n"
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                content += f"- {col_name} ({col_type})\n"
            
            # Add sample data if available
            if sample:
                content += "\nSample data:\n"
                for i, col in enumerate(columns):
                    if i < len(sample):
                        content += f"{col[1]}: {sample[i]}\n"
            
            # Create document
            doc = Document(
                page_content=content,
                metadata={"type": "schema", "table": table_name}
            )
            documents.append(doc)
        
        conn.close()
        return documents
    
    def _create_knowledge_documents(self) -> List[Document]:
        """Create documents from power system knowledge"""
        documents = []
        
        for concept, explanation in self.power_system_knowledge.items():
            doc = Document(
                page_content=f"Concept: {concept}\n{explanation}",
                metadata={"type": "knowledge", "concept": concept}
            )
            documents.append(doc)
            
        return documents
    
    def _create_rag_chain(self):
        """Create the RAG chain for question answering"""
        # Create prompt template
        prompt_template = """
        You are an expert power systems engineer specializing in power flow analysis, 
        contingency studies, and electrical grid operations. Answer the question based 
        on the provided context. If you can't answer from the context, use your knowledge 
        of power systems but make it clear when you're doing so.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create stuff documents chain (combines documents into context)
        stuff_documents_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=prompt
        )
        
        # Create retrieval chain
        self.rag_chain = create_retrieval_chain(
            self.retriever,
            stuff_documents_chain
        )
    
    def answer_question(self, question: str) -> Optional[str]:
        """
        Answer a question using the RAG system
        
        Args:
            question: The user's question about power systems
            
        Returns:
            Generated answer based on retrieved context
        """
        try:
            # Process with RAG chain
            response = self.rag_chain.invoke({"question": question})
            
            # Extract answer from response
            if "answer" in response:
                return response["answer"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"I encountered an issue while answering your question. Error: {str(e)}"
            
    def execute_query(self, query: str, params=()) -> List[Dict]:
        """Execute SQL query on the database and return formatted results"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []