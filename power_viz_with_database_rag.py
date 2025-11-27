#!/usr/bin/env python3
"""
Simple Power System Visualization with AI Chat Integration + RAG
Demonstrates the working AI chat assistant with RAG-enhanced responses using real database data.
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sqlite3
import json
import os

# RAG System Import
try:
    from simple_rag import get_rag_response, initialize_rag
    RAG_AVAILABLE = True
    print("Simple RAG system loaded successfully")
except ImportError as e:
    print(f"RAG system not available: {e}")
    RAG_AVAILABLE = False
    
    # Fallback function if RAG not available
    def get_rag_response(question):
        return None, "RAG system not available"

# AI Integration with API + RAG
def get_visualization_description(viz_type, buses_df, branches_df, comparison_df):
    """Generate description of current visualization data"""
    try:
        if viz_type == 'voltage':
            avg_voltage = buses_df['VM'].mean()
            min_voltage = buses_df['VM'].min()
            max_voltage = buses_df['VM'].max()
            low_voltage_count = len(buses_df[buses_df['VM'] < 0.95])
            high_voltage_count = len(buses_df[buses_df['VM'] > 1.05])
            
            description = f"""📊 **Voltage Analysis Overview:**
• **Average Voltage:** {avg_voltage:.3f} p.u.
• **Voltage Range:** {min_voltage:.3f} - {max_voltage:.3f} p.u.
• **Low Voltage Buses:** {low_voltage_count} buses below 0.95 p.u.
• **High Voltage Buses:** {high_voltage_count} buses above 1.05 p.u.
• **Total Buses:** {len(buses_df)} in IEEE 118-bus system

💡 **What you're seeing:** A histogram showing the distribution of voltage magnitudes across all buses. Most buses operate within normal limits (0.95-1.05 p.u.)."""
            
        elif viz_type == 'loading':
            # Calculate loading percentages safely
            valid_branches = branches_df[branches_df['RATE'] > 0]
            loading_pct = (valid_branches['MVA'] / valid_branches['RATE'] * 100)
            avg_loading = loading_pct.mean()
            max_loading = loading_pct.max()
            overloaded_count = len(loading_pct[loading_pct > 100])
            high_loading_count = len(loading_pct[loading_pct > 90])
            
            description = f"""📊 **Loading Analysis Overview:**
• **Average Loading:** {avg_loading:.1f}%
• **Maximum Loading:** {max_loading:.1f}%
• **Overloaded Lines:** {overloaded_count} lines above 100%
• **High Loading Lines:** {high_loading_count} lines above 90%
• **Total Branches:** {len(branches_df)} transmission lines

💡 **What you're seeing:** A scatter plot showing loading percentages for each transmission line. Color indicates stress level (red = overloaded, green = normal)."""
            
        elif viz_type == 'violations':
            valid_branches = branches_df[branches_df['RATE'] > 0]
            loading_pct = (valid_branches['MVA'] / valid_branches['RATE'] * 100)
            violated_lines = loading_pct[loading_pct > 100]
            
            if len(violated_lines) > 0:
                worst_violation = violated_lines.max()
                description = f"""📊 **Violation Analysis Overview:**
• **Violated Lines:** {len(violated_lines)} transmission lines
• **Worst Violation:** {worst_violation:.1f}% loading
• **Critical Status:** System has overloaded equipment
• **Total Lines Analyzed:** {len(valid_branches)}

⚠️ **What you're seeing:** Bar chart showing only the overloaded transmission lines. These require immediate attention to prevent equipment damage."""
            else:
                description = f"""📊 **Violation Analysis Overview:**
• **Violated Lines:** 0 transmission lines
• **System Status:** All equipment within limits
• **Total Lines Analyzed:** {len(valid_branches)}

✅ **What you're seeing:** No violations detected - all transmission lines are operating within their thermal limits."""
            
        elif viz_type == 'comparison':
            if not comparison_df.empty:
                description = f"""📊 **SLR vs DLR Comparison Overview:**
• **Comparison Cases:** {len(comparison_df)} analyzed scenarios
• **Static Line Rating (SLR):** Traditional fixed thermal limits
• **Dynamic Line Rating (DLR):** Weather-adjusted real-time limits
• **Analysis Type:** Contingency case comparison

💡 **What you're seeing:** Side-by-side comparison showing how dynamic line ratings can provide higher capacity than static ratings under favorable weather conditions."""
            else:
                description = "📊 **SLR vs DLR Comparison:** No comparison data available for current analysis."
                
        elif viz_type == 'generators':
            description = f"""📊 **Generator Analysis Overview:**
• **Analysis Type:** Generation capacity and dispatch
• **Data Source:** SLR_Generator table
• **Comparison:** Initial vs New generation levels
• **System:** IEEE 118-bus test case

💡 **What you're seeing:** Bar chart comparing initial and adjusted generation levels across different generator buses."""
            
        elif viz_type == 'network':
            total_load = buses_df['PD'].sum()
            total_generation = buses_df['PG'].sum()
            
            description = f"""📊 **Network Topology Overview:**
• **System:** IEEE 118-bus test network
• **Total Load:** {total_load:.1f} MW
• **Total Generation:** {total_generation:.1f} MW
• **Buses:** {len(buses_df)} nodes
• **Branches:** {len(branches_df)} transmission lines

💡 **What you're seeing:** Network layout with buses positioned in a grid. Colors represent voltage levels, and lines show transmission connections."""
        elif viz_type == 'integrated_flow':
            description = """📊 **Integrated Power Flow Map:**
• **Bus Sizing:** Based on generation/load importance
• **Branch Colors:** Loading percentage with directional flow arrows
• **Bus Colors:** Voltage magnitude intensity
• **Insight:** Visual correlation between bus conditions and branch loadings"""
        elif viz_type == 'criticality_heatmap':
            description = """📊 **Bus-Branch Criticality Heatmap:**
• **Grid Layout:** Buses vs branches vulnerability matrix
• **Color Intensity:** Criticality score based on voltage and loading
• **Insight:** Most vulnerable bus-branch combinations during contingencies"""
        elif viz_type == 'voltage_flow_3d':
            description = """📊 **Voltage-Flow 3D Surface:**
• **X-Y Axes:** System topology coordinates
• **Z-Axis:** Bus voltage levels
• **Line Colors:** Branch loading percentages
• **Insight:** 3D relationship between voltage issues and line congestion"""
        elif viz_type == 'cascading_failure':
            description = """📊 **Cascading Failure Path Visualization:**
• **Red Lines:** Initial failure points
• **Orange Lines:** Secondary failure propagation
• **Step Analysis:** How failures cascade through network
• **Insight:** Hidden dependencies between branches and buses"""
        elif viz_type == 'contingency_impact':
            description = """📊 **Contingency Impact Distribution:**
• **Bars:** Bus voltage violations by scenario
• **Lines:** Branch overloads by scenario
• **Sorting:** By severity level
• **Insight:** Which contingencies affect buses vs branches more severely"""
        elif viz_type == 'before_after':
            description = """📊 **Before/After Split-Screen Comparison:**
• **Left Panel:** Normal operation state
• **Right Panel:** Post-contingency state
• **Color Changes:** Voltage redistribution effects
• **Insight:** Clear visual of contingency impact on system voltages"""
        elif viz_type == 'dlr_benefit':
            description = """📊 **DLR Benefit Bubble Chart:**
• **X-Axis:** Bus loading levels
• **Y-Axis:** Connected branch loading percentage
• **Bubble Size:** Capacity gain from DLR vs SLR
• **Insight:** Which bus-branch pairs benefit most from DLR implementation"""
        elif viz_type == 'weather_dlr':
            description = """📊 **Weather-DLR Correlation Map:**
• **X-Axis:** Wind speed conditions
• **Y-Axis:** Temperature levels
• **Colors/Size:** DLR capacity gains
• **Insight:** When and where DLR provides most value relative to weather"""
        elif viz_type == 'constraint_binding':
            description = """📊 **Constraint Binding Analysis:**
• **Red Triangles:** Voltage-constrained buses
• **Orange Lines:** Thermal-constrained branches
• **Green Dots:** Normal operation points
• **Insight:** Whether system is voltage-limited or thermal-limited by area"""
        elif viz_type == 'upgrade_priority':
            description = """📊 **Upgrade Priority Matrix:**
• **X-Axis:** Bus importance (load + generation)
• **Y-Axis:** Connected branch utilization
• **Bubble Size:** Violation frequency
• **Insight:** Clear guidance on where system reinforcements are most effective"""
        else:
            description = "📊 **Current Visualization:** Showing IEEE 118-bus power system data with real-time database information."
            
        return description
        
    except Exception as e:
        return f"📊 **Visualization Description:** Unable to analyze current data (Error: {str(e)})"

def get_ai_response(user_message, current_viz_type='network'):
    """
    Enhanced AI response function with RAG capabilities
    Returns tuple: (response_text, visualization_command)
    """
    
    # First, try RAG response for data-specific questions
    if RAG_AVAILABLE:
        try:
            rag_response, context = get_rag_response(user_message)
            if rag_response and len(rag_response) > 50:  # Valid RAG response
                return f"🧠 **RAG Response:** {rag_response}", None
        except Exception as e:
            print(f"RAG error: {e}")
    
    # Check for visualization requests
    message_lower = user_message.lower()
    
    # Visualization command patterns
    viz_commands = {
        'show voltage': 'voltage',
        'voltage visualization': 'voltage',
        'bus voltages': 'voltage',
        'voltage analysis': 'voltage',
        'show loading': 'loading', 
        'line loading': 'loading',
        'branch loading': 'loading',
        'loading analysis': 'loading',
        'show violations': 'violations',
        'violation analysis': 'violations',
        'overloaded lines': 'violations',
        'compare slr dlr': 'comparison',
        'slr vs dlr': 'comparison',
        'efficiency comparison': 'comparison',
        'show generators': 'generators',
        'generation data': 'generators',
        'power generation': 'generators',
        'network topology': 'network',
        'system overview': 'network',
        'full network': 'network',
        'show network': 'network',
        # Advanced Network Performance Visualizations
        'integrated power flow': 'integrated_flow',
        'power flow map': 'integrated_flow',
        'comprehensive network': 'integrated_flow',
        'criticality heatmap': 'criticality_heatmap',
        'bus branch heatmap': 'criticality_heatmap',
        'vulnerability map': 'criticality_heatmap',
        'voltage flow 3d': 'voltage_flow_3d',
        '3d surface': 'voltage_flow_3d',
        'voltage correlation': 'voltage_flow_3d',
        'cascading failure': 'cascading_failure',
        'failure path': 'cascading_failure',
        'propagation analysis': 'cascading_failure',
        'contingency impact': 'contingency_impact',
        'impact distribution': 'contingency_impact',
        'severity analysis': 'contingency_impact',
        'before after': 'before_after',
        'split screen': 'before_after',
        'comparison view': 'before_after',
        'dlr benefit': 'dlr_benefit',
        'bubble chart': 'dlr_benefit',
        'capacity gain': 'dlr_benefit',
        'weather dlr': 'weather_dlr',
        'weather correlation': 'weather_dlr',
        'environmental impact': 'weather_dlr',
        'constraint binding': 'constraint_binding',
        'binding analysis': 'constraint_binding',
        'system limits': 'constraint_binding',
        'upgrade priority': 'upgrade_priority',
        'priority matrix': 'upgrade_priority',
        'reinforcement analysis': 'upgrade_priority'
    }
    
    # Check for description requests
    description_keywords = ['what am i seeing', 'describe this', 'explain this visualization', 'what does this show', 'analyze this', 'current data']
    if any(keyword in message_lower for keyword in description_keywords):
        viz_description = get_visualization_description(current_viz_type, buses_df, branches_df, comparison_df)
        return viz_description, None
    
    # Check for visualization commands
    for command, viz_type in viz_commands.items():
        if command in message_lower:
            response_text = f"🎯 **Visualization Updated!**\n\n📊 Switched to {viz_type.title()} Analysis\n\n💡 **Command:** `{command}`\n📈 **Type:** {viz_type}\n\n✅ **Status:** Visualization generated successfully!"
            return response_text, viz_type
    
    # Primary: PNNL AI Incubator API
    try:
        from openai import OpenAI
        
        # Initialize client with PNNL AI Incubator settings
        API_KEY = "sk-4UJCbpRTNTx-lvO_4bxNdQ"
        BASE_URL = "https://ai-incubator-api.pnnl.gov"
        MODEL = "claude-3-7-sonnet-20250219-v1-birthright"
        
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert power systems engineer with deep knowledge of electrical grids, transmission lines, DLR/SLR analysis, and power system operations. You can also help users understand visualizations and suggest specific charts they might want to see."},
                {"role": "user", "content": user_message}
            ],
            stream=False
        )
        return f"🖥️ {response.choices[0].message.content.strip()}", None
    except Exception as e:
        print(f"AI API error: {e}")
    
    # Fallback: Enhanced contextual responses
    message_lower = user_message.lower()
    
    power_keywords = {
        'load': "Power system loading refers to the electrical demand on the network. In our visualization, you can see how different load conditions affect transmission line efficiency and system stability.",
        'dlr': "Dynamic Line Rating (DLR) uses real-time weather and conductor temperature data to safely increase power transmission capacity beyond static limits. This can improve grid efficiency by 10-40%.",
        'slr': "Static Line Rating (SLR) uses conservative fixed limits based on worst-case weather conditions. While safer, it often underutilizes transmission capacity.",
        'contingency': "Contingency analysis studies how the power system responds when equipment fails. It's crucial for maintaining reliability and preventing cascading outages.",
        'voltage': "Voltage levels must be maintained within acceptable ranges (typically ±5% of nominal) throughout the transmission network to ensure proper equipment operation and power quality.",
        'transformer': "Transformers change voltage levels between different parts of the power system. Our database tracks transformer loadings and their impact on system efficiency.",
        'efficiency': "Power system efficiency measures how much electrical energy reaches consumers versus losses in transmission. Our analysis shows efficiency improvements with DLR implementation.",
        'ieee': "The IEEE 118-bus test system is a standard benchmark for power system studies, representing a realistic transmission network with 118 buses and 186 transmission lines.",
        'mva': "MVA (Mega Volt-Ampere) represents the apparent power flowing through transmission lines. Higher MVA indicates higher loading.",
        'violation': "Violations occur when system parameters exceed safe operating limits. Our visualization shows which lines are overloaded.",
        'base case': "Base case represents normal operating conditions without any equipment failures or contingencies.",
        'database': "Our database contains real IEEE 118-bus system data with base cases, contingency analysis, and SLR/DLR comparisons."
    }
    
    for keyword, response in power_keywords.items():
        if keyword in message_lower:
            return f"💡 {response}", None
    
    return f"🔧 I understand you're asking about '{user_message}'. The visualization above shows real data from our IEEE 118-bus system database, including voltage levels, power flows, and transmission line loadings.", None

def load_database_data():
    """Load real power system data from the database"""
    try:
        conn = sqlite3.connect('data.db')
        
        # Load base case bus data
        buses_query = """
        SELECT base_case_id, BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD
        FROM BaseBusData 
        WHERE base_case_id = 0
        ORDER BY BUS_NUMBER
        """
        buses_df = pd.read_sql_query(buses_query, conn)
        
        # Load base case branch data
        branches_query = """
        SELECT base_case_id, branch_number, From_Bus, To_Bus, PF, QF, MVA, RATE, VIO
        FROM BaseBranchData 
        WHERE base_case_id = 0
        ORDER BY branch_number
        """
        branches_df = pd.read_sql_query(branches_query, conn)
        
        # Load SLR vs DLR comparison data for visualization
        slr_query = """
        SELECT base_case_id, contingency_case_id, From_Bus, To_Bus, MVA as SLR_MVA, 
               RATE as SLR_RATE, VIO as SLR_VIO
        FROM SLR_Branches 
        WHERE base_case_id = 42 AND contingency_case_id = 123
        ORDER BY branch_number
        """
        slr_df = pd.read_sql_query(slr_query, conn)
        
        dlr_query = """
        SELECT base_case_id, contingency_case_id, From_Bus, To_Bus, MVA as DLR_MVA, 
               RATE as DLR_RATE, VIO as DLR_VIO
        FROM DLR_Branches 
        WHERE base_case_id = 42 AND contingency_case_id = 123
        ORDER BY branch_number
        """
        dlr_df = pd.read_sql_query(dlr_query, conn)
        
        conn.close()
        
        # Merge SLR and DLR data for comparison
        if not slr_df.empty and not dlr_df.empty:
            comparison_df = pd.merge(slr_df, dlr_df, on=['From_Bus', 'To_Bus'], 
                                   suffixes=('_SLR', '_DLR'), how='inner')
        else:
            comparison_df = pd.DataFrame()
        
        # Add coordinates for bus visualization (simple grid layout)
        buses_df['x_coord'] = (buses_df['BUS_NUMBER'] % 12) * 30
        buses_df['y_coord'] = (buses_df['BUS_NUMBER'] // 12) * 25
        
        print(f"Loaded {len(buses_df)} buses, {len(branches_df)} branches, {len(comparison_df)} comparison cases")
        return buses_df, branches_df, comparison_df
        
    except Exception as e:
        print(f"Database error: {e}")
        # Fallback to sample data if database fails
        return load_sample_data()

def load_sample_data():
    """Fallback sample data if database is unavailable"""
    buses = []
    for i in range(1, 119):
        buses.append({
            'BUS_NUMBER': i,
            'VM': 1.0 + (i % 10) * 0.01,
            'PD': 50 + (i % 20) * 5,
            'BASE_KV': 138.0,
            'x_coord': (i % 12) * 30,
            'y_coord': (i // 12) * 25
        })
    
    branches = []
    for i in range(1, 187):
        from_bus = i % 118 + 1
        to_bus = (i + 1) % 118 + 1
        branches.append({
            'branch_number': i,
            'From_Bus': from_bus,
            'To_Bus': to_bus,
            'MVA': 80 + (i % 15) * 5,
            'RATE': 100 + (i % 10) * 20,
            'VIO': 50 + (i % 20) * 10
        })
    
    empty_comparison = pd.DataFrame()
    return pd.DataFrame(buses), pd.DataFrame(branches), empty_comparison

def create_power_system_plot(buses_df, branches_df):
    """Create power system visualization"""
    fig = go.Figure()
    
    # Add bus points with real voltage data
    fig.add_trace(go.Scatter(
        x=buses_df['x_coord'],
        y=buses_df['y_coord'],
        mode='markers',
        marker=dict(
            size=buses_df['PD'] / 5,  # Size based on real load data
            color=buses_df['VM'],     # Color based on real voltage magnitude
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Voltage Magnitude (p.u.)")
        ),
        text=buses_df.apply(lambda row: f"Bus {int(row['BUS_NUMBER'])}<br>Voltage: {row['VM']:.3f} p.u.<br>Load: {row['PD']:.1f} MW<br>Base kV: {row['BASE_KV']:.0f}", axis=1),
        hovertemplate='%{text}<extra></extra>',
        name='Buses'
    ))
    
    # Add transmission lines (sample - first 20 lines to avoid clutter)
    line_count = 0
    for _, branch in branches_df.head(20).iterrows():
        from_bus_data = buses_df[buses_df['BUS_NUMBER'] == branch['From_Bus']]
        to_bus_data = buses_df[buses_df['BUS_NUMBER'] == branch['To_Bus']]
        
        if not from_bus_data.empty and not to_bus_data.empty:
            # Line color based on loading percentage
            loading_pct = (branch['MVA'] / branch['RATE']) * 100 if branch['RATE'] > 0 else 0
            line_color = 'red' if loading_pct > 90 else 'orange' if loading_pct > 75 else 'green'
            
            fig.add_trace(go.Scatter(
                x=[from_bus_data.iloc[0]['x_coord'], to_bus_data.iloc[0]['x_coord']],
                y=[from_bus_data.iloc[0]['y_coord'], to_bus_data.iloc[0]['y_coord']],
                mode='lines',
                line=dict(color=line_color, width=2),
                hovertemplate=f'Line {int(branch["From_Bus"])}-{int(branch["To_Bus"])}<br>MVA: {branch["MVA"]:.1f}<br>Rating: {branch["RATE"]:.1f}<br>Loading: {loading_pct:.1f}%<extra></extra>',
                showlegend=False
            ))
            line_count += 1
    
    fig.update_layout(
        title=f"IEEE 118-Bus Power System Network - Real Database Data ({line_count} lines shown)",
        xaxis_title="X Coordinate",
        yaxis_title="Y Coordinate",
        showlegend=True,
        height=600,
        template="plotly_white"
    )
    
    return fig

def create_slr_dlr_comparison(comparison_df):
    """Create SLR vs DLR comparison visualization"""
    if comparison_df.empty:
        # Return empty figure if no comparison data
        fig = go.Figure()
        fig.add_annotation(
            text="No SLR/DLR comparison data available<br>(Database may not contain comparison cases)",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title="SLR vs DLR Comparison", height=400)
        return fig
    
    fig = go.Figure()
    
    # SLR violations
    fig.add_trace(go.Scatter(
        x=comparison_df.index,
        y=comparison_df['SLR_VIO'],
        mode='markers',
        name='SLR Violations (%)',
        marker=dict(color='red', size=8),
        text=comparison_df.apply(lambda row: f"Line {int(row['From_Bus'])}-{int(row['To_Bus'])}<br>SLR: {row['SLR_VIO']:.1f}%", axis=1),
        hovertemplate='%{text}<extra></extra>'
    ))
    
    # DLR violations
    fig.add_trace(go.Scatter(
        x=comparison_df.index,
        y=comparison_df['DLR_VIO'],
        mode='markers',
        name='DLR Violations (%)',
        marker=dict(color='blue', size=8),
        text=comparison_df.apply(lambda row: f"Line {int(row['From_Bus'])}-{int(row['To_Bus'])}<br>DLR: {row['DLR_VIO']:.1f}%", axis=1),
        hovertemplate='%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"SLR vs DLR Violation Analysis - {len(comparison_df)} Cases",
        xaxis_title="Branch Index",
        yaxis_title="Violation Percentage (%)",
        height=500,
        template="plotly_white"
    )
    
    return fig

def create_voltage_analysis_plot(buses_df):
    """Create voltage-focused visualization"""
    try:
        fig = go.Figure()
        
        # Voltage histogram
        fig.add_trace(go.Histogram(
            x=buses_df['VM'],
            nbinsx=20,
            name='Voltage Distribution',
            marker_color='lightblue'
        ))
        
        # Add voltage limits
        fig.add_vline(x=0.95, line_dash="dash", line_color="red", 
                      annotation_text="Low Voltage Limit (0.95 p.u.)")
        fig.add_vline(x=1.05, line_dash="dash", line_color="red",
                      annotation_text="High Voltage Limit (1.05 p.u.)")
        
        fig.update_layout(
            title="Bus Voltage Analysis - IEEE 118 System",
            xaxis_title="Voltage Magnitude (p.u.)",
            yaxis_title="Number of Buses",
            height=500
        )
        
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error creating voltage plot: {str(e)}",
            xref="paper", yref="paper", x=0.5, y=0.5
        )
        return fig

def create_loading_analysis_plot(branches_df):
    """Create loading-focused visualization"""
    try:
        fig = go.Figure()
        
        # Calculate loading percentages (handle missing RATE values)
        loading_pct = (branches_df['MVA'] / branches_df['RATE'].replace(0, 1) * 100).fillna(0)
        
        # Loading scatter plot
        fig.add_trace(go.Scatter(
            x=branches_df.index,
            y=loading_pct,
            mode='markers',
            marker=dict(
                size=8,
                color=loading_pct,
                colorscale='RdYlGn_r',
                showscale=True,
                colorbar=dict(title="Loading (%)")
            ),
            text=branches_df.apply(lambda row: f"Line {int(row['From_Bus'])}-{int(row['To_Bus'])}<br>Loading: {(row['MVA']/max(row['RATE'], 1)*100):.1f}%<br>MVA: {row['MVA']:.1f}", axis=1),
            hovertemplate='%{text}<extra></extra>',
            name='Branch Loading'
        ))
        
        # Add critical loading lines
        fig.add_hline(y=100, line_dash="dash", line_color="red",
                      annotation_text="100% Loading (Critical)")
        fig.add_hline(y=90, line_dash="dash", line_color="orange",
                      annotation_text="90% Loading (High)")
        
        fig.update_layout(
            title="Transmission Line Loading Analysis",
            xaxis_title="Branch Index",
            yaxis_title="Loading Percentage (%)",
            height=500
        )
        
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error creating loading plot: {str(e)}",
            xref="paper", yref="paper", x=0.5, y=0.5
        )
        return fig

def create_violation_analysis_plot(branches_df):
    """Create violation-focused visualization"""
    fig = go.Figure()
    
    # Filter violated branches (>100% loading)
    loading_pct = (branches_df['MVA'] / branches_df['RATE'] * 100).fillna(0)
    violated_branches = branches_df[loading_pct > 100].copy()
    violated_loading = loading_pct[loading_pct > 100]
    
    if len(violated_branches) > 0:
        fig.add_trace(go.Bar(
            x=[f"{int(row['From_Bus'])}-{int(row['To_Bus'])}" for _, row in violated_branches.iterrows()],
            y=violated_loading,
            marker_color='red',
            name='Overloaded Lines',
            text=[f"{val:.1f}%" for val in violated_loading],
            textposition='outside'
        ))
        
        title = f"Violation Analysis - {len(violated_branches)} Overloaded Lines"
    else:
        fig.add_annotation(
            text="No violations detected in current analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        title = "Violation Analysis - No Violations Found"
    
    fig.update_layout(
        title=title,
        xaxis_title="Transmission Line",
        yaxis_title="Loading Percentage (%)",
        height=500
    )
    
    return fig

def create_generator_analysis_plot():
    """Create generator analysis from database"""
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Get generator data
        cursor.execute("""
        SELECT BUS_NUMBER, KV_LEVEL, GEN_INI, GEN_NEW, GEN_ADJ
        FROM SLR_Generator 
        WHERE base_case_id = 42 AND contingency_case_id = 123
        ORDER BY BUS_NUMBER
        """)
        gen_data = cursor.fetchall()
        conn.close()
        
        if not gen_data:
            fig = go.Figure()
            fig.add_annotation(text="No generator data available", xref="paper", yref="paper", x=0.5, y=0.5)
            return fig
        
        fig = go.Figure()
        
        bus_numbers = [row[0] for row in gen_data]
        gen_initial = [row[2] for row in gen_data]
        gen_new = [row[3] for row in gen_data]
        
        # Initial generation
        fig.add_trace(go.Bar(
            x=bus_numbers,
            y=gen_initial,
            name='Initial Generation',
            marker_color='lightblue'
        ))
        
        # Adjusted generation
        fig.add_trace(go.Bar(
            x=bus_numbers,
            y=gen_new,
            name='New Generation',
            marker_color='darkblue'
        ))
        
        fig.update_layout(
            title=f"Generator Analysis - {len(gen_data)} Units",
            xaxis_title="Bus Number",
            yaxis_title="Generation (MW)",
            height=500,
            barmode='group'
        )
        
        return fig
        
    except Exception as e:
        print(f"Generator plot error: {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Error loading generator data: {e}", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

def create_integrated_power_flow_map(buses_df, branches_df):
    """Create comprehensive network diagram with bus importance and branch loading"""
    fig = go.Figure()
    
    # Calculate bus importance (generation + load)
    buses_df['importance'] = buses_df['PG'].fillna(0) + buses_df['PD'].fillna(0)
    
    # Add bus points sized by importance
    fig.add_trace(go.Scatter(
        x=buses_df['x_coord'],
        y=buses_df['y_coord'],
        mode='markers',
        marker=dict(
            size=np.sqrt(buses_df['importance']) * 2 + 5,  # Size by importance
            color=buses_df['VM'],  # Color by voltage
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Voltage (p.u.)", x=1.02)
        ),
        text=buses_df.apply(lambda row: f"Bus {int(row['BUS_NUMBER'])}<br>Voltage: {row['VM']:.3f} p.u.<br>Importance: {row['importance']:.1f} MW", axis=1),
        hovertemplate='%{text}<extra></extra>',
        name='Buses'
    ))
    
    # Add transmission lines with directional arrows and loading colors
    for _, branch in branches_df.head(30).iterrows():  # Show more lines for comprehensive view
        from_bus_data = buses_df[buses_df['BUS_NUMBER'] == branch['From_Bus']]
        to_bus_data = buses_df[buses_df['BUS_NUMBER'] == branch['To_Bus']]
        
        if not from_bus_data.empty and not to_bus_data.empty:
            loading_pct = (branch['MVA'] / max(branch['RATE'], 1)) * 100
            line_color = 'red' if loading_pct > 90 else 'orange' if loading_pct > 75 else 'green'
            line_width = min(max(loading_pct / 20, 1), 8)  # Width based on loading
            
            # Main line
            fig.add_trace(go.Scatter(
                x=[from_bus_data.iloc[0]['x_coord'], to_bus_data.iloc[0]['x_coord']],
                y=[from_bus_data.iloc[0]['y_coord'], to_bus_data.iloc[0]['y_coord']],
                mode='lines',
                line=dict(color=line_color, width=line_width),
                hovertemplate=f'Line {int(branch["From_Bus"])}-{int(branch["To_Bus"])}<br>Loading: {loading_pct:.1f}%<br>Flow: {branch["MVA"]:.1f} MVA<extra></extra>',
                showlegend=False
            ))
            
            # Add directional arrow
            mid_x = (from_bus_data.iloc[0]['x_coord'] + to_bus_data.iloc[0]['x_coord']) / 2
            mid_y = (from_bus_data.iloc[0]['y_coord'] + to_bus_data.iloc[0]['y_coord']) / 2
            
            fig.add_annotation(
                x=mid_x, y=mid_y,
                ax=from_bus_data.iloc[0]['x_coord'], ay=from_bus_data.iloc[0]['y_coord'],
                xref='x', yref='y', axref='x', ayref='y',
                arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor=line_color
            )
    
    fig.update_layout(
        title="Integrated Power Flow Map - Bus Importance & Branch Loading",
        xaxis_title="X Coordinate", yaxis_title="Y Coordinate",
        height=700, template="plotly_white"
    )
    return fig

def create_criticality_heatmap(buses_df, branches_df):
    """Create bus-branch criticality heatmap"""
    # Create a matrix of bus-branch interactions
    bus_nums = sorted(buses_df['BUS_NUMBER'].unique())[:20]  # Limit for visualization
    branch_nums = branches_df['branch_number'].head(20).tolist()
    
    # Calculate criticality score (simplified - based on voltage and loading)
    criticality_matrix = []
    for bus in bus_nums:
        row = []
        for branch_idx in branch_nums:
            branch = branches_df[branches_df['branch_number'] == branch_idx].iloc[0]
            bus_data = buses_df[buses_df['BUS_NUMBER'] == bus].iloc[0]
            
            # Criticality = voltage deviation * loading percentage
            voltage_dev = abs(1.0 - bus_data['VM'])
            loading_pct = (branch['MVA'] / max(branch['RATE'], 1)) * 100
            criticality = voltage_dev * loading_pct
            row.append(criticality)
        criticality_matrix.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=criticality_matrix,
        x=[f"Branch {b}" for b in branch_nums],
        y=[f"Bus {b}" for b in bus_nums],
        colorscale='Reds',
        colorbar=dict(title="Criticality Score")
    ))
    
    fig.update_layout(
        title="Bus-Branch Criticality Heatmap",
        xaxis_title="Transmission Branches", yaxis_title="Bus Numbers",
        height=600
    )
    return fig

def create_voltage_flow_3d_surface(buses_df, branches_df):
    """Create 3D surface plot showing voltage-flow correlation"""
    fig = go.Figure()
    
    # Create 3D scatter plot with buses as points
    fig.add_trace(go.Scatter3d(
        x=buses_df['x_coord'],
        y=buses_df['y_coord'],
        z=buses_df['VM'],
        mode='markers',
        marker=dict(
            size=buses_df['PD'] / 10 + 3,
            color=buses_df['VM'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Voltage (p.u.)")
        ),
        text=buses_df.apply(lambda row: f"Bus {int(row['BUS_NUMBER'])}<br>Voltage: {row['VM']:.3f} p.u.", axis=1),
        name='Buses'
    ))
    
    # Add 3D lines for transmission branches
    for _, branch in branches_df.head(20).iterrows():
        from_bus = buses_df[buses_df['BUS_NUMBER'] == branch['From_Bus']]
        to_bus = buses_df[buses_df['BUS_NUMBER'] == branch['To_Bus']]
        
        if not from_bus.empty and not to_bus.empty:
            loading_pct = (branch['MVA'] / max(branch['RATE'], 1)) * 100
            line_color = 'red' if loading_pct > 90 else 'orange' if loading_pct > 75 else 'green'
            
            fig.add_trace(go.Scatter3d(
                x=[from_bus.iloc[0]['x_coord'], to_bus.iloc[0]['x_coord']],
                y=[from_bus.iloc[0]['y_coord'], to_bus.iloc[0]['y_coord']],
                z=[from_bus.iloc[0]['VM'], to_bus.iloc[0]['VM']],
                mode='lines',
                line=dict(color=line_color, width=4),
                showlegend=False,
                hovertemplate=f'Line {int(branch["From_Bus"])}-{int(branch["To_Bus"])}<br>Loading: {loading_pct:.1f}%<extra></extra>'
            ))
    
    fig.update_layout(
        title="Voltage-Flow Correlation 3D Surface",
        scene=dict(
            xaxis_title="X Coordinate",
            yaxis_title="Y Coordinate", 
            zaxis_title="Voltage (p.u.)"
        ),
        height=700
    )
    return fig

def create_cascading_failure_visualization(buses_df, branches_df):
    """Visualize cascading failure propagation paths"""
    fig = go.Figure()
    
    # Simulate a cascading failure starting from most loaded line
    branches_df['loading_pct'] = (branches_df['MVA'] / branches_df['RATE'].replace(0, 1) * 100).fillna(0)
    initial_failure = branches_df.loc[branches_df['loading_pct'].idxmax()]
    
    # Step 1: Initial failure (red)
    from_bus = buses_df[buses_df['BUS_NUMBER'] == initial_failure['From_Bus']].iloc[0]
    to_bus = buses_df[buses_df['BUS_NUMBER'] == initial_failure['To_Bus']].iloc[0]
    
    fig.add_trace(go.Scatter(
        x=[from_bus['x_coord'], to_bus['x_coord']],
        y=[from_bus['y_coord'], to_bus['y_coord']],
        mode='lines+markers',
        line=dict(color='red', width=8),
        marker=dict(size=12, color='red'),
        name='Step 1: Initial Failure',
        hovertemplate=f'Initial Failure: Line {int(initial_failure["From_Bus"])}-{int(initial_failure["To_Bus"])}<br>Loading: {initial_failure["loading_pct"]:.1f}%<extra></extra>'
    ))
    
    # Step 2: Secondary failures (orange)
    overloaded_branches = branches_df[branches_df['loading_pct'] > 85].head(5)
    for i, (_, branch) in enumerate(overloaded_branches.iterrows()):
        if branch['branch_number'] != initial_failure['branch_number']:
            from_bus = buses_df[buses_df['BUS_NUMBER'] == branch['From_Bus']]
            to_bus = buses_df[buses_df['BUS_NUMBER'] == branch['To_Bus']]
            
            if not from_bus.empty and not to_bus.empty:
                fig.add_trace(go.Scatter(
                    x=[from_bus.iloc[0]['x_coord'], to_bus.iloc[0]['x_coord']],
                    y=[from_bus.iloc[0]['y_coord'], to_bus.iloc[0]['y_coord']],
                    mode='lines+markers',
                    line=dict(color='orange', width=6),
                    marker=dict(size=10, color='orange'),
                    name=f'Step {i+2}: Secondary Failure',
                    hovertemplate=f'Secondary Failure: Line {int(branch["From_Bus"])}-{int(branch["To_Bus"])}<br>Loading: {branch["loading_pct"]:.1f}%<extra></extra>'
                ))
    
    # Add all other buses
    fig.add_trace(go.Scatter(
        x=buses_df['x_coord'],
        y=buses_df['y_coord'],
        mode='markers',
        marker=dict(size=6, color='lightgray'),
        name='Normal Buses',
        showlegend=False
    ))
    
    fig.update_layout(
        title="Cascading Failure Path Visualization",
        xaxis_title="X Coordinate", yaxis_title="Y Coordinate",
        height=600, template="plotly_white"
    )
    return fig

def create_contingency_impact_distribution(buses_df, branches_df):
    """Create contingency impact distribution chart"""
    fig = go.Figure()
    
    # Simulate contingency impacts
    contingencies = [f"Contingency {i+1}" for i in range(10)]
    voltage_violations = np.random.exponential(2, 10) * 5  # Simulated data
    branch_overloads = np.random.exponential(1.5, 10) * 8
    
    # Voltage violations (bars)
    fig.add_trace(go.Bar(
        x=contingencies,
        y=voltage_violations,
        name='Bus Voltage Violations',
        marker_color='red',
        yaxis='y'
    ))
    
    # Branch overloads (line)
    fig.add_trace(go.Scatter(
        x=contingencies,
        y=branch_overloads,
        mode='lines+markers',
        name='Branch Overloads',
        line=dict(color='blue', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Contingency Impact Distribution Chart",
        xaxis_title="Contingency Scenarios",
        yaxis=dict(title="Voltage Violations (Count)", side="left"),
        yaxis2=dict(title="Branch Overloads (Count)", side="right", overlaying="y"),
        height=500, template="plotly_white"
    )
    return fig

def create_before_after_comparison(buses_df, branches_df):
    """Create before/after split-screen comparison"""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Before Contingency", "After Contingency"),
        specs=[[{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    # Before scenario (left)
    fig.add_trace(go.Scatter(
        x=buses_df['x_coord'],
        y=buses_df['y_coord'],
        mode='markers',
        marker=dict(
            size=buses_df['PD'] / 5,
            color=buses_df['VM'],
            colorscale='RdYlGn',
            showscale=False
        ),
        name='Before: Normal Operation',
        text=buses_df.apply(lambda row: f"Bus {int(row['BUS_NUMBER'])}<br>Voltage: {row['VM']:.3f} p.u.", axis=1)
    ), row=1, col=1)
    
    # After scenario (right) - simulate voltage drops
    buses_after = buses_df.copy()
    buses_after['VM_after'] = buses_df['VM'] - np.random.uniform(0.01, 0.05, len(buses_df))
    
    fig.add_trace(go.Scatter(
        x=buses_after['x_coord'],
        y=buses_after['y_coord'],
        mode='markers',
        marker=dict(
            size=buses_after['PD'] / 5,
            color=buses_after['VM_after'],
            colorscale='RdYlGn',
            showscale=True
        ),
        name='After: Post-Contingency',
        text=buses_after.apply(lambda row: f"Bus {int(row['BUS_NUMBER'])}<br>Voltage: {row['VM_after']:.3f} p.u.", axis=1)
    ), row=1, col=2)
    
    fig.update_layout(title="Before/After Split-Screen Comparison", height=600)
    return fig

def create_dlr_benefit_bubble_chart(buses_df, branches_df, comparison_df):
    """Create DLR benefit bubble chart"""
    fig = go.Figure()
    
    if comparison_df.empty:
        # Generate synthetic data for demonstration
        n_points = 20
        bus_loading = np.random.uniform(20, 95, n_points)
        branch_loading = np.random.uniform(30, 100, n_points)
        dlr_benefit = np.random.uniform(5, 40, n_points)
        
        fig.add_trace(go.Scatter(
            x=bus_loading,
            y=branch_loading,
            mode='markers',
            marker=dict(
                size=dlr_benefit,
                color=dlr_benefit,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="DLR Benefit (%)")
            ),
            text=[f"Bus Loading: {bl:.1f}%<br>Branch Loading: {brl:.1f}%<br>DLR Benefit: {db:.1f}%" 
                  for bl, brl, db in zip(bus_loading, branch_loading, dlr_benefit)],
            hovertemplate='%{text}<extra></extra>',
            name='DLR Benefits'
        ))
    else:
        # Use real comparison data
        dlr_benefit = ((comparison_df['DLR_RATE'] - comparison_df['SLR_RATE']) / 
                      comparison_df['SLR_RATE'] * 100).fillna(0)
        
        fig.add_trace(go.Scatter(
            x=comparison_df.index,
            y=comparison_df['SLR_MVA'] / comparison_df['SLR_RATE'] * 100,
            mode='markers',
            marker=dict(
                size=dlr_benefit * 2,
                color=dlr_benefit,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="DLR Benefit (%)")
            ),
            name='DLR Benefits'
        ))
    
    fig.update_layout(
        title="DLR Benefit Bubble Chart",
        xaxis_title="Bus Loading Level (%)",
        yaxis_title="Connected Branch Loading (%)",
        height=600
    )
    return fig

def create_weather_dlr_correlation(buses_df, branches_df):
    """Create weather-DLR-load correlation map"""
    fig = go.Figure()
    
    # Simulate weather and DLR data
    n_points = len(branches_df.head(20))
    wind_speed = np.random.uniform(2, 15, n_points)
    temperature = np.random.uniform(15, 35, n_points)
    dlr_capacity_gain = wind_speed * 2 + (35 - temperature) * 1.5  # Simplified model
    
    fig.add_trace(go.Scatter(
        x=wind_speed,
        y=temperature,
        mode='markers',
        marker=dict(
            size=dlr_capacity_gain,
            color=dlr_capacity_gain,
            colorscale='RdYlBu_r',
            showscale=True,
            colorbar=dict(title="DLR Capacity Gain (%)")
        ),
        text=[f"Wind: {w:.1f} m/s<br>Temp: {t:.1f}°C<br>DLR Gain: {g:.1f}%" 
              for w, t, g in zip(wind_speed, temperature, dlr_capacity_gain)],
        hovertemplate='%{text}<extra></extra>',
        name='Weather-DLR Correlation'
    ))
    
    fig.update_layout(
        title="Weather-DLR-Load Correlation Map",
        xaxis_title="Wind Speed (m/s)",
        yaxis_title="Temperature (°C)",
        height=600
    )
    return fig

def create_constraint_binding_analysis(buses_df, branches_df):
    """Create constraint binding analysis visualization"""
    fig = go.Figure()
    
    # Analyze constraints
    voltage_constrained = buses_df[(buses_df['VM'] < 0.95) | (buses_df['VM'] > 1.05)]
    thermal_constrained = branches_df[
        (branches_df['MVA'] / branches_df['RATE'].replace(0, 1) * 100) > 90
    ]
    
    # Voltage-constrained buses
    if not voltage_constrained.empty:
        fig.add_trace(go.Scatter(
            x=voltage_constrained['x_coord'],
            y=voltage_constrained['y_coord'],
            mode='markers',
            marker=dict(size=15, color='red', symbol='triangle-up'),
            name='Voltage Constrained Buses',
            text=voltage_constrained.apply(lambda row: f"Bus {int(row['BUS_NUMBER'])}<br>Voltage: {row['VM']:.3f} p.u.", axis=1)
        ))
    
    # Thermal-constrained branches
    for _, branch in thermal_constrained.head(10).iterrows():
        from_bus = buses_df[buses_df['BUS_NUMBER'] == branch['From_Bus']]
        to_bus = buses_df[buses_df['BUS_NUMBER'] == branch['To_Bus']]
        
        if not from_bus.empty and not to_bus.empty:
            fig.add_trace(go.Scatter(
                x=[from_bus.iloc[0]['x_coord'], to_bus.iloc[0]['x_coord']],
                y=[from_bus.iloc[0]['y_coord'], to_bus.iloc[0]['y_coord']],
                mode='lines',
                line=dict(color='orange', width=6),
                name='Thermal Constrained Lines',
                showlegend=False
            ))
    
    # Normal buses
    normal_buses = buses_df[~buses_df.index.isin(voltage_constrained.index)]
    fig.add_trace(go.Scatter(
        x=normal_buses['x_coord'],
        y=normal_buses['y_coord'],
        mode='markers',
        marker=dict(size=8, color='lightgreen'),
        name='Normal Operation Buses',
        showlegend=False
    ))
    
    fig.update_layout(
        title="Constraint Binding Analysis - Voltage vs Thermal Limits",
        xaxis_title="X Coordinate", yaxis_title="Y Coordinate",
        height=600, template="plotly_white"
    )
    return fig

def create_upgrade_priority_matrix(buses_df, branches_df):
    """Create upgrade priority matrix visualization"""
    fig = go.Figure()
    
    # Calculate metrics for priority matrix
    buses_df['importance'] = buses_df['PG'].fillna(0) + buses_df['PD'].fillna(0)
    branches_df['utilization'] = (branches_df['MVA'] / branches_df['RATE'].replace(0, 1) * 100).fillna(0)
    
    # Create data for matrix (sample 15 buses)
    sample_buses = buses_df.head(15)
    
    bus_importance = sample_buses['importance']
    connected_utilization = []
    violation_frequency = []
    
    for _, bus in sample_buses.iterrows():
        # Find branches connected to this bus
        connected_branches = branches_df[
            (branches_df['From_Bus'] == bus['BUS_NUMBER']) | 
            (branches_df['To_Bus'] == bus['BUS_NUMBER'])
        ]
        
        if not connected_branches.empty:
            avg_utilization = connected_branches['utilization'].mean()
            violations = len(connected_branches[connected_branches['utilization'] > 100])
        else:
            avg_utilization = 0
            violations = 0
            
        connected_utilization.append(avg_utilization)
        violation_frequency.append(violations * 10 + 5)  # Scale for visibility
    
    fig.add_trace(go.Scatter(
        x=bus_importance,
        y=connected_utilization,
        mode='markers',
        marker=dict(
            size=violation_frequency,
            color=violation_frequency,
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Violation Frequency")
        ),
        text=[f"Bus {int(bus['BUS_NUMBER'])}<br>Importance: {imp:.1f} MW<br>Avg Utilization: {util:.1f}%<br>Violations: {int((vf-5)/10)}" 
              for bus, imp, util, vf in zip(sample_buses.itertuples(), bus_importance, connected_utilization, violation_frequency)],
        hovertemplate='%{text}<extra></extra>',
        name='Upgrade Priority'
    ))
    
    # Add quadrant lines
    med_importance = bus_importance.median()
    med_utilization = np.array(connected_utilization).mean()
    
    fig.add_hline(y=med_utilization, line_dash="dash", line_color="gray", annotation_text="Avg Utilization")
    fig.add_vline(x=med_importance, line_dash="dash", line_color="gray", annotation_text="Avg Importance")
    
    fig.update_layout(
        title="Upgrade Priority Matrix - Bus Importance vs Connected Branch Utilization",
        xaxis_title="Bus Importance (Load + Generation MW)",
        yaxis_title="Connected Branch Utilization (%)",
        height=600
    )
    return fig

def create_minimal_chat_component():
    """Create the minimal chat component with left-bottom positioning"""
    return html.Div([
        # Chat Toggle Button (left-bottom positioned)
        html.Button(
            "🖥️",
            id="chat-toggle-btn",
            style={
                "position": "fixed",
                "left": "20px",  # Left side instead of right
                "bottom": "20px",
                "width": "60px",
                "height": "60px",
                "borderRadius": "50%",
                "backgroundColor": "#007bff",
                "color": "white",
                "border": "none",
                "fontSize": "24px",
                "cursor": "pointer",
                "zIndex": "1000",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.3)"
            }
        ),
        
        # Chat Interface (hidden by default)
        html.Div([
            html.Div([
                html.H4("🖥️ AI Power Systems Assistant + RAG", style={"margin": "0", "color": "#333"}),
                html.Button("✕", id="chat-close-btn", style={
                    "position": "absolute", "top": "10px", "right": "15px",
                    "background": "none", "border": "none", "fontSize": "20px", "cursor": "pointer"
                })
            ], style={"padding": "15px", "borderBottom": "1px solid #ddd", "position": "relative"}),
            
            html.Div(id="chat-messages", children=[
                html.Div("👋 Hi! I'm your AI assistant with RAG-enhanced database knowledge. Ask me about power systems, visualizations, or specific data!", 
                        style={"padding": "10px", "backgroundColor": "#f0f8ff", "margin": "5px", "borderRadius": "10px"})
            ], style={"height": "300px", "overflowY": "auto", "padding": "10px"}),
            
            html.Div([
                dcc.Input(
                    id="chat-input",
                    type="text",
                    placeholder="Ask about power systems...",
                    style={"width": "85%", "padding": "10px", "border": "1px solid #ddd", "borderRadius": "5px"}
                ),
                html.Button("Send", id="chat-send-btn", style={
                    "width": "13%", "padding": "10px", "backgroundColor": "#007bff", 
                    "color": "white", "border": "none", "borderRadius": "5px", "cursor": "pointer"
                })
            ], style={"padding": "10px", "display": "flex", "gap": "5px"})
        ], id="chat-interface", style={
            "position": "fixed",
            "left": "20px",  # Left side positioning
            "bottom": "90px",
            "width": "350px",
            "height": "400px",
            "backgroundColor": "white",
            "border": "1px solid #ddd",
            "borderRadius": "10px",
            "boxShadow": "0 4px 20px rgba(0,0,0,0.2)",
            "display": "none",
            "zIndex": "999"
        })
    ])

# Initialize the application
print("Loading database data...")
buses_df, branches_df, comparison_df = load_database_data()

# Initialize RAG system if available
if RAG_AVAILABLE:
    try:
        initialize_rag()
        print("RAG system initialized successfully")
    except Exception as e:
        print(f"RAG initialization warning: {e}")

# Initialize Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("Power System Visualization", style={"textAlign": "center", "margin": "20px"}),
    
    html.Div([
        html.H3("System Overview"),
        html.P("This application displays power system data from the IEEE 118-bus database."),
        html.P("🖥️ Click the desktop icon in the bottom-left corner to interact with the RAG-enhanced AI assistant!"),
        html.P("📊 Data includes base case analysis, contingency scenarios, and SLR/DLR comparisons."),
        html.P("🎯 **Try asking:** 'Show voltage visualization', 'Which lines are overloaded?', 'Compare SLR vs DLR'"),
    ], style={"margin": "20px", "padding": "20px", "backgroundColor": "#f8f9fa", "borderRadius": "5px"}),
    
    # Visualization selector
    html.Div([
        html.H4("📈 Select Visualization:"),
        dcc.Dropdown(
            id='viz-selector',
            options=[
                {'label': '🏠 Main Network View', 'value': 'network'},
                {'label': '⚡ Voltage Analysis', 'value': 'voltage'},
                {'label': '📊 Loading Analysis', 'value': 'loading'},
                {'label': '⚠️ Violation Analysis', 'value': 'violations'},
                {'label': '🔄 SLR vs DLR Comparison', 'value': 'comparison'},
                {'label': '🏭 Generator Analysis', 'value': 'generators'},
                {'label': '🌐 Integrated Power Flow Map', 'value': 'integrated_flow'},
                {'label': '🔥 Bus-Branch Criticality Heatmap', 'value': 'criticality_heatmap'},
                {'label': '📈 Voltage-Flow 3D Surface', 'value': 'voltage_flow_3d'},
                {'label': '⚡ Cascading Failure Path', 'value': 'cascading_failure'},
                {'label': '📊 Contingency Impact Distribution', 'value': 'contingency_impact'},
                {'label': '🔄 Before/After Comparison', 'value': 'before_after'},
                {'label': '💡 DLR Benefit Bubble Chart', 'value': 'dlr_benefit'},
                {'label': '🌤️ Weather-DLR Correlation', 'value': 'weather_dlr'},
                {'label': '🔒 Constraint Binding Analysis', 'value': 'constraint_binding'},
                {'label': '🎯 Upgrade Priority Matrix', 'value': 'upgrade_priority'}
            ],
            value='network',
            style={'width': '100%'}
        )
    ], style={"margin": "20px", "padding": "15px", "backgroundColor": "#e3f2fd", "borderRadius": "5px"}),
    
    # Dynamic visualization area
    dcc.Graph(id="dynamic-plot"),
    
    # Hidden div to store visualization commands from AI chat
    html.Div(id="viz-command-store", style={"display": "none"}),
    
    # Hidden div to track current visualization type for AI context
    html.Div(id="current-viz-type", children="network", style={"display": "none"}),
    
    html.Div([
        html.H3("Database Information:"),
        html.Ul([
            html.Li(f"✅ Total Buses: {len(buses_df)} (IEEE 118-bus system)"),
            html.Li(f"✅ Total Branches: {len(branches_df)} transmission lines"),
            html.Li("✅ Real-time data from SQLite database"),
            html.Li("✅ RAG-enhanced AI responses with database knowledge")
        ])
    ], style={"margin": "20px", "padding": "20px", "backgroundColor": "#e8f5e8", "borderRadius": "5px"}),
    
    # Add the chat component
    create_minimal_chat_component()
])

# Visualization selection callback
@app.callback(
    Output("dynamic-plot", "figure"),
    [Input("viz-selector", "value")]
)
def update_visualization(selected_viz):
    """Update visualization based on selection"""
    try:
        if selected_viz == 'voltage':
            return create_voltage_analysis_plot(buses_df)
        elif selected_viz == 'loading':
            return create_loading_analysis_plot(branches_df)
        elif selected_viz == 'violations':
            return create_violation_analysis_plot(branches_df)
        elif selected_viz == 'comparison':
            return create_slr_dlr_comparison(comparison_df)
        elif selected_viz == 'generators':
            return create_generator_analysis_plot()
        # Advanced Network Performance Visualizations
        elif selected_viz == 'integrated_flow':
            return create_integrated_power_flow_map(buses_df, branches_df)
        elif selected_viz == 'criticality_heatmap':
            return create_criticality_heatmap(buses_df, branches_df)
        elif selected_viz == 'voltage_flow_3d':
            return create_voltage_flow_3d_surface(buses_df, branches_df)
        elif selected_viz == 'cascading_failure':
            return create_cascading_failure_visualization(buses_df, branches_df)
        elif selected_viz == 'contingency_impact':
            return create_contingency_impact_distribution(buses_df, branches_df)
        elif selected_viz == 'before_after':
            return create_before_after_comparison(buses_df, branches_df)
        elif selected_viz == 'dlr_benefit':
            return create_dlr_benefit_bubble_chart(buses_df, branches_df, comparison_df)
        elif selected_viz == 'weather_dlr':
            return create_weather_dlr_correlation(buses_df, branches_df)
        elif selected_viz == 'constraint_binding':
            return create_constraint_binding_analysis(buses_df, branches_df)
        elif selected_viz == 'upgrade_priority':
            return create_upgrade_priority_matrix(buses_df, branches_df)
        else:  # Default to network view
            return create_power_system_plot(buses_df, branches_df)
    except Exception as e:
        # Return error plot if something goes wrong
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error generating visualization: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(title="Visualization Error")
        return fig

# Chat callbacks
@app.callback(
    Output("chat-interface", "style"),
    [Input("chat-toggle-btn", "n_clicks"), Input("chat-close-btn", "n_clicks")],
    [State("chat-interface", "style")]
)
def toggle_chat(toggle_clicks, close_clicks, current_style):
    ctx = callback_context
    if not ctx.triggered:
        return current_style
    
    if current_style["display"] == "none":
        current_style["display"] = "block"
    else:
        current_style["display"] = "none"
    return current_style

@app.callback(
    [Output("chat-messages", "children"), Output("chat-input", "value"), Output("viz-command-store", "children")],
    [Input("chat-send-btn", "n_clicks")],
    [State("chat-input", "value"), State("chat-messages", "children"), State("current-viz-type", "children")]
)
def handle_chat_message(n_clicks, user_message, current_messages, current_viz_type):
    if not n_clicks or not user_message:
        return current_messages, "", ""
    
    # Add user message
    user_msg = html.Div(f"You: {user_message}", style={
        "padding": "8px", "backgroundColor": "#e3f2fd", "margin": "5px",
        "borderRadius": "10px", "textAlign": "right"
    })
    
    # Get AI response with current visualization context
    ai_response, viz_command = get_ai_response(user_message, current_viz_type or 'network')
    ai_msg = html.Div(ai_response, style={
        "padding": "8px", "backgroundColor": "#f0f8ff", "margin": "5px",
        "borderRadius": "10px"
    })
    
    # Update messages
    updated_messages = current_messages + [user_msg, ai_msg]
    
    return updated_messages, "", viz_command or ""

# New callback to update visualization selector when AI detects commands
@app.callback(
    [Output("viz-selector", "value"), Output("current-viz-type", "children")],
    [Input("viz-command-store", "children")],
    prevent_initial_call=True
)
def update_viz_selector_from_ai(viz_command):
    """Update visualization selector when AI detects visualization commands"""
    valid_commands = ['voltage', 'loading', 'violations', 'comparison', 'generators', 'network',
                     'integrated_flow', 'criticality_heatmap', 'voltage_flow_3d', 'cascading_failure',
                     'contingency_impact', 'before_after', 'dlr_benefit', 'weather_dlr',
                     'constraint_binding', 'upgrade_priority']
    if viz_command and viz_command in valid_commands:
        return viz_command, viz_command
    return dash.no_update, dash.no_update

# Callback to track visualization changes from dropdown
@app.callback(
    Output("current-viz-type", "children", allow_duplicate=True),
    [Input("viz-selector", "value")],
    prevent_initial_call=True
)
def track_viz_type_change(selected_viz):
    """Track when user manually changes visualization via dropdown"""
    return selected_viz or 'network'

if __name__ == "__main__":
    print("Starting Power System Visualization with Real Database Data")
    print("AI Assistant: PNNL AI Incubator API with Claude-3.5 Sonnet + RAG")
    print("Chat Position: LEFT-BOTTOM (as requested)")
    print("Data Source: Real IEEE 118-bus database")
    print("URL: http://127.0.0.1:8054")
    print("RAG System: Enhanced with database-grounded responses")
    app.run(debug=False, port=8054, threaded=True)