#!/usr/bin/env python3
"""
Network Comparison Visualizer
Creates side-by-side network graphs showing base case vs contingency case
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sqlite3
import traceback

def create_network_comparison_dual(case_id, contingency_id=None):
    """
    Create side-by-side network graphs: Base Case and Contingency Case
    
    Parameters:
    -----------
    case_id : int
        The case ID to visualize
    contingency_id : int or None
        The contingency ID to compare against base case
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Figure with 2 subplots (base case and contingency)
    """
    
    try:
        # Import the network graph creator
        try:
            from direct_network_integration import create_network_graph
            print("✅ Loaded direct_network_integration for dual network view")
        except ImportError:
            print("⚠️ direct_network_integration not available, using fallback")
            return create_fallback_dual_network(case_id, contingency_id)
        
        # Create subplot figure
        if contingency_id is not None:
            # Side-by-side: Base Case and Contingency
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=(
                    f"Base Case {case_id}",
                    f"Contingency {contingency_id} (Case {case_id})"
                ),
                specs=[[{"type": "scatter"}, {"type": "scatter"}]],
                horizontal_spacing=0.1
            )
            
            print(f"📊 Creating dual network view: Base Case {case_id} vs Contingency {contingency_id}")
            
            # To ensure consistent positions, we'll use the enhanced dual network graph module if available
            try:
                from network_graph_dual_view import create_dual_network_graph
                print("✅ Using enhanced dual network graph with consistent positions")
                enhanced_fig = create_dual_network_graph(case_id, contingency_id)
                return enhanced_fig
            except ImportError:
                print("⚠️ Enhanced dual network graph not available, falling back to individual graphs")
                pass
            
            # Generate base case graph
            try:
                base_graph = create_network_graph(case_id, None)
                
                # Add all traces from base graph to first subplot
                for trace in base_graph.data:
                    trace_copy = go.Scatter(trace)
                    trace_copy.showlegend = False
                    fig.add_trace(trace_copy, row=1, col=1)
                
                print(f"✅ Added base case graph ({len(base_graph.data)} traces)")
            except Exception as e:
                print(f"❌ Error creating base case graph: {e}")
                traceback.print_exc()
            
            # Generate contingency graph
            try:
                cont_graph = create_network_graph(case_id, contingency_id)
                
                # Add all traces from contingency graph to second subplot
                for trace in cont_graph.data:
                    trace_copy = go.Scatter(trace)
                    trace_copy.showlegend = False
                    fig.add_trace(trace_copy, row=1, col=2)
                
                print(f"✅ Added contingency graph ({len(cont_graph.data)} traces)")
            except Exception as e:
                print(f"❌ Error creating contingency graph: {e}")
                traceback.print_exc()
            
            # Update layout
            fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
            fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
            fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=2)
            fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=2)
            
            fig.update_layout(
                title=f"Network Comparison: Base Case {case_id} vs Contingency {contingency_id}",
                height=800,
                showlegend=False,
                hovermode='closest',
                margin=dict(l=20, r=20, t=60, b=20)
            )
            
        else:
            # No contingency - just show base case (single plot)
            print(f"📊 Creating single network view: Base Case {case_id}")
            fig = create_network_graph(case_id, None)
        
        return fig
    
    except Exception as e:
        print(f"❌ Error in create_network_comparison_dual: {e}")
        traceback.print_exc()
        
        # Return error figure
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error creating network comparison:<br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(title="Network Graph Error", height=600)
        return fig


def create_fallback_dual_network(case_id, contingency_id):
    """
    Fallback function for dual network visualization using simple scatter plots
    """
    try:
        # Connect to database
        conn = sqlite3.connect('data.db')
        
        # Load base case data
        base_buses = pd.read_sql_query(f"""
            SELECT BUS_NUMBER, VM, PG, PD
            FROM BaseBusData
            WHERE base_case_id = {case_id}
        """, conn)
        
        base_branches = pd.read_sql_query(f"""
            SELECT From_Bus, To_Bus, MVA, RATE
            FROM BaseBranchData
            WHERE base_case_id = {case_id}
        """, conn)
        
        if contingency_id is not None:
            # Load contingency data
            cont_buses = pd.read_sql_query(f"""
                SELECT bus_number as BUS_NUMBER, VM, PG, PD
                FROM ContingencyBusData
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            """, conn)
            
            cont_branches = pd.read_sql_query(f"""
                SELECT From_Bus, To_Bus, MVA, RATE
                FROM ContingencyBranchData
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            """, conn)
            
            conn.close()
            
            # Create side-by-side plots
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=(f"Base Case {case_id}", f"Contingency {contingency_id}"),
                specs=[[{"type": "scatter"}, {"type": "scatter"}]]
            )
            
            # Add base case nodes
            base_buses['x'] = (base_buses['BUS_NUMBER'] % 12) * 30
            base_buses['y'] = (base_buses['BUS_NUMBER'] // 12) * 25
            
            fig.add_trace(go.Scatter(
                x=base_buses['x'],
                y=base_buses['y'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=base_buses['VM'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Voltage (p.u.)", x=0.45)
                ),
                text=[f"Bus {int(row['BUS_NUMBER'])}<br>V={row['VM']:.3f}" 
                      for _, row in base_buses.iterrows()],
                hoverinfo='text',
                name="Base Case Buses",
                showlegend=False
            ), row=1, col=1)
            
            # Add contingency nodes
            cont_buses['x'] = (cont_buses['BUS_NUMBER'] % 12) * 30
            cont_buses['y'] = (cont_buses['BUS_NUMBER'] // 12) * 25
            
            fig.add_trace(go.Scatter(
                x=cont_buses['x'],
                y=cont_buses['y'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=cont_buses['VM'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Voltage (p.u.)", x=1.02)
                ),
                text=[f"Bus {int(row['BUS_NUMBER'])}<br>V={row['VM']:.3f}" 
                      for _, row in cont_buses.iterrows()],
                hoverinfo='text',
                name="Contingency Buses",
                showlegend=False
            ), row=1, col=2)
            
            fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
            fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
            
            fig.update_layout(
                title=f"Network Comparison: Base Case {case_id} vs Contingency {contingency_id}",
                height=800,
                hovermode='closest'
            )
            
        else:
            # Single base case only
            conn.close()
            
            fig = go.Figure()
            
            base_buses['x'] = (base_buses['BUS_NUMBER'] % 12) * 30
            base_buses['y'] = (base_buses['BUS_NUMBER'] // 12) * 25
            
            fig.add_trace(go.Scatter(
                x=base_buses['x'],
                y=base_buses['y'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=base_buses['VM'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Voltage (p.u.)")
                ),
                text=[f"Bus {int(row['BUS_NUMBER'])}<br>V={row['VM']:.3f}" 
                      for _, row in base_buses.iterrows()],
                hoverinfo='text'
            ))
            
            fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
            fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
            
            fig.update_layout(
                title=f"Network Graph: Base Case {case_id}",
                height=800,
                hovermode='closest'
            )
        
        return fig
    
    except Exception as e:
        print(f"❌ Error in fallback dual network: {e}")
        traceback.print_exc()
        
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error creating network graph:<br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        return fig


if __name__ == "__main__":
    # Test the dual network view
    print("Testing dual network view...")
    fig = create_network_comparison_dual(0, 1)
    print(f"✅ Created figure with {len(fig.data)} traces")
    print("Test complete!")
