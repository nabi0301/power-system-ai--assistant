#!/usr/bin/env python3
"""
Dual Network Graph Viewer - Side-by-Side Base Case and Contingency Case
Matches the style and functionality of data_viz_fall.py
"""

import sqlite3
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

def generate_positions(G):
    """Generate positions for nodes in the graph using spring layout."""
    return nx.spring_layout(G, seed=42)

def generate_curved_path(x_from, y_from, x_to, y_to, curvature=0.2):
    """Generate a curved path between two points using quadratic Bezier curve."""
    control_x = (x_from + x_to) / 2 + curvature * (y_to - y_from)
    control_y = (y_from + y_to) / 2 - curvature * (x_to - x_from)
    bezier_x = [x_from, control_x, x_to]
    bezier_y = [y_from, control_y, y_to]
    return bezier_x, bezier_y

def get_node_color(vm):
    """Get node color based on voltage magnitude."""
    if vm is None:
        vm = 1.0
    return "#F8DB00" if vm < 1.02 else "#F1EF76" if vm < 0.90 else "#F3A60D"

def get_node_symbol(pg):
    """Get node symbol based on generation."""
    if pg is None:
        pg = 0
    return "triangle-down" if pg > 0 else "circle"

def get_branch_color(apparent_power, rate, vio=0):
    """Get branch color based on loading."""
    if rate is None or rate == 0:
        return "rgb(0, 128, 0)"
    
    loading_percentage = (apparent_power / rate * 100) if rate > 0 else 0
    
    if loading_percentage > 100 or vio >= 100:
        return "rgb(255, 0, 0)"  # Red for violations
    elif loading_percentage > 90:
        return "rgb(255, 165, 0)"  # Orange for warnings
    elif loading_percentage > 75:
        return "#0D7798"  # Dark blue
    elif loading_percentage > 50:
        return "#28aad9"  # Medium blue
    else:
        return "#abe6f6"  # Light blue

def get_branch_width(apparent_power, rate, vio=0):
    """Get branch width based on loading."""
    if rate is None or rate == 0:
        return 2
    
    loading_percentage = (apparent_power / rate * 100) if rate > 0 else 0
    
    if loading_percentage > 100 or vio >= 100:
        return 8  # Extra thick for violations
    elif loading_percentage > 90:
        return 6  # Thick for warnings
    elif apparent_power > 50:
        return 4  # Medium for high power flow
    else:
        return 2  # Thin for low power flow

def create_single_network_graph(buses_df, branches_df, title, positions=None):
    """Create a single network graph matching data_viz_fall.py style."""
    
    # Create graph
    G = nx.Graph()
    
    # Clean data
    buses_df = buses_df.dropna(subset=['BUS_NUMBER'])
    branches_df = branches_df.dropna(subset=['From_Bus', 'To_Bus'])
    
    # Add nodes
    for _, row in buses_df.iterrows():
        G.add_node(
            int(row["BUS_NUMBER"]),
            vm=row.get("VM", 1.0),
            va=row.get("VA", 0),
            base_kv=row.get("BASE_KV", 0),
            pg=row.get("PG", 0),
            qg=row.get("QG", 0),
            pd=row.get("PD", 0),
            qd=row.get("QD", 0)
        )
    
    # Add edges
    for _, row in branches_df.iterrows():
        G.add_edge(
            int(row["From_Bus"]),
            int(row["To_Bus"]),
            pf=row.get("PF", 0),
            qf=row.get("QF", 0),
            mva=row.get("MVA", 0),
            rate=row.get("RATE", float("inf")),
            vio=row.get("VIO", 0)
        )
    
    # Use provided positions or generate new ones
    if positions is None:
        positions = generate_positions(G)
    
    # Ensure all nodes in current graph have positions
    # If a node doesn't exist in positions, add it near other nodes
    for node in G.nodes:
        if node not in positions:
            positions[node] = (0, 0)  # Default position if missing
    
    # Create traces list
    traces = []
    
    # Add branch traces
    for edge in G.edges(data=True):
        from_bus, to_bus, attributes = edge
        x_from, y_from = positions[from_bus]
        x_to, y_to = positions[to_bus]
        bezier_x, bezier_y = generate_curved_path(x_from, y_from, x_to, y_to, curvature=0.2)
        
        pf = attributes.get("pf", 0)
        qf = attributes.get("qf", 0)
        vio = attributes.get("vio", 0)
        rate = attributes.get("rate", float('inf'))
        
        apparent_power = math.sqrt(pf**2 + qf**2)
        branch_color = get_branch_color(apparent_power, rate, vio)
        branch_width = get_branch_width(apparent_power, rate, vio)
        
        loading_percentage = (apparent_power / rate * 100) if rate > 0 else 0
        
        traces.append(go.Scatter(
            x=bezier_x,
            y=bezier_y,
            mode="lines",
            line=dict(color=branch_color, width=branch_width),
            hoverinfo="text",
            hovertext=(
                f"<b>From:</b> {from_bus} → <b>To:</b> {to_bus}<br>"
                f"<b>Power Flow (PF):</b> {pf:.2f} MW<br>"
                f"<b>Reactive Power (QF):</b> {qf:.2f} MVAr<br>"
                f"<b>Apparent Power (S):</b> {apparent_power:.2f} MVA<br>"
                f"<b>RATE:</b> {rate:.2f} MVA<br>"
                f"<b>Loading:</b> {loading_percentage:.1f}%<br>"
                f"<b>Status:</b> {'VIOLATED' if loading_percentage > 100 else 'Normal'}"
            ),
            showlegend=False
        ))
    
    # Create node trace
    hovertext_list = []
    for node in G.nodes:
        vm = G.nodes[node].get('vm', 1.0)
        pg = G.nodes[node].get('pg', 0)
        qg = G.nodes[node].get('qg', 0)
        pd = G.nodes[node].get('pd', 0)
        qd = G.nodes[node].get('qd', 0)
        
        hover_info = (
            f"<b>Bus:</b> {node}<br>"
            f"<b>Voltage:</b> {vm:.4f} p.u.<br>"
            f"<b>Generation:</b> {pg:.2f} MW<br>"
            f"<b>Load:</b> {pd:.2f} MW"
        )
        hovertext_list.append(hover_info)
    
    node_trace = go.Scatter(
        x=[positions[node][0] for node in G.nodes],
        y=[positions[node][1] for node in G.nodes],
        mode="markers",
        marker=dict(
            size=15,
            symbol=[get_node_symbol(G.nodes[node].get('pg', 0)) for node in G.nodes],
            color=[get_node_color(G.nodes[node].get('vm', 1.0)) for node in G.nodes],
            line=dict(color="black", width=1),
        ),
        hoverinfo="text",
        hovertext=hovertext_list,
        showlegend=False
    )
    
    traces.append(node_trace)
    
    return traces

def create_dual_network_graph(case_id, contingency_id):
    """
    Create side-by-side network graphs for base case and contingency case.
    Matches data_viz_fall.py style.
    """
    
    # Connect to database
    conn = sqlite3.connect('data.db')
    
    # Load base case data
    base_buses_df = pd.read_sql_query(f"""
        SELECT BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD
        FROM BaseBusData
        WHERE base_case_id = {case_id}
    """, conn)
    
    base_branches_df = pd.read_sql_query(f"""
        SELECT From_Bus, To_Bus, PF, QF, MVA, RATE, VIO
        FROM BaseBranchData
        WHERE base_case_id = {case_id}
    """, conn)
    
    # Load contingency case data
    cont_buses_df = pd.read_sql_query(f"""
        SELECT bus_number as BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD
        FROM ContingencyBusData
        WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
    """, conn)
    
    cont_branches_df = pd.read_sql_query(f"""
        SELECT From_Bus, To_Bus, PF, QF, MVA, RATE, VIO
        FROM ContingencyBranchData
        WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
    """, conn)
    
    conn.close()
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f'<b>Base Case {case_id}</b>',
            f'<b>Contingency {contingency_id} (Case {case_id})</b>'
        ),
        horizontal_spacing=0.05,
        specs=[[{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    # Generate consistent positions based on base case topology
    # This ensures both graphs use the same node positions for easy comparison
    base_G = nx.Graph()
    
    # Add all base case nodes and edges to determine topology
    for _, row in base_buses_df.iterrows():
        base_G.add_node(int(row["BUS_NUMBER"]))
    
    for _, row in base_branches_df.iterrows():
        base_G.add_edge(int(row["From_Bus"]), int(row["To_Bus"]))
    
    # Generate positions once for consistent layout
    consistent_positions = generate_positions(base_G)
    print(f"Generated consistent positions for {len(consistent_positions)} nodes")
    
    # Create base case graph with consistent positions
    print(f"Creating base case graph: {len(base_buses_df)} buses, {len(base_branches_df)} branches")
    base_traces = create_single_network_graph(base_buses_df, base_branches_df, "Base Case", consistent_positions)
    
    # Create contingency case graph with same positions
    print(f"Creating contingency graph: {len(cont_buses_df)} buses, {len(cont_branches_df)} branches")
    cont_traces = create_single_network_graph(cont_buses_df, cont_branches_df, "Contingency", consistent_positions)
    
    # Add base case traces to left subplot
    for trace in base_traces:
        fig.add_trace(trace, row=1, col=1)
    
    # Add contingency traces to right subplot
    for trace in cont_traces:
        fig.add_trace(trace, row=1, col=2)
    
    # Add legend traces
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="lines",
        line=dict(color="rgb(255, 0, 0)", width=8),
        name="Violations (>100% Loading)",
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="lines",
        line=dict(color="rgb(255, 165, 0)", width=6),
        name="Warning (>90% Loading)",
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="lines",
        line=dict(color="rgb(0, 128, 0)", width=4),
        name="Normal Operation",
        showlegend=True
    ))
    
    # Update layout
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
    
    fig.update_layout(
        title={
            'text': f'<b>Network Comparison: Base Case vs Contingency {contingency_id}</b>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        height=700,
        hovermode='closest',
        plot_bgcolor='rgba(240,240,240,0.3)',
        paper_bgcolor='white'
    )
    
    return fig

# Test function
if __name__ == "__main__":
    print("Creating dual network graph...")
    fig = create_dual_network_graph(case_id=0, contingency_id=1)
    print("✅ Dual network graph created successfully!")
    print(f"Figure has {len(fig.data)} traces")
    
    # Save to HTML for testing
    fig.write_html("dual_network_test.html")
    print("✅ Saved to dual_network_test.html")
