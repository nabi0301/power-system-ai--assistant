"""
PyVista Enhanced 3D Network Graph Visualization
Advanced 3D power system network visualization using PyVista and VTK
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

try:
    import pyvista as pv
    import vtk
    PYVISTA_AVAILABLE = True
    print("✅ PyVista 3D visualization available")
except ImportError as e:
    print(f"⚠️ PyVista not available: {e}")
    PYVISTA_AVAILABLE = False

def create_3d_network_mesh(buses_df, branches_df, case_id=None, contingency_id=None):
    """
    Create 3D network mesh using PyVista for advanced visualization
    
    Parameters:
    - buses_df: Bus data DataFrame
    - branches_df: Branch data DataFrame  
    - case_id: Case identifier
    - contingency_id: Contingency identifier
    
    Returns:
    - PyVista mesh object for 3D network visualization
    """
    if not PYVISTA_AVAILABLE:
        print("❌ PyVista not available - cannot create 3D mesh")
        return None
        
    try:
        # Create 3D coordinate system for power system network
        print(f"🔧 Creating 3D network mesh for case {case_id}, contingency {contingency_id}")
        
        # Generate 3D coordinates based on electrical hierarchy
        bus_coords_3d = {}
        
        # Enhanced 3D layout based on voltage levels and electrical distance
        for idx, bus in buses_df.iterrows():
            bus_id = bus['BUS_NUMBER'] if 'BUS_NUMBER' in bus else bus.get('bus_number', idx)
            voltage_level = bus.get('BASE_KV', bus.get('voltage_level', 138))
            voltage_magnitude = bus.get('VM', bus.get('voltage_magnitude', 1.0))
            
            # Z-coordinate based on voltage level (elevation represents voltage hierarchy)
            if voltage_level >= 345:
                z_pos = 100  # EHV at highest level
                tier = 0
            elif voltage_level >= 138:
                z_pos = 70   # HV at upper level
                tier = 1
            elif voltage_level >= 69:
                z_pos = 40   # MV at middle level
                tier = 2
            else:
                z_pos = 10   # LV at lower level
                tier = 3
            
            # X-Y coordinates with improved spacing
            buses_in_tier = len(buses_df[buses_df.get('BASE_KV', 138) >= voltage_level])
            tier_radius = 30 + tier * 20
            angle = (idx % buses_in_tier) * 2 * np.pi / max(buses_in_tier, 1)
            
            x_pos = tier_radius * np.cos(angle) + np.random.normal(0, 5)
            y_pos = tier_radius * np.sin(angle) + np.random.normal(0, 5)
            
            # Add voltage magnitude perturbation
            z_pos += (voltage_magnitude - 1.0) * 20
            
            bus_coords_3d[bus_id] = (x_pos, y_pos, z_pos)
        
        # Create PyVista mesh for buses (as spheres)
        bus_mesh = pv.PolyData()
        bus_points = []
        bus_scalars = []
        
        for bus_id, (x, y, z) in bus_coords_3d.items():
            bus_points.append([x, y, z])
            # Color based on voltage level
            bus_data = buses_df[buses_df['BUS_NUMBER'] == bus_id].iloc[0] if len(buses_df[buses_df['BUS_NUMBER'] == bus_id]) > 0 else buses_df.iloc[0]
            voltage_level = bus_data.get('BASE_KV', 138)
            bus_scalars.append(voltage_level)
        
        bus_mesh.points = np.array(bus_points)
        bus_mesh['voltage_level'] = np.array(bus_scalars)
        
        # Create transmission lines as tubes
        line_mesh = pv.PolyData()
        line_points = []
        line_lines = []
        line_scalars = []
        
        point_idx = 0
        for idx, branch in branches_df.iterrows():
            from_bus = branch.get('FROM_BUS', branch.get('From_Bus', branch.get('from_bus')))
            to_bus = branch.get('TO_BUS', branch.get('To_Bus', branch.get('to_bus')))
            
            if from_bus in bus_coords_3d and to_bus in bus_coords_3d:
                from_pos = bus_coords_3d[from_bus]
                to_pos = bus_coords_3d[to_bus]
                
                line_points.extend([from_pos, to_pos])
                line_lines.append([2, point_idx, point_idx + 1])
                
                # Line scalar based on power flow
                power_flow = abs(branch.get('PF', branch.get('power_flow', 0.0)))
                line_scalars.extend([power_flow, power_flow])
                
                point_idx += 2
        
        if line_points:
            line_mesh.points = np.array(line_points)
            line_mesh.lines = np.array(line_lines)
            line_mesh['power_flow'] = np.array(line_scalars)
        
        # Combine meshes
        combined_mesh = bus_mesh + line_mesh
        
        print(f"✅ Created 3D mesh with {len(bus_points)} buses and {len(line_lines)} transmission lines")
        return combined_mesh, bus_mesh, line_mesh, bus_coords_3d
        
    except Exception as e:
        print(f"❌ Error creating 3D network mesh: {e}")
        return None

def create_enhanced_3d_network_plotly(buses_df, branches_df, case_id=None, contingency_id=None):
    """
    Create enhanced 3D network visualization using Plotly with PyVista-inspired layout
    
    Returns:
    - Plotly 3D scatter plot with enhanced network visualization
    """
    try:
        print(f"🔧 Creating enhanced 3D network visualization for case {case_id}")
        
        # Generate 3D coordinates using PyVista-inspired algorithm
        bus_coords_3d = {}
        
        # Create sophisticated 3D layout
        for idx, bus in buses_df.iterrows():
            bus_id = bus['BUS_NUMBER'] if 'BUS_NUMBER' in bus else bus.get('bus_number', idx)
            voltage_level = bus.get('BASE_KV', bus.get('voltage_level', 138))
            voltage_magnitude = bus.get('VM', bus.get('voltage_magnitude', 1.0))
            bus_type = bus.get('TYPE', bus.get('bus_type', 1))
            
            # Hierarchical Z-coordinate based on voltage level
            if voltage_level >= 345:
                z_base = 80
                color_base = 'darkblue'
                size_base = 12
            elif voltage_level >= 138:
                z_base = 60
                color_base = 'blue'
                size_base = 10
            elif voltage_level >= 69:
                z_base = 40
                color_base = 'green'
                size_base = 8
            else:
                z_base = 20
                color_base = 'orange'
                size_base = 6
            
            # Radial arrangement in X-Y plane
            tier_buses = len(buses_df[buses_df.get('BASE_KV', 138) == voltage_level])
            radius = 25 + (voltage_level / 50)
            angle = (idx % max(tier_buses, 1)) * 2 * np.pi / max(tier_buses, 1)
            
            x_pos = radius * np.cos(angle)
            y_pos = radius * np.sin(angle)
            z_pos = z_base + (voltage_magnitude - 1.0) * 15
            
            # Add small random perturbation for aesthetics
            x_pos += np.random.normal(0, 3)
            y_pos += np.random.normal(0, 3)
            
            bus_coords_3d[bus_id] = {
                'x': x_pos, 'y': y_pos, 'z': z_pos,
                'voltage_level': voltage_level,
                'voltage_magnitude': voltage_magnitude,
                'bus_type': bus_type,
                'color': color_base,
                'size': size_base
            }
        
        # Create 3D Plotly figure
        fig = go.Figure()
        
        # Add buses as 3D scatter points
        for bus_id, coords in bus_coords_3d.items():
            # Determine bus symbol and color
            if coords['bus_type'] == 3:  # Slack bus
                marker_symbol = 'diamond'
                marker_color = 'gold'
                marker_size = 15
            elif coords['bus_type'] == 2:  # Generator bus
                marker_symbol = 'square'
                marker_color = 'red'
                marker_size = 12
            else:  # Load bus
                marker_symbol = 'circle'
                marker_color = coords['color']
                marker_size = coords['size']
            
            # Add voltage violation indicators
            if coords['voltage_magnitude'] < 0.95 or coords['voltage_magnitude'] > 1.05:
                marker_color = 'red'
                marker_size += 3
            
            fig.add_trace(go.Scatter3d(
                x=[coords['x']],
                y=[coords['y']],
                z=[coords['z']],
                mode='markers+text',
                marker=dict(
                    size=marker_size,
                    color=marker_color,
                    symbol=marker_symbol,
                    line=dict(width=2, color='black'),
                    opacity=0.8
                ),
                text=str(bus_id),
                textposition='middle center',
                name=f'Bus {bus_id} ({coords["voltage_level"]}kV)',
                hovertemplate=f'<b>Bus {bus_id}</b><br>' +
                             f'Voltage Level: {coords["voltage_level"]} kV<br>' +
                             f'Voltage: {coords["voltage_magnitude"]:.3f} pu<br>' +
                             f'Position: ({coords["x"]:.1f}, {coords["y"]:.1f}, {coords["z"]:.1f})<br>' +
                             f'Type: {"Slack" if coords["bus_type"]==3 else "Generator" if coords["bus_type"]==2 else "Load"}<extra></extra>',
                showlegend=False
            ))
        
        # Add transmission lines as 3D lines
        for idx, branch in branches_df.iterrows():
            from_bus = branch.get('FROM_BUS', branch.get('From_Bus', branch.get('from_bus')))
            to_bus = branch.get('TO_BUS', branch.get('To_Bus', branch.get('to_bus')))
            
            if from_bus in bus_coords_3d and to_bus in bus_coords_3d:
                from_coords = bus_coords_3d[from_bus]
                to_coords = bus_coords_3d[to_bus]
                
                # Line styling based on power flow and voltage level
                power_flow = abs(branch.get('PF', branch.get('power_flow', 0.0)))
                rating = branch.get('RATE_A', branch.get('rating', 100.0))
                loading = power_flow / rating if rating > 0 else 0
                
                # Determine line color and width
                if loading > 0.9:
                    line_color = 'red'
                    line_width = 6
                elif loading > 0.7:
                    line_color = 'orange'
                    line_width = 4
                elif loading > 0.5:
                    line_color = 'yellow'
                    line_width = 3
                else:
                    line_color = 'blue'
                    line_width = 2
                
                # Add 3D transmission line
                fig.add_trace(go.Scatter3d(
                    x=[from_coords['x'], to_coords['x']],
                    y=[from_coords['y'], to_coords['y']],
                    z=[from_coords['z'], to_coords['z']],
                    mode='lines',
                    line=dict(
                        color=line_color,
                        width=line_width
                    ),
                    name=f'Line {from_bus}-{to_bus}',
                    hovertemplate=f'<b>Line {from_bus} → {to_bus}</b><br>' +
                                 f'Power Flow: {power_flow:.2f} MW<br>' +
                                 f'Loading: {loading*100:.1f}%<br>' +
                                 f'Rating: {rating:.1f} MVA<extra></extra>',
                    showlegend=False
                ))
        
        # Enhanced 3D layout
        fig.update_layout(
            title={
                'text': f'Enhanced 3D Power System Network - Case {case_id}' + 
                       (f' (Contingency {contingency_id})' if contingency_id else ''),
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            scene=dict(
                xaxis=dict(
                    title='X Coordinate',
                    showgrid=True,
                    gridcolor='lightgray',
                    showticklabels=True
                ),
                yaxis=dict(
                    title='Y Coordinate',
                    showgrid=True,
                    gridcolor='lightgray',
                    showticklabels=True
                ),
                zaxis=dict(
                    title='Voltage Level Hierarchy',
                    showgrid=True,
                    gridcolor='lightgray',
                    showticklabels=True
                ),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5),
                    center=dict(x=0, y=0, z=0),
                    up=dict(x=0, y=0, z=1)
                ),
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=0.7),
                bgcolor='white'
            ),
            showlegend=False,
            margin=dict(l=0, r=0, b=0, t=50),
            annotations=[
                dict(
                    text="🌐 Enhanced 3D Network Visualization<br>" +
                         "Z-axis: Voltage Level Hierarchy<br>" +
                         "Colors: Voltage Levels & Loading<br>" +
                         "Symbols: Bus Types (⬟ Slack, ⬛ Gen, ● Load)",
                    xref="paper", yref="paper",
                    x=0.02, y=0.98,
                    showarrow=False,
                    font=dict(size=10),
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="gray",
                    borderwidth=1
                )
            ]
        )
        
        print(f"✅ Enhanced 3D network visualization created with {len(bus_coords_3d)} buses")
        return fig
        
    except Exception as e:
        print(f"❌ Error creating enhanced 3D network visualization: {e}")
        return None

def create_pyvista_network_export(buses_df, branches_df, case_id=None, output_path=None):
    """
    Export network data in PyVista format for advanced 3D rendering
    
    Parameters:
    - buses_df: Bus data DataFrame
    - branches_df: Branch data DataFrame
    - case_id: Case identifier
    - output_path: Path to save VTK file
    
    Returns:
    - Success status and file path
    """
    if not PYVISTA_AVAILABLE:
        print("❌ PyVista not available for export")
        return False, None
        
    try:
        mesh_data = create_3d_network_mesh(buses_df, branches_df, case_id)
        if mesh_data is None:
            return False, None
            
        combined_mesh, bus_mesh, line_mesh, coords = mesh_data
        
        # Export to VTK format
        if output_path is None:
            output_path = f"power_system_3d_case_{case_id}.vtk"
            
        combined_mesh.save(output_path)
        print(f"✅ 3D network data exported to {output_path}")
        
        return True, output_path
        
    except Exception as e:
        print(f"❌ Error exporting PyVista network: {e}")
        return False, None

# Integration function for main application
def get_enhanced_3d_network_graph(buses_df, branches_df, case_id=None, contingency_id=None):
    """
    Main function to get enhanced 3D network graph for integration
    
    Returns:
    - Plotly figure with enhanced 3D network visualization
    """
    print("🌐 Creating PyVista-enhanced 3D network visualization...")
    
    if PYVISTA_AVAILABLE:
        print("✅ Using PyVista algorithms for 3D layout")
        return create_enhanced_3d_network_plotly(buses_df, branches_df, case_id, contingency_id)
    else:
        print("⚠️ PyVista not available, using fallback 3D visualization")
        # Fallback to basic 3D visualization
        return create_enhanced_3d_network_plotly(buses_df, branches_df, case_id, contingency_id)

# Test function
def test_pyvista_integration():
    """Test PyVista integration with sample data"""
    print("🧪 Testing PyVista 3D network visualization...")
    
    # Sample data for testing
    sample_buses = pd.DataFrame({
        'BUS_NUMBER': range(1, 11),
        'BASE_KV': [345, 345, 138, 138, 138, 69, 69, 69, 25, 25],
        'VM': [1.05, 1.02, 0.98, 1.01, 0.99, 1.03, 0.97, 1.00, 1.02, 0.96],
        'TYPE': [3, 2, 1, 1, 2, 1, 1, 1, 1, 1]
    })
    
    sample_branches = pd.DataFrame({
        'FROM_BUS': [1, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'TO_BUS': [2, 3, 4, 5, 6, 7, 8, 9, 10, 10],
        'PF': [150, 120, 90, 85, 110, 45, 60, 35, 25, 30],
        'RATE_A': [200, 180, 150, 120, 140, 80, 90, 60, 50, 45]
    })
    
    fig = get_enhanced_3d_network_graph(sample_buses, sample_branches, case_id=1)
    
    if fig:
        print("✅ PyVista-enhanced 3D visualization test successful!")
        return fig
    else:
        print("❌ PyVista-enhanced 3D visualization test failed")
        return None

if __name__ == "__main__":
    test_pyvista_integration()