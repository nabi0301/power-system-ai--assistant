#!/usr/bin/env python3
"""
Simplified Power System Visualization - Fall 2025 Edition
This is a simplified version that should work reliably.
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import math
import base64
from datetime import datetime

# Create a very simple Dash app
app = dash.Dash(__name__)
app.title = "Fall 2025 Power System Visualization"

# Create sample data
def create_sample_data():
    print("Creating sample data...")
    buses = []
    for i in range(1, 119):
        buses.append({
            'BUS_NUMBER': i,
            'VM': 0.95 + (i % 15) * 0.01,  # Voltage magnitude between 0.95 and 1.09
            'PD': 50 + (i % 20) * 5,       # Load between 50 and 145 MW
            'QD': 15 + (i % 15) * 3,       # Reactive load
            'BASE_KV': 138 if i % 3 == 0 else 230 if i % 5 == 0 else 345 if i % 7 == 0 else 500,  # Different voltage levels
            'x_coord': (i % 12) * 30,      # Grid coordinates
            'y_coord': (i // 12) * 25
        })
    
    branches = []
    for i in range(1, 150):
        from_bus = i % 118 + 1
        to_bus = (i + 7) % 118 + 1
        if from_bus != to_bus:
            mva = 100 + (i % 50) * 10      # Flow between 100 and 590 MVA
            rate = 150 + (i % 40) * 25     # Rating between 150 and 1125 MVA
            branches.append({
                'branch_number': i,
                'From_Bus': from_bus,
                'To_Bus': to_bus,
                'MVA': mva,
                'RATE': rate
            })
    
    return pd.DataFrame(buses), pd.DataFrame(branches)

# Load data
buses_df, branches_df = create_sample_data()

# Create grid layout visualization
def create_grid_layout_visualization():
    fig = go.Figure()
    
    # Add bus nodes with voltage data
    fig.add_trace(go.Scatter(
        x=buses_df['x_coord'],
        y=buses_df['y_coord'],
        mode='markers+text',
        marker=dict(
            size=buses_df['PD'] / 5,  # Size based on load data
            color=buses_df['VM'],     # Color based on voltage magnitude
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Voltage Magnitude (p.u.)")
        ),
        text=buses_df['BUS_NUMBER'].astype(int).astype(str),  # Show bus numbers directly
        textposition="middle center",
        textfont=dict(
            family="Arial Black",
            size=10,
            color="black"
        ),
        hovertext=buses_df.apply(lambda row: f"Bus {int(row['BUS_NUMBER'])}<br>Voltage: {row['VM']:.3f} p.u.<br>Load: {row['PD']:.1f} MW<br>Base kV: {row['BASE_KV']:.0f}", axis=1),
        hovertemplate='%{hovertext}<extra></extra>',
        name='Buses'
    ))
    
    # Add transmission lines with alternating colors
    line_colors = ['#FF0000', '#0000FF', '#00CC00', '#9900FF', '#FFD700']  # Red, Blue, Green, Purple, Gold
    line_count = 0
    
    for idx, branch in enumerate(branches_df.iterrows()):
        branch = branch[1]  # Get the actual data
        from_bus_data = buses_df[buses_df['BUS_NUMBER'] == branch['From_Bus']]
        to_bus_data = buses_df[buses_df['BUS_NUMBER'] == branch['To_Bus']]
        
        if not from_bus_data.empty and not to_bus_data.empty:
            # Alternating colors based on index
            color_idx = idx % len(line_colors)
            line_color = line_colors[color_idx]
            
            # Line width and pattern based on loading
            loading_pct = (branch['MVA'] / branch['RATE']) * 100 if branch['RATE'] > 0 else 0
            line_width = 3
            line_dash = 'solid'
            if loading_pct > 90:
                line_width = 4
                line_dash = 'dash'
            
            fig.add_trace(go.Scatter(
                x=[from_bus_data.iloc[0]['x_coord'], to_bus_data.iloc[0]['x_coord']],
                y=[from_bus_data.iloc[0]['y_coord'], to_bus_data.iloc[0]['y_coord']],
                mode='lines',
                line=dict(color=line_color, width=line_width, dash=line_dash),
                opacity=0.8,
                hovertemplate=f'Line {int(branch["From_Bus"])}-{int(branch["To_Bus"])}<br>MVA: {branch["MVA"]:.1f}<br>Rating: {branch["RATE"]:.1f}<br>Loading: {loading_pct:.1f}%<extra></extra>',
                showlegend=False
            ))
            line_count += 1
    
    fig.update_layout(
        title=f"IEEE 118-Bus Power System - Grid Layout View ({line_count} lines shown)",
        xaxis_title="X Coordinate",
        yaxis_title="Y Coordinate",
        showlegend=True,
        height=700,
        template="plotly_white",
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False)
    )
    
    return fig

# Create radial layout visualization
def create_radial_layout_visualization():
    fig = go.Figure()

    # Group buses by voltage level
    buses_df['voltage_group'] = pd.cut(buses_df['BASE_KV'], 
                                    bins=[0, 100, 200, 300, 500, 1000],
                                    labels=['<100kV', '100-200kV', '200-300kV', '300-500kV', '>500kV'])
    
    # Set up radial coordinates based on voltage groups
    # Higher voltage buses closer to the center
    voltage_groups = buses_df['voltage_group'].unique()
    group_radii = {group: (4-i)*30 for i, group in enumerate(voltage_groups)}
    
    # Assign radial coordinates
    buses_df['theta'] = buses_df.groupby('voltage_group').cumcount() * (2*math.pi / buses_df.groupby('voltage_group').size().max())
    buses_df['r'] = buses_df['voltage_group'].map(group_radii)
    buses_df['x_radial'] = buses_df['r'] * np.cos(buses_df['theta'])
    buses_df['y_radial'] = buses_df['r'] * np.sin(buses_df['theta'])
    
    # Color mapping for voltage groups
    voltage_colors = {
        '<100kV': '#3498db',    # Blue
        '100-200kV': '#2ecc71', # Green
        '200-300kV': '#f1c40f', # Yellow
        '300-500kV': '#e67e22', # Orange
        '>500kV': '#e74c3c'     # Red
    }
    
    # Add circular areas for voltage groups
    for group, radius in group_radii.items():
        # Create circle outlines for each voltage group
        theta = np.linspace(0, 2*math.pi, 100)
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='lines',
            line=dict(color=voltage_colors.get(group, '#888888'), width=1, dash='dot'),
            name=f"{group} Region",
            hoverinfo='name'
        ))
    
    # Add buses as nodes
    for group in voltage_groups:
        group_buses = buses_df[buses_df['voltage_group'] == group]
        fig.add_trace(go.Scatter(
            x=group_buses['x_radial'],
            y=group_buses['y_radial'],
            mode='markers+text',
            marker=dict(
                size=group_buses['PD'] / 10 + 8,  # Size based on load
                color=voltage_colors.get(group, '#888888'),
                line=dict(width=1, color='#000000')
            ),
            text=group_buses['BUS_NUMBER'].astype(int).astype(str),
            textposition="middle center",
            textfont=dict(
                family="Arial",
                size=9,
                color="black"
            ),
            name=f"Buses ({group})",
            hovertext=group_buses.apply(
                lambda row: f"Bus {int(row['BUS_NUMBER'])}<br>Group: {row['voltage_group']}<br>Base kV: {row['BASE_KV']:.0f}<br>Voltage: {row['VM']:.3f} p.u.<br>Load: {row['PD']:.1f} MW", 
                axis=1
            ),
            hovertemplate='%{hovertext}<extra></extra>'
        ))
    
    # Add transmission lines with alternating colors
    line_colors = ['#FF0000', '#0000FF', '#00CC00', '#9900FF', '#FFD700']  # Red, Blue, Green, Purple, Gold
    line_count = 0
    
    # Create a list of buses with coordinates for faster lookup
    bus_coords = {}
    for _, row in buses_df.iterrows():
        bus_coords[row['BUS_NUMBER']] = (row['x_radial'], row['y_radial'])
    
    for idx, branch in enumerate(branches_df.iterrows()):
        branch = branch[1]
        if branch['From_Bus'] in bus_coords and branch['To_Bus'] in bus_coords:
            # Get coordinates
            x0, y0 = bus_coords[branch['From_Bus']]
            x1, y1 = bus_coords[branch['To_Bus']]
            
            # Alternating colors
            color_idx = idx % len(line_colors)
            line_color = line_colors[color_idx]
            
            # Line width and pattern based on loading
            loading_pct = (branch['MVA'] / branch['RATE']) * 100 if branch['RATE'] > 0 else 0
            line_width = 3
            line_dash = 'solid'
            if loading_pct > 90:
                line_width = 4
                line_dash = 'dash'
            
            fig.add_trace(go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode='lines',
                line=dict(color=line_color, width=line_width, dash=line_dash),
                opacity=0.8,
                hovertemplate=f'Line {int(branch["From_Bus"])}-{int(branch["To_Bus"])}<br>MVA: {branch["MVA"]:.1f}<br>Rating: {branch["RATE"]:.1f}<br>Loading: {loading_pct:.1f}%<extra></extra>',
                showlegend=False
            ))
            line_count += 1
    
    # Update layout
    fig.update_layout(
        title=f"IEEE 118-Bus Power System - Radial Layout View ({line_count} lines shown)",
        showlegend=True,
        height=700,
        template="plotly_white",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            title=''
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            title='',
            scaleanchor="x",
            scaleratio=1
        )
    )
    
    return fig

# App layout
app.layout = html.Div([
    # Layout selector and download button
    html.Div([
        html.Div([
            html.Label("Select Visualization Layout:"),
            dcc.Dropdown(
                id='layout-selector',
                options=[
                    {'label': 'Grid Layout', 'value': 'grid'},
                    {'label': 'Radial Layout', 'value': 'radial'}
                ],
                value='grid',
                style={'width': '250px'}
            )
        ], style={'display': 'inline-block', 'marginRight': '20px'}),
        
        html.Button("Download as SVG", id="download-button", className="btn")
    ], style={'marginBottom': '10px', 'padding': '10px', 'backgroundColor': '#f9f9f9', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-end'}),
    
    # Hidden div for storing the SVG data
    html.Div(id='svg-data', style={'display': 'none'}),
    
    # Header
    html.Div([
        html.H1("Power System Visualization - Fall 2025", style={'textAlign': 'center', 'color': '#2c3e50'}),
        html.H3("IEEE 118-Bus System with Multiple Layout Options", style={'textAlign': 'center', 'color': '#7f8c8d'})
    ], style={'margin': '20px', 'padding': '10px'}),
    
    # Main visualization
    html.Div([
        html.H2("IEEE 118-Bus System Visualization"),
        dcc.Graph(
            id='network-visualization',
            figure=create_grid_layout_visualization(),
            style={'height': '700px'}
        )
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': 'white', 'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'}),
    
    # Info card
    html.Div([
        html.H3("System Information:"),
        html.Ul([
            html.Li(f"✅ Total Buses: 118 (IEEE 118-bus system)"),
            html.Li(f"✅ Total Branches: {len(branches_df)} transmission lines"),
            html.Li("✅ Multiple visualization layouts available"),
            html.Li("✅ Fall 2025 update with improved features")
        ])
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#e8f5e8', 'borderRadius': '5px'})
])

# Add callbacks
@app.callback(
    Output('network-visualization', 'figure'),
    [Input('layout-selector', 'value')]
)
def update_visualization(selected_layout):
    if selected_layout == 'radial':
        return create_radial_layout_visualization()
    else:
        return create_grid_layout_visualization()

@app.callback(
    Output('svg-data', 'children'),
    [Input('download-button', 'n_clicks')],
    [Input('layout-selector', 'value')],
    prevent_initial_call=True
)
def download_svg(n_clicks, selected_layout):
    if n_clicks:
        # Get current timestamp for filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{selected_layout}_layout_{timestamp}.svg"
        
        # Create a larger figure for the download
        if selected_layout == 'radial':
            fig = create_radial_layout_visualization()
        else:
            fig = create_grid_layout_visualization()
        
        # Update figure size to be larger for the download
        fig.update_layout(
            width=1800,
            height=1600
        )
        
        # Create the downloadable content
        svg_data = fig.to_image(format="svg")
        
        # Create a data URL for the download
        b64_data = base64.b64encode(svg_data).decode()
        href = f"data:image/svg+xml;base64,{b64_data}"
        
        # Return a script to trigger download
        return html.Script(f'''
            var link = document.createElement('a');
            link.href = "{href}";
            link.download = "{filename}";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        ''')
    return None

# Run server directly using the more compatible approach
if __name__ == '__main__':
    print("🔌 Loading Power System Data...")
    
    # Try multiple ports in sequence
    ports = [8056, 8057, 8058, 8059, 8060]
    
    for port in ports:
        print(f"Trying to start server on port {port}...")
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', port))
            s.close()
            
            print(f"✅ Server starting on: http://127.0.0.1:{port}")
            app.run_server(host='127.0.0.1', port=port, debug=False)
            # If we get here, the server started successfully
            break
        except Exception as e:
            print(f"❌ Could not start on port {port}: {e}")
            continue
    else:
        print("❌ Failed to start server on any port. Please check if Dash is installed correctly.")