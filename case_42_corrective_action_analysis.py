#!/usr/bin/env python3
"""
Corrective Action Analysis for Case 42 using PostgreSQL Database
Analyzes power system violations and generates corrective action recommendations
"""

import psycopg2
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def analyze_case_42_corrective_actions():
    """Comprehensive corrective action analysis for case 42"""
    
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            host='localhost',
            port='5432', 
            database='118',
            user='postgres',
            password='pnnl'
        )
        
        print("✅ Connected to PostgreSQL database for Case 42 analysis")
        
        # Load base case 42 data
        base_buses_query = """
            SELECT bus_number, vm, va, base_kv, pg, qg, pd, qd 
            FROM base_buses 
            WHERE case_id = 42
            ORDER BY bus_number
        """
        
        base_branches_query = """
            SELECT from_bus, to_bus, circuit_id, pf, qf, mva, rate, vio
            FROM base_branches 
            WHERE case_id = 42
            ORDER BY from_bus, to_bus
        """
        
        # Load contingency data for case 42
        contingency_buses_query = """
            SELECT DISTINCT contingency_case_id, bus_number, vm, va, base_kv, pg, qg, pd, qd 
            FROM contingencybusdata 
            WHERE base_case_id = 42
            ORDER BY contingency_case_id, bus_number
        """
        
        contingency_branches_query = """
            SELECT DISTINCT contingency_case_id, from_bus, to_bus, circuit_id, pf, qf, mva, rate, vio
            FROM contingencybranchdata 
            WHERE base_case_id = 42
            ORDER BY contingency_case_id, from_bus, to_bus
        """
        
        # Load data into DataFrames
        base_buses = pd.read_sql_query(base_buses_query, conn)
        base_branches = pd.read_sql_query(base_branches_query, conn)
        contingency_buses = pd.read_sql_query(contingency_buses_query, conn)
        contingency_branches = pd.read_sql_query(contingency_branches_query, conn)
        
        print(f"📊 Data loaded: {len(base_buses)} base buses, {len(base_branches)} base branches")
        print(f"📊 Contingency data: {len(contingency_buses)} contingency buses, {len(contingency_branches)} contingency branches")
        
        # Analyze violations and generate corrective actions
        analysis_results = perform_corrective_action_analysis(
            base_buses, base_branches, contingency_buses, contingency_branches
        )
        
        # Create comprehensive visualization
        fig = create_corrective_action_visualization(analysis_results)
        
        conn.close()
        return fig, analysis_results
        
    except Exception as e:
        print(f"❌ Error in corrective action analysis: {e}")
        # Return empty figure if error
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error in corrective action analysis: {e}",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
        fig.update_layout(title="Corrective Action Analysis - Error", height=600)
        return fig, {}

def perform_corrective_action_analysis(base_buses, base_branches, contingency_buses, contingency_branches):
    """Perform detailed corrective action analysis"""
    
    results = {
        'voltage_violations': [],
        'loading_violations': [],
        'corrective_actions': [],
        'contingency_analysis': {},
        'priority_actions': []
    }
    
    # 1. Voltage Violation Analysis
    voltage_low_limit = 0.95
    voltage_high_limit = 1.05
    
    # Base case voltage violations
    base_voltage_violations = base_buses[
        (base_buses['vm'] < voltage_low_limit) | (base_buses['vm'] > voltage_high_limit)
    ]
    
    for _, bus in base_voltage_violations.iterrows():
        violation_type = "Low" if bus['vm'] < voltage_low_limit else "High"
        severity = abs(bus['vm'] - 1.0)
        
        # Generate corrective action
        if violation_type == "Low":
            action = f"Install capacitor bank or reduce load at Bus {bus['bus_number']}"
            if bus['qg'] < 0:
                action += f" | Increase reactive power generation (currently {bus['qg']:.1f} MVAR)"
        else:
            action = f"Install reactor or increase load at Bus {bus['bus_number']}"
            if bus['qg'] > 0:
                action += f" | Reduce reactive power generation (currently {bus['qg']:.1f} MVAR)"
        
        results['voltage_violations'].append({
            'bus': bus['bus_number'],
            'voltage': bus['vm'],
            'type': violation_type,
            'severity': severity,
            'action': action,
            'priority': 'High' if severity > 0.1 else 'Medium'
        })
    
    # 2. Loading Violation Analysis
    loading_limit = 100.0  # 100% loading
    
    # Base case loading violations
    base_branches['loading_percent'] = (base_branches['mva'] / base_branches['rate']) * 100
    loading_violations = base_branches[base_branches['loading_percent'] > loading_limit]
    
    for _, branch in loading_violations.iterrows():
        severity = branch['loading_percent'] - 100.0
        
        # Generate corrective action based on severity
        if severity > 50:
            action = f"Emergency: Add parallel line between Bus {branch['from_bus']}-{branch['to_bus']}"
            priority = 'Critical'
        elif severity > 20:
            action = f"Urgent: Increase conductor capacity or add transformer Bus {branch['from_bus']}-{branch['to_bus']}"
            priority = 'High'
        else:
            action = f"Monitor: Consider load transfer from Bus {branch['from_bus']}-{branch['to_bus']}"
            priority = 'Medium'
        
        results['loading_violations'].append({
            'from_bus': branch['from_bus'],
            'to_bus': branch['to_bus'],
            'circuit': branch['circuit_id'],
            'loading': branch['loading_percent'],
            'severity': severity,
            'action': action,
            'priority': priority
        })
    
    # 3. Contingency Analysis
    if not contingency_buses.empty:
        contingency_cases = contingency_buses['contingency_case_id'].unique()
        
        for case_id in contingency_cases[:5]:  # Analyze top 5 contingencies
            case_buses = contingency_buses[contingency_buses['contingency_case_id'] == case_id]
            case_branches = contingency_branches[contingency_branches['contingency_case_id'] == case_id]
            
            # Check for post-contingency violations
            voltage_violations = len(case_buses[
                (case_buses['vm'] < voltage_low_limit) | (case_buses['vm'] > voltage_high_limit)
            ])
            
            case_branches['loading_percent'] = (case_branches['mva'] / case_branches['rate']) * 100
            loading_violations_count = len(case_branches[case_branches['loading_percent'] > loading_limit])
            
            results['contingency_analysis'][case_id] = {
                'voltage_violations': voltage_violations,
                'loading_violations': loading_violations_count,
                'severity': 'High' if (voltage_violations > 5 or loading_violations_count > 3) else 'Medium'
            }
    
    # 4. Priority Corrective Actions
    all_actions = results['voltage_violations'] + results['loading_violations']
    
    # Sort by priority and severity
    priority_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
    sorted_actions = sorted(all_actions, 
                           key=lambda x: (priority_order.get(x['priority'], 0), x['severity']), 
                           reverse=True)
    
    results['priority_actions'] = sorted_actions[:10]  # Top 10 priority actions
    
    return results

def create_corrective_action_visualization(results):
    """Create comprehensive corrective action visualization"""
    
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "Voltage Violations by Bus", "Loading Violations by Branch",
            "Corrective Action Priorities", "Contingency Analysis Summary",
            "Action Type Distribution", "System Health Assessment"
        ),
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "pie"}, {"type": "indicator"}]
        ]
    )
    
    # 1. Voltage Violations Plot
    if results.get('voltage_violations'):
        voltage_data = results['voltage_violations']
        bus_numbers = [v['bus'] for v in voltage_data]
        voltages = [v['voltage'] for v in voltage_data]
        colors = ['red' if v['type'] == 'Low' else 'orange' for v in voltage_data]
        
        fig.add_trace(
            go.Scatter(
                x=bus_numbers,
                y=voltages,
                mode='markers',
                marker=dict(color=colors, size=10),
                name="Voltage Violations",
                hovertemplate='<b>Bus %{x}</b><br>Voltage: %{y:.3f} pu<br>Action Required<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add voltage limits
        fig.add_hline(y=0.95, line_dash="dash", line_color="red", row=1, col=1)
        fig.add_hline(y=1.05, line_dash="dash", line_color="red", row=1, col=1)
    
    # 2. Loading Violations Plot
    if results.get('loading_violations'):
        loading_data = results['loading_violations']
        branch_labels = [f"{l['from_bus']}-{l['to_bus']}" for l in loading_data]
        loadings = [l['loading'] for l in loading_data]
        colors = ['darkred' if l['priority'] == 'Critical' else 'red' if l['priority'] == 'High' else 'orange' 
                 for l in loading_data]
        
        fig.add_trace(
            go.Scatter(
                x=range(len(branch_labels)),
                y=loadings,
                mode='markers',
                marker=dict(color=colors, size=12),
                name="Loading Violations",
                text=branch_labels,
                hovertemplate='<b>%{text}</b><br>Loading: %{y:.1f}%<br>Overloaded<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Add 100% loading limit
        fig.add_hline(y=100, line_dash="dash", line_color="red", row=1, col=2)
    
    # 3. Corrective Action Priorities
    if results.get('priority_actions'):
        priority_counts = {}
        for action in results['priority_actions']:
            priority = action['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        fig.add_trace(
            go.Bar(
                x=list(priority_counts.keys()),
                y=list(priority_counts.values()),
                marker_color=['darkred', 'red', 'orange', 'yellow'][:len(priority_counts)],
                name="Action Priorities"
            ),
            row=2, col=1
        )
    
    # 4. Contingency Analysis
    if results.get('contingency_analysis'):
        cont_data = results['contingency_analysis']
        case_ids = list(cont_data.keys())
        total_violations = [cont_data[case]['voltage_violations'] + cont_data[case]['loading_violations'] 
                           for case in case_ids]
        
        fig.add_trace(
            go.Bar(
                x=[f"Case {case}" for case in case_ids],
                y=total_violations,
                marker_color='purple',
                name="Contingency Violations"
            ),
            row=2, col=2
        )
    
    # 5. Action Type Distribution
    action_types = {'Voltage': 0, 'Loading': 0}
    if results.get('voltage_violations'):
        action_types['Voltage'] = len(results['voltage_violations'])
    if results.get('loading_violations'):
        action_types['Loading'] = len(results['loading_violations'])
    
    if sum(action_types.values()) > 0:
        fig.add_trace(
            go.Pie(
                labels=list(action_types.keys()),
                values=list(action_types.values()),
                name="Action Types"
            ),
            row=3, col=1
        )
    
    # 6. System Health Assessment
    total_violations = sum(action_types.values())
    health_score = max(0, 100 - (total_violations * 5))  # Simple health scoring
    
    health_color = "green" if health_score > 80 else "orange" if health_score > 60 else "red"
    health_status = "GOOD" if health_score > 80 else "CAUTION" if health_score > 60 else "CRITICAL"
    
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"System Health<br>{health_status}"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': health_color},
                'steps': [
                    {'range': [0, 60], 'color': "lightgray"},
                    {'range': [60, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=3, col=2
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Case 42 Corrective Action Analysis - PostgreSQL Database",
            font_size=16
        ),
        height=1000,
        showlegend=False
    )
    
    # Update axis labels
    fig.update_xaxes(title_text="Bus Number", row=1, col=1)
    fig.update_yaxes(title_text="Voltage (pu)", row=1, col=1)
    
    fig.update_xaxes(title_text="Branch Index", row=1, col=2)
    fig.update_yaxes(title_text="Loading (%)", row=1, col=2)
    
    fig.update_xaxes(title_text="Priority Level", row=2, col=1)
    fig.update_yaxes(title_text="Number of Actions", row=2, col=1)
    
    fig.update_xaxes(title_text="Contingency Case", row=2, col=2)
    fig.update_yaxes(title_text="Total Violations", row=2, col=2)
    
    return fig

def generate_corrective_action_report(results):
    """Generate a detailed corrective action report"""
    
    report = []
    report.append("=" * 60)
    report.append("CASE 42 CORRECTIVE ACTION ANALYSIS REPORT")
    report.append("=" * 60)
    
    # Voltage Violations Section
    if results.get('voltage_violations'):
        report.append("\n🔴 VOLTAGE VIOLATIONS:")
        report.append("-" * 30)
        for i, violation in enumerate(results['voltage_violations'][:5], 1):
            report.append(f"{i}. Bus {violation['bus']}: {violation['voltage']:.3f} pu ({violation['type']} voltage)")
            report.append(f"   Action: {violation['action']}")
            report.append(f"   Priority: {violation['priority']}")
            report.append("")
    
    # Loading Violations Section
    if results.get('loading_violations'):
        report.append("\n⚡ LOADING VIOLATIONS:")
        report.append("-" * 30)
        for i, violation in enumerate(results['loading_violations'][:5], 1):
            report.append(f"{i}. Branch {violation['from_bus']}-{violation['to_bus']}: {violation['loading']:.1f}%")
            report.append(f"   Action: {violation['action']}")
            report.append(f"   Priority: {violation['priority']}")
            report.append("")
    
    # Priority Actions
    if results.get('priority_actions'):
        report.append("\n🎯 TOP PRIORITY ACTIONS:")
        report.append("-" * 30)
        for i, action in enumerate(results['priority_actions'][:3], 1):
            if 'bus' in action:
                location = f"Bus {action['bus']}"
            else:
                location = f"Branch {action['from_bus']}-{action['to_bus']}"
            report.append(f"{i}. {location} - {action['priority']} Priority")
            report.append(f"   {action['action']}")
            report.append("")
    
    return "\n".join(report)

if __name__ == "__main__":
    print("🔍 Starting Case 42 Corrective Action Analysis...")
    
    fig, results = analyze_case_42_corrective_actions()
    
    # Generate and display report
    report = generate_corrective_action_report(results)
    print(report)
    
    # Save figure
    fig.write_html("case_42_corrective_action_analysis.html")
    print("📊 Analysis complete! Results saved to case_42_corrective_action_analysis.html")