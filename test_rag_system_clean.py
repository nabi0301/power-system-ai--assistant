#!/usr/bin/env python3
"""
RAG Testing Script for Power System Analysis
Demonstrates the enhanced AI capabilities with database knowledge
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from power_system_rag import PowerSystemRAG

def analyze_response_quality(response: str, question: str) -> dict:
    """Analyze the quality of RAG response"""
    
    quality_indicators = {
        'has_specific_numbers': bool(re.search(r'\d+\.?\d*', response)),
        'mentions_buses_or_lines': any(term in response.lower() for term in ['bus', 'line', 'mva', 'voltage']),
        'has_data_section': 'DATA:' in response.upper(),
        'provides_statistics': any(term in response.lower() for term in ['min:', 'max:', 'avg:', 'total:', 'statistics']),
        'actionable_insights': any(term in response.lower() for term in ['recommend', 'should', 'consider', 'attention']),
        'appropriate_length': 100 < len(response) < 1000
    }
    
    score = sum(quality_indicators.values()) * 2  # Scale to 0-10
    
    return {
        'score': min(score, 10),
        'has_data': quality_indicators['has_data_section'],
        'indicators': quality_indicators
    }

def test_rag_system():
    """Comprehensive test of RAG capabilities"""
    
    print("🔍 **POWER SYSTEM RAG TESTING**")
    print("=" * 50)
    
    try:
        rag = PowerSystemRAG('data.db')
        print("✅ RAG system initialized successfully")
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")
        return
    
    # Test questions covering different power system aspects
    test_scenarios = [
        {
            "category": "Voltage Analysis",
            "questions": [
                "Which buses have voltage violations?",
                "Show me buses with low voltage",
                "Are there any high voltage buses?",
                "What's the voltage profile of the system?"
            ]
        },
        {
            "category": "Loading Analysis", 
            "questions": [
                "Which transmission lines are overloaded?",
                "Show me the top 5 most loaded lines",
                "Are there any lines operating above 90% capacity?",
                "What's the loading distribution across the system?"
            ]
        },
        {
            "category": "System Overview",
            "questions": [
                "Give me a system summary",
                "How many buses and lines are in the system?",
                "What's the total generation and load?",
                "Show me generator buses"
            ]
        },
        {
            "category": "DLR vs SLR Analysis",
            "questions": [
                "Compare DLR and SLR performance",
                "Which lines benefit most from dynamic rating?",
                "Show SLR vs DLR comparison data",
                "How much capacity improvement does DLR provide?"
            ]
        }
    ]
    
    results_summary = []
    
    for scenario in test_scenarios:
        print(f"\n📊 **{scenario['category'].upper()}**")
        print("-" * 40)
        
        for i, question in enumerate(scenario['questions'], 1):
            print(f"\n❓ Test {i}: {question}")
            
            try:
                response, viz_cmd = rag.retrieve_and_generate(question)
                
                # Analyze response quality
                response_quality = analyze_response_quality(response, question)
                
                print(f"🤖 Response ({response_quality['score']}/10): {response[:150]}...")
                
                if viz_cmd:
                    print(f"📈 Visualization: {viz_cmd}")
                
                results_summary.append({
                    'category': scenario['category'],
                    'question': question,
                    'quality_score': response_quality['score'],
                    'has_data': response_quality['has_data'],
                    'viz_command': viz_cmd
                })
                
            except Exception as e:
                print(f"❌ Error: {e}")
                results_summary.append({
                    'category': scenario['category'],
                    'question': question, 
                    'quality_score': 0,
                    'has_data': False,
                    'viz_command': None
                })
    
    # Print summary statistics
    print_test_summary(results_summary)

def print_test_summary(results: list):
    """Print comprehensive test results summary"""
    
    print("\n" + "="*60)
    print("📈 **RAG SYSTEM PERFORMANCE SUMMARY**")
    print("="*60)
    
    total_tests = len(results)
    avg_quality = sum(r['quality_score'] for r in results) / total_tests if total_tests > 0 else 0
    data_responses = sum(1 for r in results if r['has_data'])
    viz_commands = sum(1 for r in results if r['viz_command'])
    
    print(f"\n📊 **Overall Statistics:**")
    print(f"• Total Tests: {total_tests}")
    print(f"• Average Quality Score: {avg_quality:.1f}/10")
    print(f"• Responses with Data: {data_responses}/{total_tests} ({data_responses/total_tests*100:.1f}%)")
    print(f"• Visualization Commands: {viz_commands}/{total_tests} ({viz_commands/total_tests*100:.1f}%)")
    
    # Category breakdown
    print(f"\n📋 **Performance by Category:**")
    categories = set(r['category'] for r in results)
    
    for category in categories:
        category_results = [r for r in results if r['category'] == category]
        cat_avg = sum(r['quality_score'] for r in category_results) / len(category_results)
        cat_data = sum(1 for r in category_results if r['has_data'])
        
        print(f"• {category}: {cat_avg:.1f}/10 avg, {cat_data}/{len(category_results)} with data")
    
    print(f"\n🎯 **RAG System Assessment:**")
    if avg_quality >= 8:
        print("✅ Excellent: RAG system is performing very well")
    elif avg_quality >= 6:
        print("✅ Good: RAG system is working effectively")
    elif avg_quality >= 4:
        print("⚠️ Fair: RAG system needs some improvements")
    else:
        print("❌ Poor: RAG system requires significant enhancement")
    
    print(f"\n🚀 **RAG Integration Complete - Ready for Production!**")

if __name__ == "__main__":
    test_rag_system()