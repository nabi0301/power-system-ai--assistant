#!/usr/bin/env python3
"""
Simplified RAG System for Power System Analysis
Uses SQL-based retrieval without heavy ML dependencies
"""

import sqlite3
import re
from typing import Tuple, Optional, Dict, List

class SimpleRAG:
    """Simplified RAG system using SQL queries for power system data"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Define query patterns for different types of questions
        self.query_patterns = {
            'case_list': {
                'keywords': ['cases', 'case list', 'available cases', 'what cases', 'show cases'],
                'query': """
                SELECT DISTINCT base_case_id, 
                       COUNT(*) as total_buses,
                       MIN(BUS_NUMBER) as min_bus,
                       MAX(BUS_NUMBER) as max_bus
                FROM BaseBusData 
                GROUP BY base_case_id
                ORDER BY base_case_id
                LIMIT 20;
                """
            },
            'contingency_cases': {
                'keywords': ['contingency', 'contingencies', 'contingency cases', 'outage', 'failure'],
                'query': """
                SELECT DISTINCT s.base_case_id, s.contingency_case_id,
                       COUNT(*) as affected_branches,
                       AVG(s.VIO) as avg_slr_violation,
                       AVG(d.VIO) as avg_dlr_violation
                FROM SLR_Branches s
                LEFT JOIN DLR_Branches d ON s.base_case_id = d.base_case_id 
                    AND s.contingency_case_id = d.contingency_case_id
                    AND s.From_Bus = d.From_Bus AND s.To_Bus = d.To_Bus
                GROUP BY s.base_case_id, s.contingency_case_id
                ORDER BY s.base_case_id, s.contingency_case_id
                LIMIT 15;
                """
            },
            'case_comparison': {
                'keywords': ['compare cases', 'case comparison', 'difference between cases', 'case analysis'],
                'query': """
                SELECT base_case_id,
                       COUNT(*) as total_buses,
                       ROUND(AVG(VM), 4) as avg_voltage,
                       ROUND(SUM(PD), 1) as total_load_mw,
                       ROUND(SUM(PG), 1) as total_generation_mw,
                       COUNT(CASE WHEN VM < 0.95 OR VM > 1.05 THEN 1 END) as voltage_violations
                FROM BaseBusData 
                GROUP BY base_case_id
                ORDER BY base_case_id
                LIMIT 10;
                """
            },
            'voltage_violations': {
                'keywords': ['voltage', 'violation', 'low voltage', 'high voltage', 'voltage limit'],
                'query': """
                SELECT base_case_id, BUS_NUMBER, VM, BASE_KV,
                       CASE 
                           WHEN VM < 0.95 THEN 'Low Voltage'
                           WHEN VM > 1.05 THEN 'High Voltage'
                           ELSE 'Normal'
                       END as voltage_status
                FROM BaseBusData 
                WHERE (VM < 0.95 OR VM > 1.05)
                ORDER BY base_case_id, ABS(VM - 1.0) DESC
                LIMIT 15;
                """
            },
            'overloaded_lines': {
                'keywords': ['overload', 'loading', 'thermal limit', 'line loading', 'branch loading'],
                'query': """
                SELECT base_case_id, From_Bus, To_Bus, MVA, RATE, 
                       ROUND((MVA/RATE*100), 2) as loading_percent
                FROM BaseBranchData 
                WHERE RATE > 0 AND (MVA/RATE) > 0.9
                ORDER BY base_case_id, (MVA/RATE) DESC
                LIMIT 15;
                """
            },
            'high_load_buses': {
                'keywords': ['load', 'demand', 'high load', 'power demand'],
                'query': """
                SELECT base_case_id, BUS_NUMBER, PD, VM, BASE_KV
                FROM BaseBusData 
                WHERE PD > 50
                ORDER BY base_case_id, PD DESC
                LIMIT 15;
                """
            },
            'generators': {
                'keywords': ['generator', 'generation', 'power generation', 'generator bus'],
                'query': """
                SELECT base_case_id, BUS_NUMBER, PG, VM, BASE_KV
                FROM BaseBusData 
                WHERE PG > 0
                ORDER BY base_case_id, PG DESC
                LIMIT 15;
                """
            },
            'slr_dlr_comparison': {
                'keywords': ['slr', 'dlr', 'static line rating', 'dynamic line rating', 'comparison'],
                'query': """
                SELECT s.base_case_id, s.contingency_case_id, s.From_Bus, s.To_Bus, 
                       s.RATE as SLR_Rating, d.RATE as DLR_Rating,
                       (d.RATE - s.RATE) as Rating_Improvement,
                       s.VIO as SLR_Violation, d.VIO as DLR_Violation
                FROM SLR_Branches s
                JOIN DLR_Branches d ON s.From_Bus = d.From_Bus 
                    AND s.To_Bus = d.To_Bus 
                    AND s.base_case_id = d.base_case_id
                    AND s.contingency_case_id = d.contingency_case_id
                WHERE d.RATE > s.RATE
                ORDER BY s.base_case_id, s.contingency_case_id, (d.RATE - s.RATE) DESC
                LIMIT 20;
                """
            },
            'system_summary': {
                'keywords': ['summary', 'overview', 'system status', 'total'],
                'query': """
                SELECT base_case_id,
                    COUNT(*) as total_buses,
                    ROUND(AVG(VM), 4) as avg_voltage,
                    ROUND(SUM(PD), 2) as total_load_mw,
                    ROUND(SUM(PG), 2) as total_generation_mw,
                    COUNT(CASE WHEN VM < 0.95 OR VM > 1.05 THEN 1 END) as voltage_violations
                FROM BaseBusData 
                GROUP BY base_case_id
                ORDER BY base_case_id
                LIMIT 10;
                """
            },
            'worst_violations': {
                'keywords': ['worst', 'critical', 'severe', 'emergency', 'worst case'],
                'query': """
                SELECT s.base_case_id, s.contingency_case_id, s.From_Bus, s.To_Bus,
                       s.VIO as SLR_Violation, d.VIO as DLR_Violation,
                       (s.VIO - d.VIO) as Violation_Reduction
                FROM SLR_Branches s
                JOIN DLR_Branches d ON s.From_Bus = d.From_Bus 
                    AND s.To_Bus = d.To_Bus 
                    AND s.base_case_id = d.base_case_id
                    AND s.contingency_case_id = d.contingency_case_id
                WHERE s.VIO > 100 OR d.VIO > 100
                ORDER BY GREATEST(s.VIO, d.VIO) DESC
                LIMIT 15;
                """
            },
            'efficiency_analysis': {
                'keywords': ['efficiency', 'performance', 'optimization', 'benefit', 'improvement'],
                'query': """
                SELECT s.base_case_id, s.contingency_case_id,
                       COUNT(*) as total_lines,
                       AVG(d.RATE - s.RATE) as avg_rating_improvement,
                       MAX(d.RATE - s.RATE) as max_rating_improvement,
                       COUNT(CASE WHEN d.RATE > s.RATE THEN 1 END) as lines_improved,
                       AVG(s.VIO - d.VIO) as avg_violation_reduction
                FROM SLR_Branches s
                JOIN DLR_Branches d ON s.From_Bus = d.From_Bus 
                    AND s.To_Bus = d.To_Bus 
                    AND s.base_case_id = d.base_case_id
                    AND s.contingency_case_id = d.contingency_case_id
                GROUP BY s.base_case_id, s.contingency_case_id
                HAVING COUNT(*) > 10
                ORDER BY avg_rating_improvement DESC
                LIMIT 10;
                """
            }
        }
    
    def match_query_pattern(self, question: str) -> Optional[str]:
        """Match user question to a query pattern"""
        question_lower = question.lower()
        
        best_match = None
        best_score = 0
        
        for pattern_name, pattern_info in self.query_patterns.items():
            score = 0
            for keyword in pattern_info['keywords']:
                if keyword in question_lower:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = pattern_name
        
        return best_match if best_score > 0 else None
    
    def execute_query(self, query: str) -> List[Dict]:
        """Execute SQL query and return results"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            cursor.execute(query)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            print(f"Query error: {e}")
            return []
    
    def format_results(self, results: List[Dict], pattern_name: str) -> str:
        """Format query results into readable text"""
        if not results:
            return "No relevant data found in the database."
        
        if pattern_name == 'case_list':
            response = "**Available Base Cases in Database:**\n"
            for row in results:
                response += f"• Case {row['base_case_id']}: {row['total_buses']} buses (Bus {row['min_bus']}-{row['max_bus']})\n"
        
        elif pattern_name == 'contingency_cases':
            response = "**Contingency Analysis Cases:**\n"
            for row in results:
                slr_vio = row['avg_slr_violation'] or 0
                dlr_vio = row['avg_dlr_violation'] or 0
                response += f"• Base Case {row['base_case_id']}, Contingency {row['contingency_case_id']}: {row['affected_branches']} branches, SLR: {slr_vio:.1f}% avg violation, DLR: {dlr_vio:.1f}% avg violation\n"
        
        elif pattern_name == 'case_comparison':
            response = "**Case-by-Case System Analysis:**\n"
            for row in results:
                response += f"• Case {row['base_case_id']}: {row['total_buses']} buses, {row['avg_voltage']:.3f} p.u. avg voltage, {row['total_load_mw']:.1f} MW load, {row['total_generation_mw']:.1f} MW gen, {row['voltage_violations']} violations\n"
        
        elif pattern_name == 'voltage_violations':
            response = "**Voltage Violations Across Cases:**\n"
            for row in results:
                response += f"• Case {row['base_case_id']}, Bus {row['BUS_NUMBER']}: {row['VM']:.3f} p.u. ({row['voltage_status']}) at {row['BASE_KV']} kV\n"
        
        elif pattern_name == 'overloaded_lines':
            response = "**Overloaded Transmission Lines Across Cases:**\n"
            for row in results:
                response += f"• Case {row['base_case_id']}, Line {row['From_Bus']}-{row['To_Bus']}: {row['loading_percent']:.1f}% loading ({row['MVA']:.1f}/{row['RATE']:.1f} MVA)\n"
        
        elif pattern_name == 'high_load_buses':
            response = "**High Load Buses Across Cases:**\n"
            for row in results:
                response += f"• Case {row['base_case_id']}, Bus {row['BUS_NUMBER']}: {row['PD']:.1f} MW load, {row['VM']:.3f} p.u. voltage at {row['BASE_KV']} kV\n"
        
        elif pattern_name == 'generators':
            response = "**Generator Buses Across Cases:**\n"
            for row in results:
                response += f"• Case {row['base_case_id']}, Bus {row['BUS_NUMBER']}: {row['PG']:.1f} MW generation, {row['VM']:.3f} p.u. voltage at {row['BASE_KV']} kV\n"
        
        elif pattern_name == 'slr_dlr_comparison':
            response = "**SLR vs DLR Rating Improvements Across Cases:**\n"
            for row in results:
                response += f"• Case {row['base_case_id']}, Contingency {row['contingency_case_id']}, Line {row['From_Bus']}-{row['To_Bus']}: +{row['Rating_Improvement']:.1f} MVA improvement (SLR: {row['SLR_Rating']:.1f} → DLR: {row['DLR_Rating']:.1f}), Violations: {row['SLR_Violation']:.1f}% → {row['DLR_Violation']:.1f}%\n"
        
        elif pattern_name == 'system_summary':
            response = f"**System Summary Across Cases:**\n"
            for row in results:
                response += f"• Case {row['base_case_id']}: {row['total_buses']} buses, {row['avg_voltage']:.3f} p.u. avg voltage, {row['total_load_mw']:.1f} MW load, {row['total_generation_mw']:.1f} MW gen, {row['voltage_violations']} violations\n"
        
        elif pattern_name == 'worst_violations':
            response = "**Critical Violations Across Cases:**\n"
            for row in results:
                violation_reduction = row['Violation_Reduction'] or 0
                response += f"• Case {row['base_case_id']}, Contingency {row['contingency_case_id']}, Line {row['From_Bus']}-{row['To_Bus']}: SLR {row['SLR_Violation']:.1f}%, DLR {row['DLR_Violation']:.1f}% (reduction: {violation_reduction:.1f}%)\n"
        
        elif pattern_name == 'efficiency_analysis':
            response = "**DLR Efficiency Analysis by Case:**\n"
            for row in results:
                response += f"• Case {row['base_case_id']}, Contingency {row['contingency_case_id']}: {row['total_lines']} lines analyzed, {row['lines_improved']} improved, avg +{row['avg_rating_improvement']:.1f} MVA, max +{row['max_rating_improvement']:.1f} MVA, avg violation reduction: {row['avg_violation_reduction']:.1f}%\n"
        
        else:
            response = f"**Query Results ({len(results)} records):**\n"
            for i, row in enumerate(results[:5]):  # Limit to first 5
                response += f"{i+1}. {dict(row)}\n"
        
        return response
    
    def get_response(self, question: str) -> Tuple[Optional[str], str]:
        """Get RAG response for a question"""
        # Match question to query pattern
        pattern_name = self.match_query_pattern(question)
        
        if not pattern_name:
            return None, "No matching database query found for this question."
        
        # Execute appropriate query
        query = self.query_patterns[pattern_name]['query']
        results = self.execute_query(query)
        
        # Format results
        formatted_response = self.format_results(results, pattern_name)
        context = f"Query executed: {pattern_name}, Results: {len(results)} records"
        
        return formatted_response, context

# Global RAG instance
_rag_instance = None

def initialize_rag(db_path: str = 'data.db'):
    """Initialize the global RAG instance"""
    global _rag_instance
    try:
        _rag_instance = SimpleRAG(db_path)
        print("Simple RAG system initialized successfully")
    except Exception as e:
        print(f"RAG initialization error: {e}")
        _rag_instance = None

def get_rag_response(question: str) -> Tuple[Optional[str], str]:
    """Get RAG response using global instance"""
    if _rag_instance is None:
        return None, "RAG system not initialized"
    
    return _rag_instance.get_response(question)

# Test function
def test_rag_system():
    """Test the RAG system with sample questions"""
    initialize_rag()
    
    test_questions = [
        "Show me available cases in the database",
        "List contingency cases and their violations", 
        "Compare performance across different cases",
        "Which buses have voltage violations across all cases?",
        "Show me overloaded transmission lines in all cases",
        "What are the worst violations across cases?",
        "Analyze DLR efficiency improvements by case",
        "Give me a system summary for all cases"
    ]
    
    print("Testing Enhanced RAG System with Case-wise Analysis:")
    print("=" * 60)
    
    for question in test_questions:
        print(f"\nQ: {question}")
        response, context = get_rag_response(question)
        if response:
            print(f"A: {response}")
        else:
            print(f"No response: {context}")
        print("-" * 40)

if __name__ == "__main__":
    test_rag_system()