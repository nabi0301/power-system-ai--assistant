#!/usr/bin/env python3
"""
Integrated Corrective Action Comparison Module
Ready-to-use module for comparing corrective actions across Base Case, Contingency, SLR, and DLR scenarios
Shows effectiveness of corrective actions without modifying existing system
"""

import psycopg2
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def compare_corrective_action_effectiveness(case_id=42, contingency_id=455, show_plots=True):
    """
    MAIN FUNCTION: Compare corrective action effectiveness across scenarios
    
    Args:
        case_id: Base case ID to analyze
        contingency_id: Contingency case ID for comparison
        show_plots: Whether to generate and save visualization
        
    Returns:
        dict: Comprehensive comparison results
    """
    
    try:
        print(f"🔍 Analyzing Corrective Action Effectiveness...")
        print(f"   Base Case: {case_id} | Contingency Case: {contingency_id}")
        
        # Connect to database
        conn = psycopg2.connect(
            host='localhost', port='5432', database='118',
            user='postgres', password='pnnl'
        )
        
        # Load and compare all scenarios
        comparison_results = {
            'scenarios': {},
            'effectiveness_ranking': [],
            'corrective_actions': [],
            'recommendations': {},
            'summary': {}
        }
        
        # Analyze each scenario
        scenarios = load_all_scenario_data(conn, case_id, contingency_id)
        comparison_results['scenarios'] = scenarios
        
        # Generate corrective actions based on worst scenario
        worst_scenario_key = find_scenario_with_most_violations(scenarios)
        if worst_scenario_key and scenarios[worst_scenario_key]['violations']:
            comparison_results['corrective_actions'] = generate_corrective_actions(
                scenarios[worst_scenario_key]
            )
        
        # Rank scenarios by effectiveness
        comparison_results['effectiveness_ranking'] = rank_scenarios_by_effectiveness(scenarios)
        
        # Generate implementation recommendations
        comparison_results['recommendations'] = generate_implementation_recommendations(
            scenarios, comparison_results['corrective_actions']
        )
        
        # Create summary
        comparison_results['summary'] = create_comparison_summary(comparison_results)
        
        # Generate visualization if requested
        if show_plots:
            fig = create_comparison_visualization(comparison_results, case_id, contingency_id)
            filename = f"corrective_action_comparison_case_{case_id}_cont_{contingency_id}.html"
            fig.write_html(filename)
            print(f"📊 Visualization saved to: {filename}")
        
        conn.close()
        
        # Print summary
        print_comparison_summary(comparison_results)
        
        return comparison_results
        
    except Exception as e:
        print(f"❌ Error in corrective action comparison: {e}")
        return {'error': str(e)}

def load_all_scenario_data(conn, case_id, contingency_id):
    """Load data for all scenarios: Base, Contingency, SLR, DLR"""
    
    scenarios = {}
    
    # 1. Base Case Analysis
    print("📊 Analyzing Base Case...")
    scenarios['base'] = analyze_scenario(
        conn, 'base_buses', 'base_branches', 
        f'case_id = {case_id}', f'Base Case {case_id}'
    )
    
    # 2. Contingency Case Analysis
    print("📊 Analyzing Contingency Case...")
    scenarios['contingency'] = analyze_scenario(
        conn, 'contingencybusdata', 'contingencybranchdata',
        f'base_case_id = {case_id} AND contingency_case_id = {contingency_id}',
        f'Contingency Case {contingency_id}'
    )
    
    # 3. SLR Analysis
    print("📊 Analyzing SLR Case...")
    scenarios['slr'] = analyze_scenario(
        conn, 'slr_buses', 'slr_branches', 
        f'slr_case_id = {case_id}', f'SLR Case {case_id}',
        voltage_col='vm_pu', loading_col='loading_percent'
    )
    
    # 4. DLR Analysis
    print("📊 Analyzing DLR Case...")
    scenarios['dlr'] = analyze_scenario(
        conn, 'dlr_buses', 'dlr_branches', 
        f'dlr_case_id = {case_id}', f'DLR Case {case_id}',
        voltage_col='vm_pu', loading_col='loading_percent'
    )
    
    return scenarios

def analyze_scenario(conn, bus_table, branch_table, condition, name, voltage_col='vm', loading_col=None):
    """Analyze a single scenario for violations and system health"""
    
    scenario_data = {
        'name': name,
        'violations': [],
        'system_health': 100.0,
        'total_buses': 0,
        'total_branches': 0,
        'voltage_violations': 0,
        'loading_violations': 0,
        'avg_voltage': 1.0,
        'max_loading': 0.0
    }
    
    try:
        # Voltage Analysis
        bus_query = f"""
            SELECT bus_number, {voltage_col} as voltage, base_kv 
            FROM {bus_table} 
            WHERE {condition}
            ORDER BY bus_number
        """
        
        buses_df = pd.read_sql_query(bus_query, conn)
        scenario_data['total_buses'] = len(buses_df)
        
        if not buses_df.empty:
            scenario_data['avg_voltage'] = float(buses_df['voltage'].mean())
            
            # Find voltage violations (0.95 - 1.05 pu range)
            voltage_violations = buses_df[
                (buses_df['voltage'] < 0.95) | (buses_df['voltage'] > 1.05)
            ]
            
            scenario_data['voltage_violations'] = len(voltage_violations)
            
            for _, row in voltage_violations.iterrows():
                violation = {
                    'type': 'Voltage',
                    'location': f"Bus {int(row['bus_number'])}",
                    'value': float(row['voltage']),
                    'limit': 0.95 if row['voltage'] < 0.95 else 1.05,
                    'severity': 'High' if abs(row['voltage'] - 1.0) > 0.08 else 'Medium'
                }
                scenario_data['violations'].append(violation)
        
        # Loading Analysis
        if loading_col:
            # SLR/DLR have loading_percent column
            branch_query = f"""
                SELECT from_bus, to_bus, {loading_col} as loading_percent
                FROM {branch_table} 
                WHERE {condition} AND mva_rating > 0
                ORDER BY from_bus, to_bus
            """
        else:
            # Base/Contingency need to calculate loading
            branch_query = f"""
                SELECT from_bus, to_bus, mva, rate,
                       CASE WHEN rate > 0 THEN (mva / rate) * 100 ELSE 0 END as loading_percent
                FROM {branch_table} 
                WHERE {condition} AND rate > 0
                ORDER BY from_bus, to_bus
            """
        
        branches_df = pd.read_sql_query(branch_query, conn)
        scenario_data['total_branches'] = len(branches_df)
        
        if not branches_df.empty:
            scenario_data['max_loading'] = float(branches_df['loading_percent'].max())
            
            # Find loading violations (>100%)
            loading_violations = branches_df[branches_df['loading_percent'] > 100]
            scenario_data['loading_violations'] = len(loading_violations)
            
            for _, row in loading_violations.iterrows():
                violation = {
                    'type': 'Loading',
                    'location': f"Line {int(row['from_bus'])}-{int(row['to_bus'])}",
                    'value': float(row['loading_percent']),
                    'limit': 100.0,
                    'severity': 'Critical' if row['loading_percent'] > 120 else 'High'
                }
                scenario_data['violations'].append(violation)
        
        # Calculate system health
        total_violations = len(scenario_data['violations'])
        total_elements = scenario_data['total_buses'] + scenario_data['total_branches']
        if total_elements > 0:
            violation_rate = (total_violations / total_elements) * 100
            scenario_data['system_health'] = max(0, 100 - (violation_rate * 2))
        
        print(f"   {name}: {total_violations} violations, {scenario_data['system_health']:.1f}% health")
        
    except Exception as e:
        print(f"⚠️ Error analyzing {name}: {e}")
        scenario_data['error'] = str(e)
    
    return scenario_data

def find_scenario_with_most_violations(scenarios):
    """Find scenario with most violations for corrective action generation"""
    
    max_violations = 0
    worst_scenario = None
    
    for scenario_key, data in scenarios.items():
        violation_count = len(data.get('violations', []))
        if violation_count > max_violations:
            max_violations = violation_count
            worst_scenario = scenario_key
    
    return worst_scenario

def generate_corrective_actions(scenario_data):
    """Generate corrective actions based on violations"""
    
    actions = []
    
    for violation in scenario_data.get('violations', []):
        if violation['type'] == 'Voltage':
            # Voltage corrective action
            bus_num = violation['location'].split()[1]
            voltage = violation['value']
            
            if voltage < 0.95:
                # Low voltage - capacitor
                capacitor_size = max(1, int((0.95 - voltage) * 100))
                action = {
                    'target': violation['location'],
                    'type': 'Voltage Support',
                    'action': f"Install {capacitor_size} MVAR capacitor bank",
                    'current_value': f"{voltage:.3f} pu",
                    'expected_value': f"{min(1.02, voltage + 0.05):.3f} pu",
                    'priority': violation['severity'],
                    'cost': capacitor_size * 50000,
                    'timeline': '4-8 weeks',
                    'effectiveness': 'High' if abs(voltage - 0.95) > 0.05 else 'Medium'
                }
            else:
                # High voltage - reactor
                reactor_size = max(1, int((voltage - 1.05) * 100))
                action = {
                    'target': violation['location'],
                    'type': 'Voltage Reduction',
                    'action': f"Install {reactor_size} MVAR reactor",
                    'current_value': f"{voltage:.3f} pu",
                    'expected_value': f"{max(0.98, voltage - 0.05):.3f} pu",
                    'priority': violation['severity'],
                    'cost': reactor_size * 45000,
                    'timeline': '3-6 weeks',
                    'effectiveness': 'High'
                }
            
        elif violation['type'] == 'Loading':
            # Loading corrective action
            loading = violation['value']
            overload = loading - 100
            
            if overload > 50:
                action = {
                    'target': violation['location'],
                    'type': 'Emergency Capacity Addition',
                    'action': f"Add parallel transmission line",
                    'current_value': f"{loading:.1f}%",
                    'expected_value': f"{max(85, loading - overload - 15):.1f}%",
                    'priority': 'Critical',
                    'cost': int(overload * 2000000),
                    'timeline': '36-52 weeks',
                    'effectiveness': 'Critical'
                }
            elif overload > 20:
                action = {
                    'target': violation['location'],
                    'type': 'Capacity Upgrade',
                    'action': f"Upgrade conductor capacity",
                    'current_value': f"{loading:.1f}%",
                    'expected_value': f"{max(85, loading - overload - 15):.1f}%",
                    'priority': 'High',
                    'cost': int(overload * 1500000),
                    'timeline': '16-26 weeks',
                    'effectiveness': 'High'
                }
            else:
                action = {
                    'target': violation['location'],
                    'type': 'Load Management',
                    'action': f"Implement load transfer",
                    'current_value': f"{loading:.1f}%",
                    'expected_value': f"{max(85, loading - overload - 15):.1f}%",
                    'priority': 'Medium',
                    'cost': int(overload * 500000),
                    'timeline': '4-8 weeks',
                    'effectiveness': 'Medium'
                }
        
        actions.append(action)
    
    # Sort by priority and cost
    priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
    actions.sort(key=lambda x: (priority_order.get(x['priority'], 4), x['cost']))
    
    return actions

def rank_scenarios_by_effectiveness(scenarios):
    """Rank scenarios by overall effectiveness (health score)"""
    
    ranking = []
    
    for scenario_key, data in scenarios.items():
        if 'error' not in data:
            ranking.append({
                'scenario': scenario_key,
                'name': data['name'],
                'health_score': data['system_health'],
                'violations': len(data.get('violations', [])),
                'recommendation': get_effectiveness_recommendation(
                    data['system_health'], len(data.get('violations', []))
                )
            })
    
    # Sort by health score (descending)
    ranking.sort(key=lambda x: -x['health_score'])
    
    return ranking

def get_effectiveness_recommendation(health_score, violations):
    """Get recommendation based on scenario performance"""
    
    if health_score >= 99 and violations == 0:
        return "Excellent - Target State"
    elif health_score >= 95:
        return "Very Good - Minor Adjustments"
    elif health_score >= 90:
        return "Good - Some Improvements Needed"
    elif health_score >= 80:
        return "Acceptable - Moderate Corrective Actions"
    else:
        return "Poor - Significant Improvements Required"

def generate_implementation_recommendations(scenarios, corrective_actions):
    """Generate implementation recommendations"""
    
    recommendations = {
        'best_scenario': None,
        'worst_scenario': None,
        'priority_actions': [],
        'total_cost': 0,
        'quick_wins': [],
        'strategy': ''
    }
    
    # Find best/worst scenarios
    health_scores = {k: v['system_health'] for k, v in scenarios.items() if 'error' not in v}
    if health_scores:
        recommendations['best_scenario'] = max(health_scores, key=health_scores.get)
        recommendations['worst_scenario'] = min(health_scores, key=health_scores.get)
    
    # Priority actions (top 3)
    if corrective_actions:
        recommendations['priority_actions'] = corrective_actions[:3]
        recommendations['total_cost'] = sum(action['cost'] for action in recommendations['priority_actions'])
        
        # Quick wins (≤8 weeks)
        recommendations['quick_wins'] = [
            action for action in corrective_actions 
            if 'weeks' in action['timeline'] and int(action['timeline'].split('-')[0]) <= 8
        ]
    
    # Strategy recommendation
    if recommendations['best_scenario'] and recommendations['worst_scenario']:
        best_health = scenarios[recommendations['best_scenario']]['system_health']
        worst_health = scenarios[recommendations['worst_scenario']]['system_health']
        health_gap = best_health - worst_health
        
        if health_gap > 15:
            recommendations['strategy'] = f"Significant improvement potential ({health_gap:.1f}% gap). Focus on corrective actions."
        elif health_gap > 5:
            recommendations['strategy'] = f"Moderate improvement potential ({health_gap:.1f}% gap). Targeted actions recommended."
        else:
            recommendations['strategy'] = "Scenarios perform similarly. Focus on maintaining best-case conditions."
    
    return recommendations

def create_comparison_summary(comparison_results):
    """Create comprehensive comparison summary"""
    
    summary = {
        'total_scenarios': len(comparison_results['scenarios']),
        'total_violations': 0,
        'total_actions': len(comparison_results['corrective_actions']),
        'scenario_performance': {},
        'action_breakdown': {},
        'cost_analysis': {}
    }
    
    # Scenario performance
    for scenario_key, data in comparison_results['scenarios'].items():
        if 'error' not in data:
            violations = len(data.get('violations', []))
            summary['total_violations'] += violations
            summary['scenario_performance'][scenario_key] = {
                'health': data['system_health'],
                'violations': violations,
                'status': 'Good' if data['system_health'] >= 95 else 'Needs Attention'
            }
    
    # Action breakdown
    if comparison_results['corrective_actions']:
        action_types = {}
        total_cost = 0
        
        for action in comparison_results['corrective_actions']:
            action_type = action['type']
            action_types[action_type] = action_types.get(action_type, 0) + 1
            total_cost += action['cost']
        
        summary['action_breakdown'] = action_types
        summary['cost_analysis'] = {
            'total_cost': total_cost,
            'average_cost': total_cost / len(comparison_results['corrective_actions']),
            'priority_cost': sum(action['cost'] for action in comparison_results['corrective_actions'][:3])
        }
    
    return summary

def create_comparison_visualization(comparison_results, case_id, contingency_id):
    """Create comparison visualization"""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Scenario Health Comparison", "Corrective Action Priorities",
            "Implementation Timeline", "Cost Distribution"
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "pie"}]
        ]
    )
    
    # 1. Scenario Health Comparison
    if comparison_results['effectiveness_ranking']:
        scenarios = [item['name'] for item in comparison_results['effectiveness_ranking']]
        health_scores = [item['health_score'] for item in comparison_results['effectiveness_ranking']]
        colors = ['green' if h >= 95 else 'yellow' if h >= 85 else 'red' for h in health_scores]
        
        fig.add_trace(
            go.Bar(x=scenarios, y=health_scores, marker_color=colors, name="Health Score"),
            row=1, col=1
        )
    
    # 2. Corrective Action Priorities
    if comparison_results['corrective_actions']:
        actions = comparison_results['corrective_actions'][:5]
        action_labels = [a['target'] for a in actions]
        action_costs = [a['cost'] / 1000000 for a in actions]  # Convert to millions
        priority_colors = {'Critical': 'darkred', 'High': 'red', 'Medium': 'orange'}
        colors = [priority_colors.get(a['priority'], 'gray') for a in actions]
        
        fig.add_trace(
            go.Bar(x=action_labels, y=action_costs, marker_color=colors, name="Cost ($M)"),
            row=1, col=2
        )
    
    # 3. Implementation Timeline
    if comparison_results['corrective_actions']:
        actions = comparison_results['corrective_actions'][:4]
        timeline_weeks = []
        for action in actions:
            # Extract weeks from timeline string
            weeks_str = action['timeline'].split('-')[0]
            timeline_weeks.append(int(weeks_str))
        
        cumulative_weeks = [sum(timeline_weeks[:i+1]) for i in range(len(timeline_weeks))]
        action_sequence = [f"Action {i+1}" for i in range(len(actions))]
        
        fig.add_trace(
            go.Scatter(x=action_sequence, y=cumulative_weeks, mode='markers+lines', 
                      marker=dict(size=10), name="Timeline"),
            row=2, col=1
        )
    
    # 4. Cost Distribution
    if comparison_results['corrective_actions']:
        action_types = {}
        for action in comparison_results['corrective_actions']:
            action_type = action['type']
            action_types[action_type] = action_types.get(action_type, 0) + action['cost']
        
        fig.add_trace(
            go.Pie(labels=list(action_types.keys()), values=list(action_types.values()), 
                   name="Cost Distribution"),
            row=2, col=2
        )
    
    # Update layout
    fig.update_layout(
        title=f"Corrective Action Effectiveness Comparison - Case {case_id} vs Contingency {contingency_id}",
        height=700,
        showlegend=False
    )
    
    fig.update_yaxes(title_text="Health Score (%)", row=1, col=1)
    fig.update_yaxes(title_text="Cost ($M)", row=1, col=2)
    fig.update_yaxes(title_text="Cumulative Weeks", row=2, col=1)
    
    return fig

def print_comparison_summary(comparison_results):
    """Print formatted comparison summary"""
    
    print("\n" + "="*80)
    print("CORRECTIVE ACTION EFFECTIVENESS COMPARISON SUMMARY")
    print("="*80)
    
    # Best vs Worst Scenario
    if comparison_results['effectiveness_ranking']:
        best = comparison_results['effectiveness_ranking'][0]
        worst = comparison_results['effectiveness_ranking'][-1]
        
        print(f"\n🏆 BEST PERFORMING SCENARIO:")
        print(f"   {best['name']} - {best['health_score']:.1f}% system health")
        print(f"   Violations: {best['violations']} | {best['recommendation']}")
        
        print(f"\n⚠️  NEEDS MOST IMPROVEMENT:")
        print(f"   {worst['name']} - {worst['health_score']:.1f}% system health")
        print(f"   Violations: {worst['violations']} | {worst['recommendation']}")
    
    # Priority Corrective Actions
    if comparison_results['recommendations']['priority_actions']:
        print(f"\n🎯 TOP PRIORITY CORRECTIVE ACTIONS:")
        for i, action in enumerate(comparison_results['recommendations']['priority_actions'], 1):
            print(f"   {i}. {action['target']} - {action['priority']} Priority")
            print(f"      Action: {action['action']}")
            print(f"      Current: {action['current_value']} → Expected: {action['expected_value']}")
            print(f"      Cost: ${action['cost']:,} | Timeline: {action['timeline']}")
    
    # Implementation Strategy
    if comparison_results['recommendations']['strategy']:
        print(f"\n📋 IMPLEMENTATION STRATEGY:")
        print(f"   {comparison_results['recommendations']['strategy']}")
        
        if comparison_results['recommendations']['total_cost']:
            print(f"   Priority Investment: ${comparison_results['recommendations']['total_cost']:,}")
    
    # Quick Wins
    if comparison_results['recommendations']['quick_wins']:
        print(f"\n⚡ QUICK WINS (≤8 weeks):")
        for action in comparison_results['recommendations']['quick_wins'][:3]:
            print(f"   • {action['target']}: {action['action']}")
    
    print("\n" + "="*80)

# Integration-ready function for existing systems
def run_corrective_action_comparison(case_id=42, contingency_id=455):
    """
    Integration-ready function for existing power system analysis tools
    Use this function to add corrective action comparison to your workflow
    """
    
    return compare_corrective_action_effectiveness(case_id, contingency_id, show_plots=True)

if __name__ == "__main__":
    # Run comparison analysis
    results = compare_corrective_action_effectiveness(case_id=42, contingency_id=455)