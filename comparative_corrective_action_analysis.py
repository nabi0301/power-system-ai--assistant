#!/usr/bin/env python3
"""
Comparative Corrective Action Analysis
Compares corrective actions with respective contingency cases, SLR, and DLR scenarios
Shows effectiveness of corrective actions across different operating conditions
"""

import psycopg2
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def create_comparative_corrective_action_analysis(case_id=42, contingency_id=None):
    """
    Create comparative analysis showing corrective actions effectiveness
    across base case, contingency case, SLR, and DLR scenarios
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
        
        print(f"✅ Connected to PostgreSQL for comparative analysis - Case {case_id}")
        
        # Load all data scenarios
        data_scenarios = load_all_scenarios(conn, case_id, contingency_id)
        
        # Perform comparative analysis
        comparative_results = perform_comparative_analysis(data_scenarios)
        
        # Create comprehensive comparison visualization
        fig = create_comparative_visualization(comparative_results, case_id, contingency_id)
        
        conn.close()
        return fig, comparative_results
        
    except Exception as e:
        print(f"❌ Error in comparative corrective action analysis: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Comparative Analysis Error: {str(e)}",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font_size=14
        )
        fig.update_layout(title="Comparative Corrective Action Analysis - Error", height=600)
        return fig, {}

def load_all_scenarios(conn, case_id, contingency_id):
    """Load data for all scenarios: base, contingency, SLR, DLR"""
    
    scenarios = {}
    
    # 1. Base Case Data
    base_buses_query = f"""
        SELECT bus_number, vm, va, base_kv, pg, qg, pd, qd 
        FROM base_buses 
        WHERE case_id = {case_id}
        ORDER BY bus_number
    """
    
    base_branches_query = f"""
        SELECT from_bus, to_bus, circuit_id, pf, qf, mva, rate, vio
        FROM base_branches 
        WHERE case_id = {case_id} AND rate > 0
        ORDER BY from_bus, to_bus
    """
    
    scenarios['base'] = {
        'buses': pd.read_sql_query(base_buses_query, conn),
        'branches': pd.read_sql_query(base_branches_query, conn),
        'name': f'Base Case {case_id}'
    }
    
    # 2. Contingency Case Data (if specified)
    if contingency_id:
        cont_buses_query = f"""
            SELECT bus_number, vm, va, base_kv, pg, qg, pd, qd 
            FROM contingencybusdata 
            WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            ORDER BY bus_number
        """
        
        cont_branches_query = f"""
            SELECT from_bus, to_bus, circuit_id, pf, qf, mva, rate, vio
            FROM contingencybranchdata 
            WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id} AND rate > 0
            ORDER BY from_bus, to_bus
        """
        
        scenarios['contingency'] = {
            'buses': pd.read_sql_query(cont_buses_query, conn),
            'branches': pd.read_sql_query(cont_branches_query, conn),
            'name': f'Contingency Case {contingency_id}'
        }
    
    # 3. SLR Data - find matching SLR case
    slr_cases_query = f"""
        SELECT DISTINCT slr_case_id 
        FROM slr_buses 
        ORDER BY slr_case_id 
        LIMIT 5
    """
    
    cursor = conn.cursor()
    cursor.execute(slr_cases_query)
    slr_cases = [row[0] for row in cursor.fetchall()]
    
    if slr_cases:
        # Use first available SLR case or map to case_id logic
        slr_case_id = slr_cases[min(len(slr_cases)-1, case_id // 10)] if case_id >= 42 else slr_cases[0]
        
        slr_buses_query = f"""
            SELECT bus_number, vm_pu as vm, va_degrees as va, base_kv, pg_mw as pg, qg_mvar as qg, pd_mw as pd, qd_mvar as qd 
            FROM slr_buses 
            WHERE slr_case_id = {slr_case_id}
            ORDER BY bus_number
        """
        
        slr_branches_query = f"""
            SELECT from_bus, to_bus, circuit_id, pf_mw as pf, qf_mvar as qf, mva_flow as mva, mva_rating as rate, 
                   (loading_percent - 100) as vio
            FROM slr_branches 
            WHERE slr_case_id = {slr_case_id} AND mva_rating > 0
            ORDER BY from_bus, to_bus
        """
        
        scenarios['slr'] = {
            'buses': pd.read_sql_query(slr_buses_query, conn),
            'branches': pd.read_sql_query(slr_branches_query, conn),
            'name': f'SLR Case {slr_case_id}'
        }
    
    # 4. DLR Data - find matching DLR case
    dlr_cases_query = f"""
        SELECT DISTINCT dlr_case_id 
        FROM dlr_buses 
        ORDER BY dlr_case_id 
        LIMIT 5
    """
    
    cursor.execute(dlr_cases_query)
    dlr_cases = [row[0] for row in cursor.fetchall()]
    
    if dlr_cases:
        # Use corresponding DLR case
        dlr_case_id = dlr_cases[min(len(dlr_cases)-1, case_id // 10)] if case_id >= 42 else dlr_cases[0]
        
        dlr_buses_query = f"""
            SELECT bus_number, vm_pu as vm, va_degrees as va, base_kv, pg_mw as pg, qg_mvar as qg, pd_mw as pd, qd_mvar as qd 
            FROM dlr_buses 
            WHERE dlr_case_id = {dlr_case_id}
            ORDER BY bus_number
        """
        
        dlr_branches_query = f"""
            SELECT from_bus, to_bus, circuit_id, pf_mw as pf, qf_mvar as qf, mva_flow as mva, mva_rating as rate,
                   (loading_percent - 100) as vio
            FROM dlr_branches 
            WHERE dlr_case_id = {dlr_case_id} AND mva_rating > 0
            ORDER BY from_bus, to_bus
        """
        
        scenarios['dlr'] = {
            'buses': pd.read_sql_query(dlr_buses_query, conn),
            'branches': pd.read_sql_query(dlr_branches_query, conn),
            'name': f'DLR Case {dlr_case_id}'
        }
    
    cursor.close()
    
    # Print data availability
    for scenario_name, data in scenarios.items():
        print(f"📊 {scenario_name.upper()}: {len(data['buses'])} buses, {len(data['branches'])} branches")
    
    return scenarios

def perform_comparative_analysis(scenarios):
    """Perform comparative analysis across all scenarios"""
    
    results = {
        'voltage_comparison': {},
        'loading_comparison': {},
        'violation_summary': {},
        'corrective_actions': {},
        'effectiveness_metrics': {}
    }
    
    voltage_limits = {'low': 0.95, 'high': 1.05}
    loading_limit = 100.0
    
    # Analyze each scenario
    for scenario_name, data in scenarios.items():
        buses_df = data['buses']
        branches_df = data['branches']
        
        # Voltage analysis
        if not buses_df.empty and 'vm' in buses_df.columns:
            voltage_violations = buses_df[
                (buses_df['vm'] < voltage_limits['low']) | (buses_df['vm'] > voltage_limits['high'])
            ]
            
            results['voltage_comparison'][scenario_name] = {
                'total_buses': len(buses_df),
                'violations': len(voltage_violations),
                'violation_rate': len(voltage_violations) / len(buses_df) * 100,
                'min_voltage': float(buses_df['vm'].min()),
                'max_voltage': float(buses_df['vm'].max()),
                'avg_voltage': float(buses_df['vm'].mean()),
                'violation_buses': voltage_violations['bus_number'].tolist() if len(voltage_violations) > 0 else []
            }
        
        # Loading analysis
        if not branches_df.empty and 'mva' in branches_df.columns and 'rate' in branches_df.columns:
            branches_df = branches_df.copy()
            branches_df['loading_percent'] = (branches_df['mva'] / branches_df['rate']) * 100
            loading_violations = branches_df[branches_df['loading_percent'] > loading_limit]
            
            results['loading_comparison'][scenario_name] = {
                'total_branches': len(branches_df),
                'violations': len(loading_violations),
                'violation_rate': len(loading_violations) / len(branches_df) * 100,
                'max_loading': float(branches_df['loading_percent'].max()) if len(branches_df) > 0 else 0,
                'avg_loading': float(branches_df['loading_percent'].mean()) if len(branches_df) > 0 else 0,
                'violation_branches': [(int(row['from_bus']), int(row['to_bus'])) 
                                     for _, row in loading_violations.iterrows()] if len(loading_violations) > 0 else []
            }
    
    # Generate corrective actions based on base case
    if 'base' in scenarios:
        results['corrective_actions'] = generate_comparative_corrective_actions(
            scenarios['base']['buses'], scenarios['base']['branches']
        )
    
    # Calculate effectiveness metrics
    results['effectiveness_metrics'] = calculate_effectiveness_metrics(results, scenarios)
    
    # Create violation summary
    results['violation_summary'] = create_violation_summary(results)
    
    return results

def generate_comparative_corrective_actions(base_buses, base_branches):
    """Generate corrective actions with effectiveness predictions"""
    
    actions = []
    
    # Voltage corrective actions
    voltage_violations = base_buses[
        (base_buses['vm'] < 0.95) | (base_buses['vm'] > 1.05)
    ]
    
    for _, bus in voltage_violations.iterrows():
        bus_num = int(bus['bus_number'])
        voltage = float(bus['vm'])
        
        if voltage < 0.95:
            voltage_deficit = 0.95 - voltage
            capacitor_size = int(voltage_deficit * 100)  # MVAR
            
            action = {
                'type': 'Voltage Support',
                'location': f'Bus {bus_num}',
                'current_voltage': voltage,
                'target_voltage': 0.98,
                'action': f'Install {capacitor_size} MVAR capacitor bank',
                'expected_improvement': voltage_deficit + 0.03,
                'priority': 'High' if voltage_deficit > 0.05 else 'Medium',
                'cost_estimate': capacitor_size * 50000,
                'implementation_weeks': 8 if capacitor_size > 10 else 4
            }
            
        else:  # High voltage
            voltage_excess = voltage - 1.05
            reactor_size = int(voltage_excess * 100)  # MVAR
            
            action = {
                'type': 'Voltage Reduction',
                'location': f'Bus {bus_num}',
                'current_voltage': voltage,
                'target_voltage': 1.02,
                'action': f'Install {reactor_size} MVAR reactor',
                'expected_improvement': -(voltage_excess + 0.03),
                'priority': 'High' if voltage_excess > 0.05 else 'Medium',
                'cost_estimate': reactor_size * 45000,
                'implementation_weeks': 6 if reactor_size > 10 else 3
            }
        
        actions.append(action)
    
    # Loading corrective actions
    if not base_branches.empty:
        base_branches_copy = base_branches.copy()
        base_branches_copy['loading_percent'] = (base_branches_copy['mva'] / base_branches_copy['rate']) * 100
        loading_violations = base_branches_copy[base_branches_copy['loading_percent'] > 100]
        
        for _, branch in loading_violations.iterrows():
            from_bus = int(branch['from_bus'])
            to_bus = int(branch['to_bus'])
            loading = float(branch['loading_percent'])
            overload = loading - 100
            
            if overload > 50:
                action_type = 'Emergency Line Addition'
                action_desc = f'Add parallel transmission line {from_bus}-{to_bus}'
                cost = int(overload * 2000000)
                weeks = 52
            elif overload > 20:
                action_type = 'Capacity Upgrade'
                action_desc = f'Upgrade conductor capacity {from_bus}-{to_bus}'
                cost = int(overload * 1500000)
                weeks = 26
            else:
                action_type = 'Load Management'
                action_desc = f'Implement load transfer from {from_bus}-{to_bus}'
                cost = int(overload * 500000)
                weeks = 8
            
            action = {
                'type': action_type,
                'location': f'Line {from_bus}-{to_bus}',
                'current_loading': loading,
                'target_loading': 85.0,
                'action': action_desc,
                'expected_improvement': -(overload + 15),
                'priority': 'Critical' if overload > 50 else 'High' if overload > 20 else 'Medium',
                'cost_estimate': cost,
                'implementation_weeks': weeks
            }
            
            actions.append(action)
    
    return actions

def calculate_effectiveness_metrics(results, scenarios):
    """Calculate effectiveness metrics comparing scenarios"""
    
    metrics = {}
    
    if 'base' in results['voltage_comparison']:
        base_voltage = results['voltage_comparison']['base']
        
        # Compare with other scenarios
        for scenario in ['contingency', 'slr', 'dlr']:
            if scenario in results['voltage_comparison']:
                scenario_voltage = results['voltage_comparison'][scenario]
                
                metrics[f'{scenario}_vs_base'] = {
                    'voltage_improvement': scenario_voltage['violation_rate'] - base_voltage['violation_rate'],
                    'loading_improvement': (results['loading_comparison'].get(scenario, {}).get('violation_rate', 0) - 
                                          results['loading_comparison'].get('base', {}).get('violation_rate', 0)),
                    'overall_improvement': calculate_overall_improvement(base_voltage, scenario_voltage)
                }
    
    return metrics

def calculate_overall_improvement(base_data, scenario_data):
    """Calculate overall system improvement percentage"""
    
    base_score = 100 - (base_data['violation_rate'] * 2)  # Simple scoring
    scenario_score = 100 - (scenario_data['violation_rate'] * 2)
    
    return scenario_score - base_score

def create_violation_summary(results):
    """Create summary of violations across all scenarios"""
    
    summary = {
        'worst_case': None,
        'best_case': None,
        'improvement_ranking': []
    }
    
    # Find worst and best cases
    violation_rates = {}
    for scenario in results['voltage_comparison']:
        total_rate = (results['voltage_comparison'][scenario]['violation_rate'] + 
                     results['loading_comparison'].get(scenario, {}).get('violation_rate', 0))
        violation_rates[scenario] = total_rate
    
    if violation_rates:
        summary['worst_case'] = max(violation_rates, key=violation_rates.get)
        summary['best_case'] = min(violation_rates, key=violation_rates.get)
        summary['improvement_ranking'] = sorted(violation_rates.items(), key=lambda x: x[1])
    
    return summary

def create_comparative_visualization(results, case_id, contingency_id):
    """Create comprehensive comparative visualization"""
    
    fig = make_subplots(
        rows=3, cols=3,
        subplot_titles=(
            "Voltage Violations Comparison", "Loading Violations Comparison", "Corrective Actions Timeline",
            "Scenario Effectiveness", "Cost-Benefit Analysis", "Implementation Priority",
            "Before/After Voltage Profile", "System Health Comparison", "Improvement Metrics"
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "pie"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "bar"}, {"type": "table"}]
        ]
    )
    
    # 1. Voltage Violations Comparison
    scenarios = list(results['voltage_comparison'].keys())
    voltage_violations = [results['voltage_comparison'][s]['violations'] for s in scenarios]
    colors = ['red', 'orange', 'blue', 'green'][:len(scenarios)]
    
    fig.add_trace(
        go.Bar(
            x=scenarios,
            y=voltage_violations,
            marker_color=colors,
            name="Voltage Violations",
            hovertemplate='<b>%{x}</b><br>Violations: %{y}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # 2. Loading Violations Comparison
    loading_violations = [results['loading_comparison'].get(s, {}).get('violations', 0) for s in scenarios]
    
    fig.add_trace(
        go.Bar(
            x=scenarios,
            y=loading_violations,
            marker_color=colors,
            name="Loading Violations",
            hovertemplate='<b>%{x}</b><br>Violations: %{y}<extra></extra>'
        ),
        row=1, col=2
    )
    
    # 3. Corrective Actions Timeline
    if results.get('corrective_actions'):
        actions = results['corrective_actions'][:6]  # Top 6 actions
        action_labels = [a['location'] for a in actions]
        implementation_weeks = [a['implementation_weeks'] for a in actions]
        priority_colors = {'Critical': 'darkred', 'High': 'red', 'Medium': 'orange', 'Low': 'yellow'}
        action_colors = [priority_colors.get(a['priority'], 'gray') for a in actions]
        
        fig.add_trace(
            go.Bar(
                x=action_labels,
                y=implementation_weeks,
                marker_color=action_colors,
                name="Implementation Timeline",
                hovertemplate='<b>%{x}</b><br>Weeks: %{y}<extra></extra>'
            ),
            row=1, col=3
        )
    
    # 4. Scenario Effectiveness
    if results.get('effectiveness_metrics'):
        effectiveness_scenarios = []
        effectiveness_values = []
        
        for metric_name, metric_data in results['effectiveness_metrics'].items():
            if 'overall_improvement' in metric_data:
                effectiveness_scenarios.append(metric_name.replace('_vs_base', '').upper())
                effectiveness_values.append(metric_data['overall_improvement'])
        
        if effectiveness_scenarios:
            fig.add_trace(
                go.Scatter(
                    x=effectiveness_scenarios,
                    y=effectiveness_values,
                    mode='markers+lines',
                    marker=dict(size=12, color='purple'),
                    name="Effectiveness",
                    hovertemplate='<b>%{x}</b><br>Improvement: %{y:.1f}%<extra></extra>'
                ),
                row=2, col=1
            )
    
    # 5. Cost-Benefit Analysis
    if results.get('corrective_actions'):
        action_types = {}
        for action in results['corrective_actions']:
            action_type = action['type']
            action_types[action_type] = action_types.get(action_type, 0) + action['cost_estimate']
        
        if action_types:
            fig.add_trace(
                go.Pie(
                    labels=list(action_types.keys()),
                    values=list(action_types.values()),
                    name="Cost Distribution",
                    hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.0f}<extra></extra>'
                ),
                row=2, col=2
            )
    
    # 6. Implementation Priority
    if results.get('corrective_actions'):
        priority_counts = {}
        for action in results['corrective_actions']:
            priority = action['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        if priority_counts:
            fig.add_trace(
                go.Bar(
                    x=list(priority_counts.keys()),
                    y=list(priority_counts.values()),
                    marker_color=['darkred', 'red', 'orange', 'yellow'][:len(priority_counts)],
                    name="Priority Distribution",
                    hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
                ),
                row=2, col=3
            )
    
    # 7. Before/After Voltage Profile (if SLR/DLR available)
    if 'base' in results['voltage_comparison'] and ('slr' in results['voltage_comparison'] or 'dlr' in results['voltage_comparison']):
        # Use SLR or DLR as "after" scenario
        after_scenario = 'slr' if 'slr' in results['voltage_comparison'] else 'dlr'
        
        base_avg = results['voltage_comparison']['base']['avg_voltage']
        after_avg = results['voltage_comparison'][after_scenario]['avg_voltage']
        
        fig.add_trace(
            go.Scatter(
                x=['Before (Base)', f'After ({after_scenario.upper()})'],
                y=[base_avg, after_avg],
                mode='markers+lines',
                marker=dict(size=15, color=['red', 'green']),
                line=dict(width=3),
                name="Voltage Improvement",
                hovertemplate='<b>%{x}</b><br>Avg Voltage: %{y:.3f} pu<extra></extra>'
            ),
            row=3, col=1
        )
    
    # 8. System Health Comparison
    health_scores = {}
    for scenario in scenarios:
        voltage_health = 100 - (results['voltage_comparison'][scenario]['violation_rate'] * 2)
        loading_health = 100 - (results['loading_comparison'].get(scenario, {}).get('violation_rate', 0) * 2)
        overall_health = (voltage_health + loading_health) / 2
        health_scores[scenario] = overall_health
    
    fig.add_trace(
        go.Bar(
            x=list(health_scores.keys()),
            y=list(health_scores.values()),
            marker_color=['red' if h < 80 else 'orange' if h < 90 else 'green' for h in health_scores.values()],
            name="System Health",
            hovertemplate='<b>%{x}</b><br>Health: %{y:.1f}%<extra></extra>'
        ),
        row=3, col=2
    )
    
    # 9. Improvement Metrics Table
    if results.get('corrective_actions'):
        top_actions = results['corrective_actions'][:5]
        
        table_data = [
            ['Action', 'Location', 'Priority', 'Cost ($M)', 'Timeline (weeks)'],
            *[[a['type'][:15], a['location'], a['priority'], f"{a['cost_estimate']/1000000:.1f}", a['implementation_weeks']] 
              for a in top_actions]
        ]
        
        fig.add_trace(
            go.Table(
                header=dict(values=table_data[0], fill_color='lightblue', font_size=10),
                cells=dict(values=list(zip(*table_data[1:])), fill_color='white', font_size=9, height=20)
            ),
            row=3, col=3
        )
    
    # Update layout
    title_text = f"Comparative Corrective Action Analysis - Case {case_id}"
    if contingency_id:
        title_text += f" vs Contingency {contingency_id}"
    title_text += " with SLR/DLR Comparison"
    
    fig.update_layout(
        title=dict(text=title_text, font_size=16),
        height=1200,
        showlegend=False
    )
    
    # Update axis labels
    fig.update_xaxes(title_text="Scenarios", row=1, col=1)
    fig.update_yaxes(title_text="Violation Count", row=1, col=1)
    
    fig.update_xaxes(title_text="Scenarios", row=1, col=2)
    fig.update_yaxes(title_text="Violation Count", row=1, col=2)
    
    fig.update_xaxes(title_text="Actions", row=1, col=3)
    fig.update_yaxes(title_text="Weeks", row=1, col=3)
    
    fig.update_xaxes(title_text="Scenarios", row=2, col=1)
    fig.update_yaxes(title_text="Improvement (%)", row=2, col=1)
    
    fig.update_xaxes(title_text="Priority Level", row=2, col=3)
    fig.update_yaxes(title_text="Action Count", row=2, col=3)
    
    fig.update_xaxes(title_text="Comparison", row=3, col=1)
    fig.update_yaxes(title_text="Voltage (pu)", row=3, col=1)
    
    fig.update_xaxes(title_text="Scenarios", row=3, col=2)
    fig.update_yaxes(title_text="Health Score (%)", row=3, col=2)
    
    return fig

def generate_comparative_report(results, case_id, contingency_id):
    """Generate detailed comparative analysis report"""
    
    report = []
    report.append("=" * 80)
    report.append(f"COMPARATIVE CORRECTIVE ACTION ANALYSIS REPORT")
    report.append(f"Case {case_id}" + (f" vs Contingency {contingency_id}" if contingency_id else ""))
    report.append("=" * 80)
    
    # Scenario Comparison
    report.append("\n📊 SCENARIO COMPARISON:")
    report.append("-" * 40)
    
    for scenario, data in results['voltage_comparison'].items():
        report.append(f"\n{scenario.upper()}:")
        report.append(f"  • Voltage Violations: {data['violations']} ({data['violation_rate']:.1f}%)")
        if scenario in results['loading_comparison']:
            loading_data = results['loading_comparison'][scenario]
            report.append(f"  • Loading Violations: {loading_data['violations']} ({loading_data['violation_rate']:.1f}%)")
        report.append(f"  • Avg Voltage: {data['avg_voltage']:.3f} pu")
    
    # Effectiveness Analysis
    if results.get('effectiveness_metrics'):
        report.append("\n🎯 EFFECTIVENESS ANALYSIS:")
        report.append("-" * 40)
        
        for metric_name, metric_data in results['effectiveness_metrics'].items():
            scenario = metric_name.replace('_vs_base', '').upper()
            report.append(f"\n{scenario} vs BASE CASE:")
            report.append(f"  • Voltage Improvement: {metric_data['voltage_improvement']:.1f}%")
            report.append(f"  • Loading Improvement: {metric_data['loading_improvement']:.1f}%")
            report.append(f"  • Overall Improvement: {metric_data['overall_improvement']:.1f}%")
    
    # Top Corrective Actions
    if results.get('corrective_actions'):
        report.append("\n🔧 TOP CORRECTIVE ACTIONS:")
        report.append("-" * 40)
        
        for i, action in enumerate(results['corrective_actions'][:5], 1):
            report.append(f"\n{i}. {action['location']} - {action['priority']} Priority")
            report.append(f"   Action: {action['action']}")
            report.append(f"   Cost: ${action['cost_estimate']:,}")
            report.append(f"   Timeline: {action['implementation_weeks']} weeks")
    
    # Best Case Recommendation
    if results.get('violation_summary'):
        summary = results['violation_summary']
        if summary.get('best_case'):
            report.append(f"\n✅ RECOMMENDATION:")
            report.append("-" * 40)
            report.append(f"Best performing scenario: {summary['best_case'].upper()}")
            report.append("Consider implementing corrective actions based on this scenario's characteristics.")
    
    return "\n".join(report)

if __name__ == "__main__":
    print("🔍 Starting Comparative Corrective Action Analysis...")
    
    # Test with case 42 and contingency case
    case_id = 42
    contingency_id = 455  # Example contingency case
    
    fig, results = create_comparative_corrective_action_analysis(case_id, contingency_id)
    
    # Generate and display report
    report = generate_comparative_report(results, case_id, contingency_id)
    print(report)
    
    # Save visualization
    filename = f"comparative_corrective_analysis_case_{case_id}_cont_{contingency_id}.html"
    fig.write_html(filename)
    print(f"📊 Comparative analysis complete! Results saved to {filename}")