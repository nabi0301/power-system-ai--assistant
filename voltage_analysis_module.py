#!/usr/bin/env python3
"""
Voltage Analysis Module
Contains the create_voltage_analysis_plot function for comprehensive voltage analysis
"""

import pandas as pd
import sqlite3
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_voltage_analysis_plot(buses_df=None, case_id=None, contingency_id=None):
    """Creates comprehensive voltage analysis visualization with multiple perspectives"""
    if buses_df is None or buses_df.empty:
        # Try to load data from database
        try:
            conn = sqlite3.connect('data.db')
            if case_id is not None:
                if contingency_id is not None:
                    query = f"SELECT * FROM ContingencyBusData WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}"
                else:
                    query = f"SELECT * FROM BaseBusData WHERE base_case_id = {case_id}"
            else:
                query = "SELECT * FROM BaseBusData WHERE base_case_id = 42 LIMIT 1000"
            
            buses_df = pd.read_sql_query(query, conn)
            conn.close()
        except Exception as e:
            print(f"Error loading bus data: {e}")
            buses_df = pd.DataFrame()
    
    if buses_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No bus voltage data available for analysis", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font_size=16)
        fig.update_layout(title="Voltage Analysis - No Data Available", height=600)
        return fig
    
    # Create voltage analysis subplots
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=("Voltage Magnitude Distribution", "Voltage Profile by Bus", "Voltage Level Classification",
                      "Voltage Violations", "Voltage Statistics", "System Health Overview"),
        specs=[[{"type": "xy"}, {"type": "xy"}, {"type": "xy"}],
               [{"type": "xy"}, {"type": "table"}, {"type": "indicator"}]]
    )
    
    # Prepare voltage data
    voltage_col = 'VM' if 'VM' in buses_df.columns else 'voltage_magnitude' if 'voltage_magnitude' in buses_df.columns else None
    voltage_level_col = 'BASE_KV' if 'BASE_KV' in buses_df.columns else 'voltage_level' if 'voltage_level' in buses_df.columns else None
    bus_num_col = 'BUS_NUMBER' if 'BUS_NUMBER' in buses_df.columns else 'bus_number' if 'bus_number' in buses_df.columns else None
    
    if voltage_col is None:
        fig.add_annotation(text="No voltage magnitude data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Voltage Analysis - Insufficient Data", height=600)
        return fig
    
    voltages = buses_df[voltage_col].dropna()
    
    # 1. Voltage Magnitude Distribution (Histogram)
    fig.add_trace(
        go.Histogram(
            x=voltages,
            nbinsx=30,
            name="Voltage Distribution",
            marker_color='lightblue',
            opacity=0.7
        ),
        row=1, col=1
    )
    
    # Add voltage limit lines
    fig.add_vline(x=0.95, line_dash="dash", line_color="red", annotation_text="Lower Limit (0.95 pu)", row=1, col=1)
    fig.add_vline(x=1.05, line_dash="dash", line_color="red", annotation_text="Upper Limit (1.05 pu)", row=1, col=1)
    
    # 2. Voltage Profile by Bus Number
    if bus_num_col is not None:
        bus_numbers = buses_df[bus_num_col]
        colors = ['red' if v < 0.95 or v > 1.05 else 'green' for v in voltages]
        
        fig.add_trace(
            go.Scatter(
                x=bus_numbers,
                y=voltages,
                mode='markers',
                name="Bus Voltages",
                marker=dict(color=colors, size=6),
                hovertemplate='<b>Bus %{x}</b><br>Voltage: %{y:.3f} pu<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Add voltage limit lines
        fig.add_hline(y=0.95, line_dash="dash", line_color="red", row=1, col=2)
        fig.add_hline(y=1.05, line_dash="dash", line_color="red", row=1, col=2)
    
    # 3. Voltage Level Classification
    if voltage_level_col is not None:
        voltage_levels = buses_df[voltage_level_col].dropna()
        level_counts = voltage_levels.value_counts().sort_index()
        
        # Color code by voltage level
        colors = []
        for level in level_counts.index:
            if level >= 345:
                colors.append('#ff6b6b')  # Red for EHV
            elif level >= 138:
                colors.append('#4ecdc4')  # Teal for HV
            elif level >= 69:
                colors.append('#45b7d1')  # Blue for MV
            else:
                colors.append('#96ceb4')  # Green for LV
        
        fig.add_trace(
            go.Bar(
                x=[f"{level} kV" for level in level_counts.index],
                y=level_counts.values,
                name="Voltage Levels",
                marker_color=colors,
                hovertemplate='<b>%{x}</b><br>Bus Count: %{y}<extra></extra>'
            ),
            row=1, col=3
        )
    
    # 4. Voltage Violations Analysis
    violations_low = voltages[voltages < 0.95]
    violations_high = voltages[voltages > 1.05]
    normal_voltages = voltages[(voltages >= 0.95) & (voltages <= 1.05)]
    
    fig.add_trace(
        go.Bar(
            x=['Normal<br>(0.95-1.05 pu)', 'Low Voltage<br>(<0.95 pu)', 'High Voltage<br>(>1.05 pu)'],
            y=[len(normal_voltages), len(violations_low), len(violations_high)],
            marker_color=['green', 'orange', 'red'],
            name="Voltage Categories",
            hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # 5. Voltage Statistics Table
    stats_data = [
        ['Total Buses', len(voltages)],
        ['Min Voltage', f"{voltages.min():.4f} pu"],
        ['Max Voltage', f"{voltages.max():.4f} pu"],
        ['Mean Voltage', f"{voltages.mean():.4f} pu"],
        ['Std Deviation', f"{voltages.std():.4f} pu"],
        ['Low Violations', len(violations_low)],
        ['High Violations', len(violations_high)],
        ['Violation Rate', f"{((len(violations_low) + len(violations_high)) / len(voltages) * 100):.2f}%"]
    ]
    
    fig.add_trace(
        go.Table(
            header=dict(values=['Metric', 'Value'], fill_color='lightblue', font_size=12),
            cells=dict(values=list(zip(*stats_data)), fill_color='white', font_size=11, height=25)
        ),
        row=2, col=2
    )
    
    # 6. System Health Indicator
    total_violations = len(violations_low) + len(violations_high)
    violation_percentage = (total_violations / len(voltages)) * 100
    
    # Determine health status
    if violation_percentage == 0:
        health_color = "green"
        health_status = "EXCELLENT"
    elif violation_percentage < 5:
        health_color = "lightgreen"
        health_status = "GOOD"
    elif violation_percentage < 15:
        health_color = "orange"
        health_status = "CAUTION"
    else:
        health_color = "red"
        health_status = "CRITICAL"
    
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=100 - violation_percentage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"System Health<br>{health_status}"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': health_color},
                'steps': [
                    {'range': [0, 85], 'color': "lightgray"},
                    {'range': [85, 95], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=2, col=3
    )
    
    # Update layout
    title = "Comprehensive Voltage Analysis"
    if case_id is not None:
        title += f" - Case {case_id}"
    if contingency_id is not None:
        title += f" (Contingency {contingency_id})"
    
    fig.update_layout(
        title=dict(text=title, font_size=16),
        height=800,
        showlegend=False,
        font_size=10
    )
    
    # Update subplot axes
    fig.update_xaxes(title_text="Voltage Magnitude (pu)", row=1, col=1)
    fig.update_yaxes(title_text="Frequency", row=1, col=1)
    
    if bus_num_col is not None:
        fig.update_xaxes(title_text="Bus Number", row=1, col=2)
        fig.update_yaxes(title_text="Voltage (pu)", row=1, col=2)
    
    if voltage_level_col is not None:
        fig.update_xaxes(title_text="Voltage Level", row=1, col=3)
        fig.update_yaxes(title_text="Number of Buses", row=1, col=3)
    
    fig.update_xaxes(title_text="Voltage Category", row=2, col=1)
    fig.update_yaxes(title_text="Number of Buses", row=2, col=1)
    
    return fig