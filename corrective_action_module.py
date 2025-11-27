#!/usr/bin/env python3
"""
Case 42 Corrective Action Analysis Integration Module
For integration with the main power visualization system
"""

import psycopg2
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def create_case_42_corrective_action_analysis():
    """
    Create corrective action analysis specifically for Case 42 using PostgreSQL
    Returns a Plotly figure for integration with the main system
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
        
        # Load Case 42 data
        base_buses_query = """
            SELECT bus_number, vm, va, base_kv, pg, qg, pd, qd 
            FROM base_buses 
            WHERE case_id = 42
            ORDER BY bus_number
        """
        
        base_branches_query = """
            SELECT from_bus, to_bus, circuit_id, pf, qf, mva, rate, vio
            FROM base_branches 
            WHERE case_id = 42 AND rate > 0
            ORDER BY from_bus, to_bus
        """
        
        base_buses = pd.read_sql_query(base_buses_query, conn)
        base_branches = pd.read_sql_query(base_branches_query, conn)
        
        conn.close()
        
        # Perform analysis
        analysis_results = analyze_violations_and_actions(base_buses, base_branches)
        
        # Create visualization
        fig = create_integrated_corrective_action_plot(analysis_results, base_buses, base_branches)
        
        return fig
        
    except Exception as e:
        print(f"❌ Error in Case 42 corrective action analysis: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Corrective Action Analysis Error: {str(e)}",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font_size=14
        )
        fig.update_layout(title="Case 42 Corrective Action Analysis - Error", height=600)
        return fig

def analyze_violations_and_actions(base_buses, base_branches):
    """Analyze violations and generate corrective actions"""
    
    results = {
        'voltage_violations': [],
        'loading_violations': [],
        'system_health': {},
        'priority_actions': []
    }
    
    # Voltage analysis
    voltage_low = 0.95
    voltage_high = 1.05
    
    for _, bus in base_buses.iterrows():
        if bus['vm'] < voltage_low:
            severity = abs(bus['vm'] - voltage_low)
            action = f"Install {int(severity * 100)} MVAR capacitor bank at Bus {int(bus['bus_number'])}"
            if bus['qg'] < 0:
                action += f" | Increase reactive power by {abs(bus['qg']):.1f} MVAR"
            
            results['voltage_violations'].append({
                'bus': int(bus['bus_number']),
                'voltage': float(bus['vm']),
                'type': 'Low',
                'severity': float(severity),
                'action': action,
                'priority': 'High' if severity > 0.05 else 'Medium',
                'cost_estimate': int(severity * 500000)  # Rough cost estimate
            })
        
        elif bus['vm'] > voltage_high:
            severity = abs(bus['vm'] - voltage_high)
            action = f"Install {int(severity * 100)} MVAR reactor at Bus {int(bus['bus_number'])}"
            if bus['qg'] > 0:
                action += f" | Reduce reactive power by {bus['qg']:.1f} MVAR"
            
            results['voltage_violations'].append({
                'bus': int(bus['bus_number']),
                'voltage': float(bus['vm']),
                'type': 'High',
                'severity': float(severity),
                'action': action,
                'priority': 'High' if severity > 0.05 else 'Medium',
                'cost_estimate': int(severity * 400000)
            })
    
    # Loading analysis
    base_branches = base_branches.copy()
    base_branches['loading_percent'] = (base_branches['mva'] / base_branches['rate']) * 100
    
    overloaded = base_branches[base_branches['loading_percent'] > 100]
    
    for _, branch in overloaded.iterrows():
        severity = float(branch['loading_percent'] - 100)
        from_bus = int(branch['from_bus'])
        to_bus = int(branch['to_bus'])
        
        if severity > 50:
            action = f"Emergency: Add parallel transmission line {from_bus}-{to_bus}"
            priority = 'Critical'
            cost = int(severity * 1000000)
        elif severity > 20:
            action = f"Upgrade conductor capacity {from_bus}-{to_bus} by {severity:.0f}%"
            priority = 'High'
            cost = int(severity * 750000)
        else:
            action = f"Load transfer or upgrade transformers {from_bus}-{to_bus}"
            priority = 'Medium'
            cost = int(severity * 500000)
        
        results['loading_violations'].append({
            'from_bus': from_bus,
            'to_bus': to_bus,
            'circuit': int(branch['circuit_id']),
            'loading': float(branch['loading_percent']),
            'severity': severity,
            'action': action,
            'priority': priority,
            'cost_estimate': cost
        })
    
    # System health assessment
    total_violations = len(results['voltage_violations']) + len(results['loading_violations'])
    total_buses = len(base_buses)
    total_branches = len(base_branches)
    
    voltage_health = (1 - len(results['voltage_violations']) / total_buses) * 100
    loading_health = (1 - len(results['loading_violations']) / total_branches) * 100
    overall_health = (voltage_health + loading_health) / 2
    
    results['system_health'] = {
        'voltage_health': voltage_health,
        'loading_health': loading_health,
        'overall_health': overall_health,
        'total_violations': total_violations,
        'status': 'GOOD' if overall_health > 90 else 'CAUTION' if overall_health > 75 else 'CRITICAL'
    }
    
    # Priority actions (combined and sorted)
    all_actions = []
    
    for v in results['voltage_violations']:
        all_actions.append({
            'type': 'Voltage',
            'location': f"Bus {v['bus']}",
            'priority': v['priority'],
            'severity': v['severity'],
            'action': v['action'],
            'cost': v['cost_estimate']
        })
    
    for l in results['loading_violations']:
        all_actions.append({
            'type': 'Loading',
            'location': f"Line {l['from_bus']}-{l['to_bus']}",
            'priority': l['priority'],
            'severity': l['severity'],
            'action': l['action'],
            'cost': l['cost_estimate']
        })
    
    # Sort by priority and severity
    priority_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
    all_actions.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['severity']), reverse=True)
    
    results['priority_actions'] = all_actions[:8]  # Top 8 actions
    
    return results

def create_integrated_corrective_action_plot(results, base_buses, base_branches):
    """Create integrated corrective action visualization"""
    
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=(
            "Voltage Violations Map", "Loading Analysis", "Priority Actions",
            "Cost Analysis", "System Health Metrics", "Implementation Timeline"
        ),
        specs=[
            [{"type": "scatter"}, {"type": "bar"}, {"type": "bar"}],
            [{"type": "pie"}, {"type": "indicator"}, {"type": "bar"}]
        ]
    )
    
    # 1. Voltage Violations Map
    if results['voltage_violations']:
        v_data = results['voltage_violations']
        bus_nums = [v['bus'] for v in v_data]
        voltages = [v['voltage'] for v in v_data]
        colors = ['red' if v['type'] == 'Low' else 'orange' for v in v_data]
        severities = [v['severity'] * 1000 for v in v_data]  # Scale for marker size
        
        fig.add_trace(
            go.Scatter(
                x=bus_nums,
                y=voltages,
                mode='markers',
                marker=dict(color=colors, size=severities, sizemin=8),
                name="Voltage Violations",
                hovertemplate='<b>Bus %{x}</b><br>Voltage: %{y:.3f} pu<br>Violation Detected<extra></extra>'
            ),
            row=1, col=1
        )
        
        fig.add_hline(y=0.95, line_dash="dash", line_color="red", row=1, col=1)
        fig.add_hline(y=1.05, line_dash="dash", line_color="red", row=1, col=1)
    
    # Add normal voltage buses for context
    normal_buses = base_buses[(base_buses['vm'] >= 0.95) & (base_buses['vm'] <= 1.05)]
    fig.add_trace(
        go.Scatter(
            x=normal_buses['bus_number'],
            y=normal_buses['vm'],
            mode='markers',
            marker=dict(color='green', size=4, opacity=0.6),
            name="Normal Voltages",
            hovertemplate='<b>Bus %{x}</b><br>Voltage: %{y:.3f} pu<br>Normal Operation<extra></extra>'
        ),
        row=1, col=1
    )
    
    # 2. Loading Analysis
    if results['loading_violations']:
        l_data = results['loading_violations']
        branch_labels = [f"{l['from_bus']}-{l['to_bus']}" for l in l_data]
        loadings = [l['loading'] for l in l_data]
        colors = ['darkred' if l['priority'] == 'Critical' else 'red' if l['priority'] == 'High' else 'orange' 
                 for l in l_data]
        
        fig.add_trace(
            go.Bar(
                x=branch_labels,
                y=loadings,
                marker_color=colors,
                name="Overloaded Lines",
                hovertemplate='<b>%{x}</b><br>Loading: %{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )
        
        fig.add_hline(y=100, line_dash="dash", line_color="red", row=1, col=2)
    
    # 3. Priority Actions
    if results['priority_actions']:
        actions = results['priority_actions'][:6]  # Top 6 for visibility
        action_labels = [f"{a['type'][:4]}-{a['location']}" for a in actions]
        severities = [a['severity'] for a in actions]
        colors = ['darkred' if a['priority'] == 'Critical' else 'red' if a['priority'] == 'High' else 'orange' 
                 for a in actions]
        
        fig.add_trace(
            go.Bar(
                x=action_labels,
                y=severities,
                marker_color=colors,
                name="Priority Actions",
                hovertemplate='<b>%{x}</b><br>Severity: %{y:.2f}<br>Priority Action<extra></extra>'
            ),
            row=1, col=3
        )
    
    # 4. Cost Analysis
    if results['priority_actions']:
        cost_by_type = {'Voltage': 0, 'Loading': 0}
        for action in results['priority_actions']:
            cost_by_type[action['type']] += action['cost']
        
        fig.add_trace(
            go.Pie(
                labels=list(cost_by_type.keys()),
                values=list(cost_by_type.values()),
                name="Cost Distribution",
                hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.0f}<extra></extra>'
            ),
            row=2, col=1
        )
    
    # 5. System Health Indicator
    health_score = results['system_health']['overall_health']
    health_status = results['system_health']['status']
    health_color = "green" if health_score > 90 else "orange" if health_score > 75 else "red"
    
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
                    {'range': [0, 75], 'color': "lightgray"},
                    {'range': [75, 90], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=2, col=2
    )
    
    # 6. Implementation Timeline (Priority-based)
    if results['priority_actions']:
        timeline_actions = results['priority_actions'][:5]
        timeline_weeks = []
        for i, action in enumerate(timeline_actions):
            if action['priority'] == 'Critical':
                weeks = 2 + i
            elif action['priority'] == 'High':
                weeks = 8 + i * 2
            else:
                weeks = 16 + i * 4
            timeline_weeks.append(weeks)
        
        action_names = [f"{a['type'][:4]}-{a['location']}" for a in timeline_actions]
        colors = ['darkred' if a['priority'] == 'Critical' else 'red' if a['priority'] == 'High' else 'orange' 
                 for a in timeline_actions]
        
        fig.add_trace(
            go.Bar(
                x=action_names,
                y=timeline_weeks,
                marker_color=colors,
                name="Implementation Timeline",
                hovertemplate='<b>%{x}</b><br>Timeline: %{y} weeks<extra></extra>'
            ),
            row=2, col=3
        )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Case 42 Corrective Action Analysis - PostgreSQL Database",
            font_size=16
        ),
        height=800,
        showlegend=False
    )
    
    # Update axis labels
    fig.update_xaxes(title_text="Bus Number", row=1, col=1)
    fig.update_yaxes(title_text="Voltage (pu)", row=1, col=1)
    
    fig.update_xaxes(title_text="Transmission Lines", row=1, col=2)
    fig.update_yaxes(title_text="Loading (%)", row=1, col=2)
    
    fig.update_xaxes(title_text="Actions", row=1, col=3)
    fig.update_yaxes(title_text="Severity Index", row=1, col=3)
    
    fig.update_xaxes(title_text="Actions", row=2, col=3)
    fig.update_yaxes(title_text="Implementation (Weeks)", row=2, col=3)
    
    return fig

if __name__ == "__main__":
    # Test the function
    fig = create_case_42_corrective_action_analysis()
    fig.write_html("case_42_integrated_analysis.html")
    print("✅ Case 42 corrective action analysis created successfully!")