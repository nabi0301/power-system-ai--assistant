import pandas as pd
import sqlite3
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
import importlib.util
import re

def create_network_comparison(case_id, contingency_id=None):
    """
    Create a comparison view with 4 network graphs showing base case, contingency case, SLR, and DLR
    
    Parameters:
    -----------
    case_id : int
        The base case ID to visualize
    contingency_id : int or None
        The contingency case ID to visualize. If None, will show only base case comparison.
    
    Returns:
    --------
    plotly.graph_objects.Figure
        The comparison figure with 4 subplots
        
    Note:
    -----
    Checks for data availability across all four cases and provides clear feedback if data is missing.
    """
    try:
        # Use the direct network integration module if available
        try:
            from direct_network_integration import import_data_viz_fall
            data_viz_fall = import_data_viz_fall()
            if data_viz_fall is not None:
                print("✅ Successfully imported data_viz_fall using direct_network_integration")
        except ImportError:
            # Fall back to manual import if direct integration is not available
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_viz_fall_path = os.path.join(current_dir, 'data_viz_fall.py')
            
            if not os.path.exists(data_viz_fall_path):
                print(f"❌ Error: data_viz_fall.py not found at {data_viz_fall_path}")
                return go.Figure(layout={"title": "Error: data_viz_fall.py not found"})
                
            # Import create_network_graph from data_viz_fall.py
            spec = importlib.util.spec_from_file_location("data_viz_fall", data_viz_fall_path)
            data_viz_fall = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(data_viz_fall)
            
            if not hasattr(data_viz_fall, 'create_network_graph'):
                print("❌ Error: create_network_graph function not found in data_viz_fall.py")
                return go.Figure(layout={"title": "Error: create_network_graph function not found"})
                
            print("✅ Successfully imported create_network_graph from data_viz_fall.py")
        
        # Connect to database and load data
        conn = sqlite3.connect('data.db')
        
        # Dictionary to track data availability for each case
        data_available = {
            'base_case': False,
            'contingency_case': False,
            'slr_case': False,
            'dlr_case': False
        }
        
        # 1. Get Base Case Data
        base_buses_query = f"SELECT * FROM BaseBusData WHERE base_case_id = {case_id}"
        base_branches_query = f"SELECT * FROM BaseBranchData WHERE base_case_id = {case_id}"
        
        base_buses = pd.read_sql_query(base_buses_query, conn)
        base_branches = pd.read_sql_query(base_branches_query, conn)
        
        # Check if base case data is available
        data_available['base_case'] = not base_buses.empty and not base_branches.empty
        
        # Add coordinates for visualization
        if 'x_coord' not in base_buses.columns or 'y_coord' not in base_buses.columns:
            base_buses['x_coord'] = (base_buses['BUS_NUMBER'] % 12) * 30
            base_buses['y_coord'] = (base_buses['BUS_NUMBER'] // 12) * 25
            
        # 2. Get Contingency Case Data (if requested)
        if contingency_id is not None:
            cont_buses_query = f"""
                SELECT * FROM ContingencyBusData 
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            """
            cont_branches_query = f"""
                SELECT * FROM ContingencyBranchData 
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            """
            
            cont_buses = pd.read_sql_query(cont_buses_query, conn)
            cont_branches = pd.read_sql_query(cont_branches_query, conn)
            
            # Check if contingency case data is available
            data_available['contingency_case'] = not cont_buses.empty and not cont_branches.empty
            
            # Add coordinates for visualization
            if not cont_buses.empty and ('x_coord' not in cont_buses.columns or 'y_coord' not in cont_buses.columns):
                cont_buses['x_coord'] = (cont_buses['BUS_NUMBER'] % 12) * 30
                cont_buses['y_coord'] = (cont_buses['BUS_NUMBER'] // 12) * 25
        else:
            # If no contingency specified, use base case data for contingency subplot
            cont_buses = base_buses.copy()
            cont_branches = base_branches.copy()
            data_available['contingency_case'] = data_available['base_case']
            
        # 3. Get SLR Data
        slr_buses_query = f"""
            SELECT * FROM BaseBusData WHERE base_case_id = {case_id}
        """
        slr_branches_query = f"""
            SELECT * FROM SLR_Branches 
            WHERE base_case_id = {case_id}
            {f"AND contingency_case_id = {contingency_id}" if contingency_id is not None else ""}
        """
        
        slr_buses = pd.read_sql_query(slr_buses_query, conn)
        slr_branches = pd.read_sql_query(slr_branches_query, conn)
        
        # Check if SLR data is available
        data_available['slr_case'] = not slr_buses.empty and not slr_branches.empty
        
        # Add coordinates for visualization
        if not slr_buses.empty and ('x_coord' not in slr_buses.columns or 'y_coord' not in slr_buses.columns):
            slr_buses['x_coord'] = (slr_buses['BUS_NUMBER'] % 12) * 30
            slr_buses['y_coord'] = (slr_buses['BUS_NUMBER'] // 12) * 25
            
        # 4. Get DLR Data
        dlr_buses_query = f"""
            SELECT * FROM BaseBusData WHERE base_case_id = {case_id}
        """
        dlr_branches_query = f"""
            SELECT * FROM DLR_Branches 
            WHERE base_case_id = {case_id}
            {f"AND contingency_case_id = {contingency_id}" if contingency_id is not None else ""}
        """
        
        dlr_buses = pd.read_sql_query(dlr_buses_query, conn)
        dlr_branches = pd.read_sql_query(dlr_branches_query, conn)
        
        # Check if DLR data is available
        data_available['dlr_case'] = not dlr_buses.empty and not dlr_branches.empty
        
        # Add coordinates for visualization
        if not dlr_buses.empty and ('x_coord' not in dlr_buses.columns or 'y_coord' not in dlr_buses.columns):
            dlr_buses['x_coord'] = (dlr_buses['BUS_NUMBER'] % 12) * 30
            dlr_buses['y_coord'] = (dlr_buses['BUS_NUMBER'] // 12) * 25
            
        # Log data availability
        print(f"Data availability for case {case_id}, contingency {contingency_id}:")
        print(f"  - Base case: {'✅ Available' if data_available['base_case'] else '❌ Missing'}")
        print(f"  - Contingency case: {'✅ Available' if data_available['contingency_case'] else '❌ Missing'}")
        print(f"  - SLR case: {'✅ Available' if data_available['slr_case'] else '❌ Missing'}")
        print(f"  - DLR case: {'✅ Available' if data_available['dlr_case'] else '❌ Missing'}")
            
        # Get tripped branch info for contingency cases
        tripped_branch_info = None
        if contingency_id is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT tripped_branch, from_bus, to_bus 
                    FROM contingency_info 
                    WHERE base_case_id = ? AND contingency_id = ?
                """, (case_id, contingency_id))
                result = cursor.fetchone()
                
                if result:
                    tripped_branch_info = {
                        'branch_id': result[0],
                        'from_bus': result[1],
                        'to_bus': result[2]
                    }
            except Exception as e:
                print(f"Error getting tripped branch info: {e}")
                
        # Close database connection
        conn.close()
        
        # Get min and max load for consistent color scaling
        all_branches = pd.concat([base_branches, cont_branches, slr_branches, dlr_branches])
        min_load = 0
        max_load = 100
        
        # Try to get loading percentage
        if 'LOADING_PERCENT' in all_branches.columns:
            min_load = all_branches['LOADING_PERCENT'].min()
            max_load = all_branches['LOADING_PERCENT'].max()
        elif 'LOADING' in all_branches.columns:
            min_load = all_branches['LOADING'].min()
            max_load = all_branches['LOADING'].max()
        elif 'MVA' in all_branches.columns and 'RATE' in all_branches.columns:
            # Calculate loading percentage
            all_branches['loading_pct'] = all_branches['MVA'] / all_branches['RATE'] * 100
            min_load = all_branches['loading_pct'].min()
            max_load = all_branches['loading_pct'].max()
            
        # Make sure we have reasonable values
        min_load = max(0, min_load if not pd.isna(min_load) else 0)
        max_load = min(150, max_load if not pd.isna(max_load) else 100)
        
        # Create subplot titles
        base_title = f"Base Case {case_id}"
        contingency_title = f"Contingency {contingency_id}" if contingency_id is not None else "Base Case"
        slr_title = "SLR" + (f" (Contingency {contingency_id})" if contingency_id is not None else "")
        dlr_title = "DLR" + (f" (Contingency {contingency_id})" if contingency_id is not None else "")
        
        # Check overall data availability and provide feedback
        missing_data = [key for key, available in data_available.items() if not available]
        if len(missing_data) > 0:
            print(f"Warning: Missing data for {len(missing_data)} case types: {', '.join(missing_data)}")
            
            # If all data is missing, return an error figure
            if len(missing_data) == 4:
                error_msg = f"No data available for any of the requested case types (case {case_id}"
                if contingency_id is not None:
                    error_msg += f", contingency {contingency_id}"
                error_msg += ")"
                print(f"Error: {error_msg}")
                return go.Figure(layout={"title": error_msg})
        
        # Create the comparison figure using subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[base_title, contingency_title, slr_title, dlr_title],
            specs=[[{'type': 'xy'}, {'type': 'xy'}],
                   [{'type': 'xy'}, {'type': 'xy'}]],
            vertical_spacing=0.1,
            horizontal_spacing=0.05
        )
        
        # Function to create a "data not available" figure
        def create_missing_data_figure(title, case_type):
            missing_fig = go.Figure()
            missing_fig.add_annotation(
                text=f"Data not available for {case_type}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            return missing_fig
        
        # Create individual network plots using data_viz_fall's create_network_graph function
        try:
            # Base Case
            if data_available['base_case']:
                base_fig = data_viz_fall.create_network_graph(
                    base_buses, base_branches, base_title, min_load, max_load, case_id
                )
            else:
                base_fig = create_missing_data_figure(base_title, "Base Case")
                
            # Contingency Case
            if data_available['contingency_case']:
                contingency_fig = data_viz_fall.create_network_graph(
                    cont_buses, cont_branches, contingency_title, min_load, max_load, 
                    case_id, tripped_branch_info=tripped_branch_info
                )
            else:
                contingency_fig = create_missing_data_figure(contingency_title, "Contingency Case")
                
            # SLR Case
            if data_available['slr_case']:
                slr_fig = data_viz_fall.create_network_graph(
                    slr_buses, slr_branches, slr_title, min_load, max_load, case_id
                )
            else:
                slr_fig = create_missing_data_figure(slr_title, "SLR Case")
                
            # DLR Case
            if data_available['dlr_case']:
                dlr_fig = data_viz_fall.create_network_graph(
                    dlr_buses, dlr_branches, dlr_title, min_load, max_load, case_id
                )
            else:
                dlr_fig = create_missing_data_figure(dlr_title, "DLR Case")
            
            # Add each figure's traces to the subplots
            for trace in base_fig.data:
                fig.add_trace(trace, row=1, col=1)
                
            for trace in contingency_fig.data:
                fig.add_trace(trace, row=1, col=2)
                
            for trace in slr_fig.data:
                fig.add_trace(trace, row=2, col=1)
                
            for trace in dlr_fig.data:
                fig.add_trace(trace, row=2, col=2)
                
        except Exception as e:
            print(f"Error creating network comparison subplots: {e}")
            return go.Figure(layout={"title": f"Error creating network comparison: {str(e)}"})
            
        # Update layout for overall comparison
        comparison_title = f"Network Comparison: Case {case_id}"
        if contingency_id is not None:
            comparison_title += f", Contingency {contingency_id}"
            
        # Add data availability information to the title
        if missing_data:
            available_data = [key.replace('_case', '').upper() for key, available in data_available.items() if available]
            comparison_title += f" (Available data: {', '.join(available_data)})"
        
        # Add a common legend for all subplots to make violation detection clear
        # For consistency with the enhanced violation detection added to data_viz_fall.py
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color="rgb(255, 0, 0)", width=8),
                name="Violations (>100% Loading)",
                showlegend=True
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color="rgb(255, 165, 0)", width=7),
                name="Warning (>90% Loading)",
                showlegend=True
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color="rgb(0, 128, 0)", width=4),
                name="Normal Operation",
                showlegend=True
            )
        )
            
        fig.update_layout(
            title_text=comparison_title,
            height=900,  # Taller to accommodate 4 subplots
            width=1200,
            template='plotly_white',
            legend=dict(
                title="Network Elements",
                orientation="h",
                yanchor="bottom",
                y=-0.05,  # Position slightly higher to accommodate the added legend items
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.5)",
                borderwidth=1
            )
        )
        
        # Use the same axis ranges for all subplots for consistency
        x_min = min(base_buses['x_coord'].min(), cont_buses['x_coord'].min(), 
                   slr_buses['x_coord'].min(), dlr_buses['x_coord'].min())
        x_max = max(base_buses['x_coord'].max(), cont_buses['x_coord'].max(),
                   slr_buses['x_coord'].max(), dlr_buses['x_coord'].max())
        y_min = min(base_buses['y_coord'].min(), cont_buses['y_coord'].min(),
                   slr_buses['y_coord'].min(), dlr_buses['y_coord'].min())
        y_max = max(base_buses['y_coord'].max(), cont_buses['y_coord'].max(),
                   slr_buses['y_coord'].max(), dlr_buses['y_coord'].max())
                   
        # Add some padding
        x_padding = (x_max - x_min) * 0.1
        y_padding = (y_max - y_min) * 0.1
        
        # Set the same range for all subplots
        fig.update_xaxes(range=[x_min-x_padding, x_max+x_padding])
        fig.update_yaxes(range=[y_min-y_padding, y_max+y_padding])
        
        # Add annotations explaining the comparison
        fig.add_annotation(
            text="Compare base case topology with contingency scenario and rating methods",
            xref="paper", yref="paper",
            x=0.5, y=1.05,
            showarrow=False,
            font=dict(size=14)
        )
        
        return fig
    
    except Exception as e:
        print(f"Error in create_network_comparison: {str(e)}")
        return go.Figure(layout={"title": f"Error creating network comparison: {str(e)}"})