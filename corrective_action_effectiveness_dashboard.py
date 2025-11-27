#!/usr/bin/env python3
"""
Corrective Action Effectiveness Dashboard
Simplified comparative analysis showing corrective action effectiveness
across Base Case, Contingency, SLR, and DLR scenarios
"""

import psycopg2
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def create_corrective_action_effectiveness_dashboard(case_id=42, contingency_id=455):
    """
    Create simplified effectiveness dashboard comparing corrective actions
    across different scenarios to show what works best
    """
    
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            host='localhost',
            port='5432', 
            database='118',
            user='postgres',
            password='pnnl'
        )
        
        print(f"✅ Connected to PostgreSQL for effectiveness analysis - Case {case_id}")
        
        # Load and analyze all scenarios
        effectiveness_data = analyze_corrective_action_effectiveness(conn, case_id, contingency_id)
        
        # Create effectiveness dashboard
        fig = create_effectiveness_dashboard(effectiveness_data, case_id, contingency_id)
        
        conn.close()
        return fig, effectiveness_data
        
    except Exception as e:
        print(f"❌ Error in effectiveness analysis: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Effectiveness Analysis Error: {str(e)}",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font_size=14
        )
        fig.update_layout(title="Corrective Action Effectiveness Analysis - Error", height=600)
        return fig, {}

def analyze_corrective_action_effectiveness(conn, case_id, contingency_id):
    """Analyze effectiveness of corrective actions across scenarios"""
    
    effectiveness_data = {
        'scenarios': {},
        'corrective_actions': [],
        'effectiveness_ranking': [],
        'recommendations': {}
    }
    
    # Define scenarios to analyze
    scenarios_config = {
        'base': {
            'name': f'Base Case {case_id}',
            'bus_table': 'base_buses',
            'branch_table': 'base_branches',
            'condition': f'case_id = {case_id}'
        },
        'contingency': {
            'name': f'Contingency Case {contingency_id}',
            'bus_table': 'contingencybusdata',
            'branch_table': 'contingencybranchdata',
            'condition': f'base_case_id = {case_id} AND contingency_case_id = {contingency_id}'
        },
        'slr': {
            'name': 'SLR Analysis',
            'bus_table': 'slr_buses',
            'branch_table': 'slr_branches',
            'condition': 'slr_case_id = 42',  # Match with case_id mapping
            'voltage_col': 'vm_pu',
            'angle_col': 'va_degrees'
        },
        'dlr': {
            'name': 'DLR Analysis',
            'bus_table': 'dlr_buses',
            'branch_table': 'dlr_branches',
            'condition': 'dlr_case_id = 42',  # Match with case_id mapping
            'voltage_col': 'vm_pu',
            'angle_col': 'va_degrees'
        }
    }
    
    # Analyze each scenario
    for scenario_key, config in scenarios_config.items():
        try:
            scenario_data = analyze_single_scenario(conn, config, scenario_key)
            effectiveness_data['scenarios'][scenario_key] = scenario_data
            print(f"📊 {config['name']}: {scenario_data['total_violations']} total violations")
        except Exception as e:
            print(f"⚠️ Could not analyze {config['name']}: {e}")
    
    # Generate corrective actions based on worst-case scenario
    worst_scenario = find_worst_scenario(effectiveness_data['scenarios'])
    if worst_scenario:
        effectiveness_data['corrective_actions'] = generate_targeted_corrective_actions(
            effectiveness_data['scenarios'][worst_scenario]
        )
    
    # Rank scenario effectiveness
    effectiveness_data['effectiveness_ranking'] = rank_scenario_effectiveness(effectiveness_data['scenarios'])
    
    # Generate recommendations
    effectiveness_data['recommendations'] = generate_effectiveness_recommendations(effectiveness_data)
    
    return effectiveness_data

def analyze_single_scenario(conn, config, scenario_key):
    """Analyze a single scenario for violations and system health"""
    
    scenario_data = {
        'name': config['name'],
        'voltage_violations': [],
        'loading_violations': [],
        'total_violations': 0,
        'system_health': 0,
        'avg_voltage': 0,
        'max_loading': 0,
        'buses_analyzed': 0,
        'branches_analyzed': 0
    }
    
    # Voltage analysis
    voltage_col = config.get('voltage_col', 'vm')
    bus_query = f"""
        SELECT bus_number, {voltage_col} as voltage, base_kv 
        FROM {config['bus_table']} 
        WHERE {config['condition']}
        ORDER BY bus_number
    """
    
    try:
        buses_df = pd.read_sql_query(bus_query, conn)
        scenario_data['buses_analyzed'] = len(buses_df)
        
        if not buses_df.empty:
            # Find voltage violations (outside 0.95-1.05 pu range)
            voltage_violations = buses_df[
                (buses_df['voltage'] < 0.95) | (buses_df['voltage'] > 1.05)
            ]
            
            scenario_data['voltage_violations'] = [
                {
                    'bus': int(row['bus_number']),
                    'voltage': float(row['voltage']),
                    'severity': 'High' if abs(row['voltage'] - 1.0) > 0.08 else 'Medium',
                    'violation_type': 'Low' if row['voltage'] < 0.95 else 'High'
                }
                for _, row in voltage_violations.iterrows()
            ]
            
            scenario_data['avg_voltage'] = float(buses_df['voltage'].mean())
    
    except Exception as e:
        print(f"⚠️ Voltage analysis failed for {config['name']}: {e}")
    
    # Loading analysis
    if scenario_key in ['slr', 'dlr']:
        # SLR/DLR branches have different column names
        branch_query = f"""
            SELECT from_bus, to_bus, mva_flow as mva, mva_rating as rate, loading_percent
            FROM {config['branch_table']} 
            WHERE {config['condition']} AND mva_rating > 0
            ORDER BY from_bus, to_bus
        """
    else:
        # Base and contingency branches
        branch_query = f"""
            SELECT from_bus, to_bus, mva, rate, 
                   CASE WHEN rate > 0 THEN (mva / rate) * 100 ELSE 0 END as loading_percent
            FROM {config['branch_table']} 
            WHERE {config['condition']} AND rate > 0
            ORDER BY from_bus, to_bus
        """
    
    try:
        branches_df = pd.read_sql_query(branch_query, conn)
        scenario_data['branches_analyzed'] = len(branches_df)
        
        if not branches_df.empty:
            # Find loading violations (>100%)
            loading_violations = branches_df[branches_df['loading_percent'] > 100]
            
            scenario_data['loading_violations'] = [
                {
                    'from_bus': int(row['from_bus']),
                    'to_bus': int(row['to_bus']),
                    'loading': float(row['loading_percent']),
                    'severity': 'Critical' if row['loading_percent'] > 120 else 'High' if row['loading_percent'] > 110 else 'Medium'
                }
                for _, row in loading_violations.iterrows()
            ]
            
            scenario_data['max_loading'] = float(branches_df['loading_percent'].max())
    
    except Exception as e:
        print(f"⚠️ Loading analysis failed for {config['name']}: {e}")
    
    # Calculate overall metrics
    scenario_data['total_violations'] = len(scenario_data['voltage_violations']) + len(scenario_data['loading_violations'])
    
    # System health score (0-100)
    voltage_health = max(0, 100 - (len(scenario_data['voltage_violations']) / max(1, scenario_data['buses_analyzed']) * 100))
    loading_health = max(0, 100 - (len(scenario_data['loading_violations']) / max(1, scenario_data['branches_analyzed']) * 100))
    scenario_data['system_health'] = (voltage_health + loading_health) / 2
    
    return scenario_data

def find_worst_scenario(scenarios):
    """Find the scenario with the most violations"""
    worst_scenario = None
    max_violations = -1
    
    for scenario_key, data in scenarios.items():
        if data['total_violations'] > max_violations:
            max_violations = data['total_violations']
            worst_scenario = scenario_key
    
    return worst_scenario

def generate_targeted_corrective_actions(scenario_data):
    """Generate targeted corrective actions based on scenario analysis"""
    
    actions = []
    
    # Voltage corrective actions
    for violation in scenario_data['voltage_violations']:
        bus_num = violation['bus']
        voltage = violation['voltage']
        
        if violation['violation_type'] == 'Low':
            # Low voltage - install capacitor
            voltage_deficit = 0.95 - voltage
            capacitor_size = max(1, int(voltage_deficit * 100))  # Minimum 1 MVAR
            
            action = {
                'type': 'Voltage Support',
                'target': f"Bus {bus_num}",
                'current_state': f"{voltage:.3f} pu",
                'action': f"Install {capacitor_size} MVAR capacitor bank",
                'expected_result': f"{min(1.02, voltage + 0.05):.3f} pu",
                'priority': violation['severity'],
                'cost_estimate': capacitor_size * 50000,
                'implementation_time': '4-8 weeks',
                'effectiveness_rating': 'High' if voltage_deficit > 0.05 else 'Medium'
            }
        else:
            # High voltage - install reactor
            voltage_excess = voltage - 1.05
            reactor_size = max(1, int(voltage_excess * 100))
            
            action = {
                'type': 'Voltage Reduction',
                'target': f"Bus {bus_num}",
                'current_state': f"{voltage:.3f} pu",
                'action': f"Install {reactor_size} MVAR reactor",
                'expected_result': f"{max(0.98, voltage - 0.05):.3f} pu",
                'priority': violation['severity'],
                'cost_estimate': reactor_size * 45000,
                'implementation_time': '3-6 weeks',
                'effectiveness_rating': 'High' if voltage_excess > 0.05 else 'Medium'
            }
        
        actions.append(action)
    
    # Loading corrective actions
    for violation in scenario_data['loading_violations']:
        from_bus = violation['from_bus']
        to_bus = violation['to_bus']
        loading = violation['loading']
        
        overload = loading - 100
        
        if overload > 50:
            action_type = 'Emergency Capacity Addition'
            action_desc = f"Add parallel line {from_bus}-{to_bus}"
            cost = int(overload * 2000000)
            time = '36-52 weeks'
            effectiveness = 'Critical'
        elif overload > 20:
            action_type = 'Capacity Upgrade'
            action_desc = f"Upgrade conductor {from_bus}-{to_bus}"
            cost = int(overload * 1500000)
            time = '16-26 weeks'
            effectiveness = 'High'
        else:
            action_type = 'Load Management'
            action_desc = f"Implement load transfer from {from_bus}-{to_bus}"
            cost = int(overload * 500000)
            time = '4-8 weeks'
            effectiveness = 'Medium'
        
        action = {
            'type': action_type,
            'target': f"Line {from_bus}-{to_bus}",
            'current_state': f"{loading:.1f}% loading",
            'action': action_desc,
            'expected_result': f"{max(85, loading - overload - 15):.1f}% loading",
            'priority': violation['severity'],
            'cost_estimate': cost,
            'implementation_time': time,
            'effectiveness_rating': effectiveness
        }
        
        actions.append(action)
    
    # Sort by priority and cost-effectiveness
    priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
    actions.sort(key=lambda x: (priority_order.get(x['priority'], 4), x['cost_estimate']))
    
    return actions

def rank_scenario_effectiveness(scenarios):
    """Rank scenarios by overall effectiveness"""
    
    ranking = []
    
    for scenario_key, data in scenarios.items():
        effectiveness_score = data['system_health']
        
        ranking.append({
            'scenario': scenario_key,
            'name': data['name'],
            'health_score': effectiveness_score,
            'total_violations': data['total_violations'],
            'recommendation': get_scenario_recommendation(effectiveness_score, data['total_violations'])
        })
    
    # Sort by health score (descending) and violations (ascending)
    ranking.sort(key=lambda x: (-x['health_score'], x['total_violations']))
    
    return ranking

def get_scenario_recommendation(health_score, violations):
    """Get recommendation based on scenario performance"""
    
    if health_score >= 95 and violations == 0:
        return "Excellent - Use as target state"
    elif health_score >= 90 and violations <= 2:
        return "Good - Minor improvements needed"
    elif health_score >= 80 and violations <= 5:
        return "Acceptable - Moderate corrective actions required"
    elif health_score >= 70:
        return "Poor - Significant improvements required"
    else:
        return "Critical - Immediate corrective actions required"

def generate_effectiveness_recommendations(effectiveness_data):
    """Generate overall effectiveness recommendations"""
    
    recommendations = {
        'best_scenario': None,
        'worst_scenario': None,
        'priority_actions': [],
        'implementation_strategy': '',
        'cost_estimate': 0
    }
    
    # Find best and worst scenarios
    if effectiveness_data['effectiveness_ranking']:
        recommendations['best_scenario'] = effectiveness_data['effectiveness_ranking'][0]
        recommendations['worst_scenario'] = effectiveness_data['effectiveness_ranking'][-1]
    
    # Priority actions (top 3)
    if effectiveness_data['corrective_actions']:
        recommendations['priority_actions'] = effectiveness_data['corrective_actions'][:3]
        recommendations['cost_estimate'] = sum(action['cost_estimate'] for action in recommendations['priority_actions'])
    
    # Implementation strategy
    if recommendations['best_scenario'] and recommendations['worst_scenario']:
        best_health = recommendations['best_scenario']['health_score']
        worst_health = recommendations['worst_scenario']['health_score']
        
        if best_health - worst_health > 20:
            recommendations['implementation_strategy'] = f"Significant improvement potential. Focus on corrective actions to move from {worst_health:.1f}% to {best_health:.1f}% system health."
        elif best_health - worst_health > 10:
            recommendations['implementation_strategy'] = f"Moderate improvement potential. Targeted corrective actions can improve system health by {best_health - worst_health:.1f}%."
        else:
            recommendations['implementation_strategy'] = "Scenarios are relatively similar. Focus on preventing worst-case conditions."
    
    return recommendations

def create_effectiveness_dashboard(effectiveness_data, case_id, contingency_id):
    """Create effectiveness dashboard visualization"""
    
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=(
            "Scenario Effectiveness Ranking", "Corrective Action Priorities", "System Health Comparison",
            "Implementation Timeline", "Cost-Benefit Analysis", "Effectiveness Summary"
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "pie"}, {"type": "table"}]
        ]
    )
    
    # 1. Scenario Effectiveness Ranking
    if effectiveness_data['effectiveness_ranking']:
        scenarios = [item['name'] for item in effectiveness_data['effectiveness_ranking']]
        health_scores = [item['health_score'] for item in effectiveness_data['effectiveness_ranking']]
        colors = ['green' if h >= 95 else 'lightgreen' if h >= 90 else 'yellow' if h >= 80 else 'orange' if h >= 70 else 'red' for h in health_scores]
        
        fig.add_trace(
            go.Bar(
                x=scenarios,
                y=health_scores,
                marker_color=colors,
                name="System Health",
                hovertemplate='<b>%{x}</b><br>Health: %{y:.1f}%<extra></extra>'
            ),
            row=1, col=1
        )
    
    # 2. Corrective Action Priorities
    if effectiveness_data['corrective_actions']:
        actions = effectiveness_data['corrective_actions'][:6]  # Top 6
        action_names = [f"{a['target']}" for a in actions]
        action_costs = [a['cost_estimate'] / 1000000 for a in actions]  # Convert to millions
        priority_colors = {'Critical': 'darkred', 'High': 'red', 'Medium': 'orange', 'Low': 'yellow'}
        colors = [priority_colors.get(a['priority'], 'gray') for a in actions]
        
        fig.add_trace(
            go.Bar(
                x=action_names,
                y=action_costs,
                marker_color=colors,
                name="Action Cost",
                hovertemplate='<b>%{x}</b><br>Cost: $%{y:.1f}M<extra></extra>'
            ),
            row=1, col=2
        )
    
    # 3. System Health Comparison
    if effectiveness_data['scenarios']:
        scenario_names = []
        health_scores = []
        
        for scenario_key, data in effectiveness_data['scenarios'].items():
            scenario_names.append(scenario_key.upper())
            health_scores.append(data['system_health'])
        
        fig.add_trace(
            go.Bar(
                x=scenario_names,
                y=health_scores,
                marker_color=['red' if h < 80 else 'orange' if h < 90 else 'green' for h in health_scores],
                name="Health Score",
                hovertemplate='<b>%{x}</b><br>Health: %{y:.1f}%<extra></extra>'
            ),
            row=1, col=3
        )
    
    # 4. Implementation Timeline
    if effectiveness_data['corrective_actions']:
        actions = effectiveness_data['corrective_actions'][:5]
        cumulative_cost = np.cumsum([a['cost_estimate'] / 1000000 for a in actions])
        action_sequence = [f"Action {i+1}" for i in range(len(actions))]
        
        fig.add_trace(
            go.Scatter(
                x=action_sequence,
                y=cumulative_cost,
                mode='markers+lines',
                marker=dict(size=10, color='blue'),
                line=dict(width=3),
                name="Cumulative Cost",
                hovertemplate='<b>%{x}</b><br>Total Cost: $%{y:.1f}M<extra></extra>'
            ),
            row=2, col=1
        )
    
    # 5. Cost-Benefit Analysis
    if effectiveness_data['corrective_actions']:
        action_types = {}
        for action in effectiveness_data['corrective_actions']:
            action_type = action['type']
            action_types[action_type] = action_types.get(action_type, 0) + action['cost_estimate']
        
        fig.add_trace(
            go.Pie(
                labels=list(action_types.keys()),
                values=list(action_types.values()),
                name="Cost Distribution",
                hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.0f}<extra></extra>'
            ),
            row=2, col=2
        )
    
    # 6. Effectiveness Summary Table
    if effectiveness_data['recommendations']['priority_actions']:
        actions = effectiveness_data['recommendations']['priority_actions']
        
        table_data = [
            ['Priority', 'Target', 'Action', 'Cost ($M)', 'Timeline'],
            *[[a['priority'], a['target'], a['action'][:30] + '...', f"{a['cost_estimate']/1000000:.1f}", a['implementation_time']] 
              for a in actions]
        ]
        
        fig.add_trace(
            go.Table(
                header=dict(values=table_data[0], fill_color='lightblue', font_size=11),
                cells=dict(values=list(zip(*table_data[1:])), fill_color='white', font_size=10, height=25)
            ),
            row=2, col=3
        )
    
    # Update layout
    title_text = f"Corrective Action Effectiveness Dashboard - Case {case_id}"
    if contingency_id:
        title_text += f" vs Contingency {contingency_id}"
    
    fig.update_layout(
        title=dict(text=title_text, font_size=16),
        height=800,
        showlegend=False
    )
    
    # Update axes
    fig.update_yaxes(title_text="Health Score (%)", row=1, col=1)
    fig.update_yaxes(title_text="Cost ($M)", row=1, col=2)
    fig.update_yaxes(title_text="Health Score (%)", row=1, col=3)
    fig.update_yaxes(title_text="Cumulative Cost ($M)", row=2, col=1)
    
    return fig

def generate_effectiveness_summary(effectiveness_data, case_id, contingency_id):
    """Generate concise effectiveness summary"""
    
    summary = []
    summary.append("=" * 70)
    summary.append("CORRECTIVE ACTION EFFECTIVENESS SUMMARY")
    summary.append(f"Case {case_id}" + (f" vs Contingency {contingency_id}" if contingency_id else ""))
    summary.append("=" * 70)
    
    # Best vs Worst Scenario
    if effectiveness_data['recommendations']['best_scenario'] and effectiveness_data['recommendations']['worst_scenario']:
        best = effectiveness_data['recommendations']['best_scenario']
        worst = effectiveness_data['recommendations']['worst_scenario']
        
        summary.append(f"\n🏆 BEST PERFORMING SCENARIO:")
        summary.append(f"   {best['name']} - {best['health_score']:.1f}% health")
        summary.append(f"   {best['recommendation']}")
        
        summary.append(f"\n⚠️  WORST PERFORMING SCENARIO:")
        summary.append(f"   {worst['name']} - {worst['health_score']:.1f}% health")
        summary.append(f"   {worst['recommendation']}")
    
    # Top Priority Actions
    if effectiveness_data['recommendations']['priority_actions']:
        summary.append(f"\n🎯 TOP PRIORITY CORRECTIVE ACTIONS:")
        for i, action in enumerate(effectiveness_data['recommendations']['priority_actions'], 1):
            summary.append(f"   {i}. {action['target']} - {action['priority']} Priority")
            summary.append(f"      {action['action']}")
            summary.append(f"      Cost: ${action['cost_estimate']:,} | Timeline: {action['implementation_time']}")
    
    # Implementation Strategy
    if effectiveness_data['recommendations']['implementation_strategy']:
        summary.append(f"\n📋 IMPLEMENTATION STRATEGY:")
        summary.append(f"   {effectiveness_data['recommendations']['implementation_strategy']}")
        
        if effectiveness_data['recommendations']['cost_estimate']:
            summary.append(f"   Total Priority Investment: ${effectiveness_data['recommendations']['cost_estimate']:,}")
    
    # Quick Win Identification
    quick_wins = [action for action in effectiveness_data.get('corrective_actions', []) 
                  if 'weeks' in action.get('implementation_time', '') and 
                  int(action['implementation_time'].split('-')[0]) <= 8]
    
    if quick_wins:
        summary.append(f"\n⚡ QUICK WINS (≤8 weeks):")
        for action in quick_wins[:3]:
            summary.append(f"   • {action['target']}: {action['action']}")
    
    return "\n".join(summary)

if __name__ == "__main__":
    print("🎯 Starting Corrective Action Effectiveness Analysis...")
    
    # Analyze effectiveness for case 42 vs contingency 455
    case_id = 42
    contingency_id = 455
    
    fig, effectiveness_data = create_corrective_action_effectiveness_dashboard(case_id, contingency_id)
    
    # Generate and display summary
    summary = generate_effectiveness_summary(effectiveness_data, case_id, contingency_id)
    print(summary)
    
    # Save dashboard
    filename = f"corrective_action_effectiveness_case_{case_id}_cont_{contingency_id}.html"
    fig.write_html(filename)
    print(f"\n🎯 Effectiveness analysis complete! Dashboard saved to {filename}")