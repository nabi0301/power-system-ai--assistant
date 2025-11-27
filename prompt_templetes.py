#!/usr/bin/env python3
"""
IEEE 118 Bus System - Organized Prompt Templates
"""

class IEEE118PromptTemplates:
    def __init__(self):
        self.system_info = {
            'total_buses': 118,
            'total_branches': 186,
            'generators': [10, 12, 25, 26, 31, 46, 49, 54, 59, 61, 65, 66, 69, 80, 87, 89, 100, 103, 111],
            'voltage_levels': ['138kV', '230kV', '345kV'],
            'areas': 3
        }
    
    def get_prompt_categories(self):
        """Return organized prompt categories"""
        return {
            'NETWORK_VISUALIZATION': self._get_network_prompts(),
            'SYSTEM_ANALYSIS': self._get_analysis_prompts(),
            'CASE_STUDIES': self._get_case_study_prompts(),
            'COMPONENT_ANALYSIS': self._get_component_prompts(),
            'OPTIMIZATION': self._get_optimization_prompts(),
            'QUICK_COMMANDS': self._get_quick_commands()
        }
    
    def _get_network_prompts(self):
        """Network visualization prompts"""
        return {
            'basic_network': [
                "Show network graph",
                "Display IEEE 118 network topology", 
                "Show me the power system network",
                "Create network diagram"
            ],
            'case_specific': [
                "Show network for case {case_id}",
                "Display network graph for case {case_id}, contingency {contingency_id}",
                "Network topology for base case {case_id}",
                "Contingency network view case {case_id}"
            ]
        }
    
    def _get_analysis_prompts(self):
        """System analysis prompts"""
        return {
            'voltage_analysis': [
                "Analyze voltage profile",
                "Show voltage violations", 
                "Bus voltage analysis for case {case_id}",
                "Voltage stability assessment"
            ]
        }
    
    def _get_case_study_prompts(self):
        """Case study prompts"""
        return {
            'base_case': [
                "Analyze base case {case_id}",
                "Base case power flow for case {case_id}"
            ]
        }
    
    def _get_component_prompts(self):
        """Component analysis prompts"""
        return {
            'bus_analysis': [
                "Analyze bus {bus_number}",
                "Bus {bus_number} voltage status"
            ]
        }
    
    def _get_optimization_prompts(self):
        """Optimization prompts"""
        return {
            'efficiency': [
                "Optimize system efficiency",
                "Minimize transmission losses"
            ]
        }
    
    def _get_quick_commands(self):
        """Quick commands"""
        return {
            'instant_views': [
                "Quick voltage check",
                "Fast loading scan"
            ]
        }
    
    def generate_example_prompts(self, category=None):
        """Generate example prompts"""
        if category:
            return self.get_prompt_categories().get(category, {})
        
        examples = []
        for cat_name, cat_prompts in self.get_prompt_categories().items():
            examples.append(f"\n🔹 **{cat_name.replace('_', ' ').title()}:**")
            for prompt_type, prompts in cat_prompts.items():
                examples.append(f"   • {prompts[0]}")
        
        return "\n".join(examples)
    
    def get_contextual_suggestions(self, current_viz, recent_actions):
        """Get contextual suggestions"""
        suggestions = []
        
        if current_viz == 'network_view':
            suggestions.extend([
                "Try 'analyze voltage violations' to check system health",
                "Ask 'show loading analysis' to see line utilization"
            ])
        
        return suggestions[:3]

# Global instance
ieee118_prompts = IEEE118PromptTemplates()