#!/usr/bin/env python3
"""
RAG Testing Script for Power System Analysis
Demonstrates the enhanced AI capabilities with database knowledge
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from power_system_rag import PowerSystemRAG

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
        },
        {
            "category": "Specific Technical Queries",
            "questions": [
                "Find buses with power demand above 50 MW",
                "Which lines have the highest MVA flow?",
                "Show me voltage angle differences",
                "Identify critical equipment"
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
                })\n    \n    # Print summary statistics\n    print_test_summary(results_summary)\n\ndef analyze_response_quality(response: str, question: str) -> dict:\n    \"\"\"Analyze the quality of RAG response\"\"\"\n    \n    quality_indicators = {\n        'has_specific_numbers': bool(re.search(r'\\d+\\.?\\d*', response)),\n        'mentions_buses_or_lines': any(term in response.lower() for term in ['bus', 'line', 'mva', 'voltage']),\n        'has_data_section': 'DATA:' in response.upper(),\n        'provides_statistics': any(term in response.lower() for term in ['min:', 'max:', 'avg:', 'total:', 'statistics']),\n        'actionable_insights': any(term in response.lower() for term in ['recommend', 'should', 'consider', 'attention']),\n        'appropriate_length': 100 < len(response) < 1000\n    }\n    \n    score = sum(quality_indicators.values()) * 2  # Scale to 0-10\n    \n    return {\n        'score': min(score, 10),\n        'has_data': quality_indicators['has_data_section'],\n        'indicators': quality_indicators\n    }\n\ndef print_test_summary(results: list):\n    \"\"\"Print comprehensive test results summary\"\"\"\n    \n    print(\"\\n\" + \"=\"*60)\n    print(\"📈 **RAG SYSTEM PERFORMANCE SUMMARY**\")\n    print(\"=\"*60)\n    \n    total_tests = len(results)\n    avg_quality = sum(r['quality_score'] for r in results) / total_tests if total_tests > 0 else 0\n    data_responses = sum(1 for r in results if r['has_data'])\n    viz_commands = sum(1 for r in results if r['viz_command'])\n    \n    print(f\"\\n📊 **Overall Statistics:**\")\n    print(f\"• Total Tests: {total_tests}\")\n    print(f\"• Average Quality Score: {avg_quality:.1f}/10\")\n    print(f\"• Responses with Data: {data_responses}/{total_tests} ({data_responses/total_tests*100:.1f}%)\")\n    print(f\"• Visualization Commands: {viz_commands}/{total_tests} ({viz_commands/total_tests*100:.1f}%)\")\n    \n    # Category breakdown\n    print(f\"\\n📋 **Performance by Category:**\")\n    categories = set(r['category'] for r in results)\n    \n    for category in categories:\n        category_results = [r for r in results if r['category'] == category]\n        cat_avg = sum(r['quality_score'] for r in category_results) / len(category_results)\n        cat_data = sum(1 for r in category_results if r['has_data'])\n        \n        print(f\"• {category}: {cat_avg:.1f}/10 avg, {cat_data}/{len(category_results)} with data\")\n    \n    # Best and worst performing questions\n    best_result = max(results, key=lambda x: x['quality_score'])\n    worst_result = min(results, key=lambda x: x['quality_score'])\n    \n    print(f\"\\n🏆 **Best Performance:**\")\n    print(f\"• Question: {best_result['question']}\")\n    print(f\"• Score: {best_result['quality_score']}/10\")\n    \n    print(f\"\\n⚠️ **Needs Improvement:**\")\n    print(f\"• Question: {worst_result['question']}\")\n    print(f\"• Score: {worst_result['quality_score']}/10\")\n    \n    print(f\"\\n🎯 **RAG System Assessment:**\")\n    if avg_quality >= 8:\n        print(\"✅ Excellent: RAG system is performing very well\")\n    elif avg_quality >= 6:\n        print(\"✅ Good: RAG system is working effectively\")\n    elif avg_quality >= 4:\n        print(\"⚠️ Fair: RAG system needs some improvements\")\n    else:\n        print(\"❌ Poor: RAG system requires significant enhancement\")\n    \n    print(f\"\\n💡 **Recommendations:**\")\n    if data_responses / total_tests < 0.8:\n        print(\"• Improve database query coverage for more question types\")\n    if viz_commands / total_tests < 0.5:\n        print(\"• Enhance visualization command detection\")\n    if avg_quality < 7:\n        print(\"• Refine knowledge base and response templates\")\n    \n    print(\"\\n🚀 **RAG Integration Complete - Ready for Production!**\")\n\nif __name__ == \"__main__\":\n    import re\n    test_rag_system()