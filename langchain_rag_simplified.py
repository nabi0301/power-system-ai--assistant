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
    
    def answer_question(self, question: str) -> Optional[str]:
        """
        Answer a question using the RAG system
        This is a simplified implementation that doesn't depend on full LangChain
        
        Args:
            question: The user's question about power systems
            
        Returns:
            Generated answer based on retrieved context
        """
        try:
            # Simple keyword matching
            if "voltage" in question.lower():
                query = """
                SELECT BUS_NUMBER, VM, VA, BASE_KV
                FROM BaseBusData 
                WHERE base_case_id = 0
                ORDER BY VM DESC
                LIMIT 5
                """
                results = self.execute_query(query)
                
                response = "Here's voltage information for some buses:\n\n"
                for row in results:
                    response += f"Bus {row['BUS_NUMBER']}: {row['VM']:.4f} pu ({row['BASE_KV']} kV), angle: {row['VA']:.2f}°\n"
                return response
            
            elif "loading" in question.lower() or "overload" in question.lower():
                query = """
                SELECT From_Bus, To_Bus, MVA, RATE,
                       CASE WHEN RATE > 0 THEN (MVA/RATE*100) ELSE 0 END as loading_pct
                FROM BaseBranchData 
                WHERE base_case_id = 0
                ORDER BY loading_pct DESC
                LIMIT 5
                """
                results = self.execute_query(query)
                
                response = "Here's loading information for the most loaded lines:\n\n"
                for row in results:
                    loading = row['loading_pct']
                    status = "🟢 Normal" if loading < 90 else "🟠 High" if loading < 100 else "🔴 Overloaded"
                    response += f"Line {row['From_Bus']}-{row['To_Bus']}: {loading:.1f}% ({row['MVA']:.1f}/{row['RATE']:.1f} MVA) - {status}\n"
                return response
                
            elif "network" in question.lower() or "graph" in question.lower():
                return "To see the network graph, try the specific command: 'Show network graph'"
                
            elif "slr" in question.lower() or "dlr" in question.lower():
                query = """
                SELECT s.From_Bus, s.To_Bus, s.RATE as slr_rate, d.Enhanced_Rating as dlr_rate,
                       d.Enhanced_Rating - s.RATE as rating_increase
                FROM SLR_Branches s
                JOIN DLR_Branches d ON s.From_Bus = d.From_Bus AND s.To_Bus = d.To_Bus
                WHERE s.base_case_id = 0 AND s.contingency_case_id = 0
                AND d.base_case_id = 0 AND d.contingency_case_id = 0
                ORDER BY rating_increase DESC
                LIMIT 5
                """
                
                try:
                    results = self.execute_query(query)
                    
                    response = "Here's a comparison of SLR vs DLR ratings:\n\n"
                    for row in results:
                        increase_pct = (row['dlr_rate'] - row['slr_rate']) / row['slr_rate'] * 100
                        response += f"Line {row['From_Bus']}-{row['To_Bus']}: SLR = {row['slr_rate']:.1f} MVA, DLR = {row['dlr_rate']:.1f} MVA, Increase: {increase_pct:.1f}%\n"
                    return response
                except:
                    return "I couldn't retrieve SLR vs DLR comparison data. The tables might not be available."
            
            # General questions about power systems
            for concept, info in self.power_system_knowledge.items():
                if any(kw in question.lower() for kw in concept.lower().split('_')):
                    return f"Based on power system knowledge:\n\n{info}"
                    
            # Default response
            return "I'm a simplified version of the LangChain RAG system. For specific power system questions, try asking about voltage, loading, network graphs, or SLR vs DLR comparisons."
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"I encountered an issue while answering your question in simplified mode. Error: {str(e)}"