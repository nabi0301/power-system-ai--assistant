#!/usr/bin/env python3
"""
Power System Analysis with LangChain Integration
Advanced demonstration of LangChain capabilities for power system analysis
"""

import os
import sqlite3
import pandas as pd
import sys
from typing import List, Dict, Any

# Try to import config
try:
    from config import AI_CONFIG
    if 'openai_api_key' in AI_CONFIG and AI_CONFIG['openai_api_key']:
        os.environ["OPENAI_API_KEY"] = AI_CONFIG['openai_api_key']
except ImportError:
    pass

# LangChain imports
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.agents import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.chat_models import ChatOpenAI
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType

class PowerSystemLangChainIntegration:
    """
    Advanced integration of LangChain capabilities for power system analysis
    Showcases agents, memory, chains, and tools for comprehensive analysis
    """
    
    def __init__(self, db_path: str = "data.db"):
        """Initialize the LangChain integration"""
        self.db_path = db_path
        
        # Set up LLM
        self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        
        # Set up embeddings
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Set up database connection
        self.db_uri = f"sqlite:///{db_path}"
        self.db = SQLDatabase.from_uri(self.db_uri)
        
        # Set up vector store
        self._setup_vector_store()
        
        # Set up SQL agent
        self._setup_sql_agent()
        
        # Set up conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Set up tools
        self._setup_tools()
        
        # Set up conversation chain
        self._setup_conversation_chain()
        
        print("Power System LangChain Integration initialized successfully")
    
    def _setup_vector_store(self):
        """Set up vector store with power system knowledge"""
        # Create documents from power system knowledge
        docs = self._create_power_system_documents()
        
        # Create vector store
        self.vector_store = Chroma.from_documents(
            documents=docs,
            embedding=self.embeddings,
            persist_directory="./chroma_power_db"
        )
        
        # Create retriever
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 5}
        )
    
    def _setup_sql_agent(self):
        """Set up SQL agent for database queries"""
        # Create SQL toolkit
        self.sql_toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        
        # Create SQL agent
        self.sql_agent = create_sql_agent(
            llm=self.llm,
            toolkit=self.sql_toolkit,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS
        )
    
    def _setup_tools(self):
        """Set up tools for the agent"""
        self.tools = [
            Tool(
                name="SQL_Database",
                func=self.sql_agent.run,
                description="Useful for when you need to query the power system database. Input should be a natural language query about the power system data."
            ),
            Tool(
                name="Power_System_Knowledge",
                func=self._query_power_system_knowledge,
                description="Useful for when you need general knowledge about power systems, concepts, and terminology."
            ),
            Tool(
                name="System_Statistics",
                func=self._get_system_statistics,
                description="Useful for when you need statistical information about the power system."
            )
        ]
        
        # Create agent with tools
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            memory=self.memory
        )
    
    def _setup_conversation_chain(self):
        """Set up conversational retrieval chain"""
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert power systems engineer specializing in power flow analysis, 
            contingency studies, and electrical grid operations. Answer the user's questions using the provided context
            and your knowledge of power systems. If you need to query the database, use the appropriate tools."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        # Create conversation chain
        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": prompt}
        )
    
    def _create_power_system_documents(self) -> List[Document]:
        """Create documents from power system knowledge"""
        power_system_knowledge = {
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
            """
        }
        
        documents = []
        for concept, content in power_system_knowledge.items():
            documents.append(
                Document(
                    page_content=f"Concept: {concept}\n{content}",
                    metadata={"concept": concept, "type": "knowledge"}
                )
            )
        
        return documents
    
    def _query_power_system_knowledge(self, query: str) -> str:
        """Query the power system knowledge base"""
        # Simple implementation using the retriever
        docs = self.retriever.get_relevant_documents(query)
        return "\n\n".join([doc.page_content for doc in docs])
    
    def _get_system_statistics(self, query: str) -> str:
        """Get statistical information about the power system"""
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        
        # Run some predefined statistical queries
        stats = {}
        
        # Get bus statistics
        bus_df = pd.read_sql("SELECT COUNT(*) as count, AVG(VM) as avg_voltage, MIN(VM) as min_voltage, MAX(VM) as max_voltage FROM BaseBusData WHERE base_case_id = 0", conn)
        stats["bus_stats"] = bus_df.to_dict(orient="records")[0]
        
        # Get branch statistics
        branch_df = pd.read_sql("SELECT COUNT(*) as count, AVG(MVA) as avg_flow, MAX(MVA) as max_flow FROM BaseBranchData WHERE base_case_id = 0", conn)
        stats["branch_stats"] = branch_df.to_dict(orient="records")[0]
        
        # Get generator statistics
        gen_df = pd.read_sql("SELECT COUNT(*) as count, SUM(GEN_INI) as total_generation FROM SLR_Generator WHERE base_case_id = 0", conn)
        stats["generator_stats"] = gen_df.to_dict(orient="records")[0]
        
        conn.close()
        
        return f"""
        Power System Statistics:
        
        Bus Statistics:
        - Total Buses: {stats['bus_stats']['count']}
        - Average Voltage (pu): {stats['bus_stats']['avg_voltage']:.4f}
        - Minimum Voltage (pu): {stats['bus_stats']['min_voltage']:.4f}
        - Maximum Voltage (pu): {stats['bus_stats']['max_voltage']:.4f}
        
        Branch Statistics:
        - Total Branches: {stats['branch_stats']['count']}
        - Average Power Flow (MVA): {stats['branch_stats']['avg_flow']:.2f}
        - Maximum Power Flow (MVA): {stats['branch_stats']['max_flow']:.2f}
        
        Generator Statistics:
        - Total Generators: {stats['generator_stats']['count']}
        - Total Generation (MW): {stats['generator_stats']['total_generation']:.2f}
        """
    
    def process_query(self, query: str) -> str:
        """
        Process a user query using the LangChain tools
        
        Args:
            query: User's question about the power system
            
        Returns:
            Response from the conversation chain or agent
        """
        try:
            # Determine if this is a database query
            if "database" in query.lower() or "sql" in query.lower() or "query" in query.lower():
                # Use SQL agent for database queries
                return self.sql_agent.run(query)
            else:
                # Use conversation chain for general questions
                response = self.conversation_chain({"question": query})
                return response["answer"]
                
        except Exception as e:
            return f"Error processing query: {str(e)}"

def main():
    """Demo the LangChain integration"""
    integration = PowerSystemLangChainIntegration()
    
    print("\n" + "="*50)
    print("Power System Analysis with LangChain")
    print("="*50)
    
    while True:
        query = input("\nEnter your question (or 'exit' to quit): ")
        
        if query.lower() in ['exit', 'quit', 'q']:
            break
            
        response = integration.process_query(query)
        print("\nResponse:")
        print(response)

if __name__ == "__main__":
    # API key is already set from config.py
    main()