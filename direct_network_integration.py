#!/usr/bin/env python3
"""
Direct Network Graph Integration Module

This module provides direct integration between power_viz_with_database.py and data_viz_fall.py
to ensure network graphs are properly displayed in the application.
"""

import importlib.util
import os
import sys
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import traceback
from functools import lru_cache

# Try to import the dynamic case management module
try:
    from dynamic_case_management import validate_case_id, get_first_available_case_id
    DYNAMIC_CASE_MANAGEMENT_AVAILABLE = True
except ImportError:
    print("⚠️ dynamic_case_management module not available")
    DYNAMIC_CASE_MANAGEMENT_AVAILABLE = False

# Cache for database queries - significantly speeds up repeated requests
@lru_cache(maxsize=128)
def _fetch_case_data_cached(case_id, contingency_id):
    """
    Internal cached version of fetch_case_data
    Returns pickled dataframes that can be cached
    """
    try:
        # Connect to database
        conn = sqlite3.connect('data.db')
        
        # Determine which tables to query based on contingency_id
        if contingency_id is not None:
            # Get contingency case data - select only needed columns for performance
            buses_query = f"""
                SELECT BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD, Bus_Name
                FROM ContingencyBusData 
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            """
            branches_query = f"""
                SELECT From_Bus, To_Bus, PF, QF, PT, QT, MVA, RATE, Ckt_ID
                FROM ContingencyBranchData 
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
            """
            title = f"Contingency {contingency_id} (Case {case_id})"
        else:
            # Get base case data - select only needed columns
            buses_query = f"""
                SELECT BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD, Bus_Name
                FROM BaseBusData 
                WHERE base_case_id = {case_id}
            """
            branches_query = f"""
                SELECT From_Bus, To_Bus, PF, QF, PT, QT, MVA, RATE, Ckt_ID
                FROM BaseBranchData 
                WHERE base_case_id = {case_id}
            """
            title = f"Base Case {case_id}"
        
        # Execute queries
        buses_df = pd.read_sql_query(buses_query, conn)
        branches_df = pd.read_sql_query(branches_query, conn)
        
        # Close connection
        conn.close()
        
        return buses_df, branches_df, title
        
    except Exception as e:
        print(f"❌ Error in _fetch_case_data_cached: {e}")
        traceback.print_exc()
        return None, None, None

def import_data_viz_fall():
    """Import the data_viz_fall module dynamically"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_viz_fall_path = os.path.join(current_dir, 'data_viz_fall.py')
        
        if not os.path.exists(data_viz_fall_path):
            print(f"❌ Error: data_viz_fall.py not found at {data_viz_fall_path}")
            return None
        
        # Import create_network_graph from data_viz_fall.py
        spec = importlib.util.spec_from_file_location("data_viz_fall", data_viz_fall_path)
        data_viz_fall = importlib.util.module_from_spec(spec)
        sys.modules["data_viz_fall"] = data_viz_fall  # Add to sys.modules to make it importable
        spec.loader.exec_module(data_viz_fall)
        
        # Verify the create_network_graph function exists
        if not hasattr(data_viz_fall, 'create_network_graph'):
            print("❌ Error: create_network_graph function not found in data_viz_fall.py")
            return None
            
        print("✅ Successfully imported data_viz_fall module")
        return data_viz_fall
    except Exception as e:
        print(f"❌ Error importing data_viz_fall module: {e}")
        traceback.print_exc()
        return None

def fetch_case_data(case_id, contingency_id=None):
    """
    Fetch case data from the database - uses caching for performance
    
    Parameters:
    -----------
    case_id : int
        The case ID to fetch
    contingency_id : int or None
        The contingency ID to fetch, or None for base case
        
    Returns:
    --------
    tuple
        (buses_df, branches_df, title, min_load, max_load)
    """
    try:
        # Validate and prepare case_id
        if case_id is None:
            if DYNAMIC_CASE_MANAGEMENT_AVAILABLE:
                first_available = get_first_available_case_id()
                if first_available:
                    print(f"INFO: Using first available case ID: {first_available}")
                    case_id = first_available
                else:
                    raise ValueError("No valid case IDs available in the database")
            else:
                raise ValueError("case_id must be specified - no default value will be used")
        else:
            try:
                case_id = int(case_id)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid case_id: {case_id} - must be a valid integer")
                
        # Additional validation using dynamic case management if available
        if DYNAMIC_CASE_MANAGEMENT_AVAILABLE:
            try:
                case_id = validate_case_id(case_id)
            except ValueError as e:
                print(f"WARNING: {e}")
                first_available = get_first_available_case_id()
                if first_available:
                    print(f"INFO: Using first available case ID: {first_available} instead")
                    case_id = first_available
        # Validate contingency_id if provided
        if contingency_id is not None:
            try:
                contingency_id = int(contingency_id)
            except (ValueError, TypeError):
                print(f"Warning: Invalid contingency_id '{contingency_id}', ignoring contingency")
                contingency_id = None
        
        # Use cached version for actual data fetching
        buses_df, branches_df, title = _fetch_case_data_cached(case_id, contingency_id)
        
        if buses_df is None or branches_df is None:
            print(f"❌ No data found for case_id={case_id}, contingency_id={contingency_id}")
            return None, None, title if title else f"Case {case_id}", 0, 100
        
        if buses_df.empty or branches_df.empty:
            print(f"❌ Empty data for case_id={case_id}, contingency_id={contingency_id}")
            return None, None, title, 0, 100
        
        print(f"✅ Found data for {title}: {len(buses_df)} buses, {len(branches_df)} branches")
        
        # Calculate min and max load for color scaling
        min_load = 0
        max_load = 100
        
        # Try to get loading percentage from various column names
        for load_col in ['LOADING_PERCENT', 'LOADING', 'load_level']:
            if load_col in branches_df.columns:
                min_load = branches_df[load_col].min()
                max_load = branches_df[load_col].max()
                break
                
        # If we have MVA and RATE, calculate loading percentage
        if 'MVA' in branches_df.columns and 'RATE' in branches_df.columns:
            # Make sure RATE is not zero to avoid division by zero
            branches_df['calculated_loading'] = branches_df.apply(
                lambda row: (row['MVA'] / row['RATE'] * 100) if row['RATE'] > 0 else 0, 
                axis=1
            )
            min_load = min(min_load, branches_df['calculated_loading'].min())
            max_load = max(max_load, branches_df['calculated_loading'].max())
        
        # Make sure we have reasonable values
        min_load = max(0, min_load if not pd.isna(min_load) else 0)
        max_load = min(150, max_load if not pd.isna(max_load) and max_load > 0 else 100)
        
        return buses_df, branches_df, title, min_load, max_load
        
    except Exception as e:
        print(f"❌ Error fetching case data: {e}")
        traceback.print_exc()
        return None, None, f"Case {case_id}", 0, 100

def create_network_graph(case_id, contingency_id=None):
    """
    Create a network graph using data_viz_fall.py
    
    Parameters:
    -----------
    case_id : int
        The case ID to visualize
    contingency_id : int or None
        The contingency ID to visualize, or None for base case
        
    Returns:
    --------
    plotly.graph_objects.Figure
        The network graph figure
    """
    import time
    start_time = time.time()
    
    try:
        print(f"⏱️ Starting network graph creation for case_id={case_id}, contingency_id={contingency_id}")
        
        # Import data_viz_fall module
        data_viz_fall = import_data_viz_fall()
        if data_viz_fall is None:
            raise ImportError("Failed to import data_viz_fall module")
        
        fetch_start = time.time()
        # Fetch case data
        buses_df, branches_df, title, min_load, max_load = fetch_case_data(case_id, contingency_id)
        fetch_time = time.time() - fetch_start
        print(f"⏱️ Data fetch took {fetch_time:.2f} seconds")
        
        if buses_df is None or branches_df is None:
            fig = go.Figure()
            fig.add_annotation(
                text=f"No data found for case {case_id}" + 
                     (f", contingency {contingency_id}" if contingency_id is not None else ""),
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="orange")
            )
            fig.update_layout(title=f"No Data Available - {title}")
            return fig
        
        # Create network graph - Make sure column names match what create_network_graph expects
        # Check if the expected columns exist, if not try to map from other common column names
        column_mappings = {
            'FROM_BUS': ['From_Bus', 'FROM', 'from_bus', 'F_BUS'],
            'TO_BUS': ['To_Bus', 'TO', 'to_bus', 'T_BUS']
        }
        
        # Enhanced column mapping with better debugging
        for target_col, possible_cols in column_mappings.items():
            if target_col not in branches_df.columns:
                mapped = False
                for col in possible_cols:
                    if col in branches_df.columns:
                        branches_df[target_col] = branches_df[col]
                        print(f"✅ Mapped column {col} to {target_col}")
                        mapped = True
                        break
                if not mapped:
                    print(f"❌ ERROR: Could not map any column to {target_col}. Available columns: {branches_df.columns.tolist()}")
            else:
                print(f"✓ Column {target_col} already exists")
        
        # Debug info before calling create_network_graph
        print(f"Creating network graph with:")
        print(f"- Buses shape: {buses_df.shape}")
        print(f"- Branches shape: {branches_df.shape}")
        print(f"- Buses columns: {buses_df.columns.tolist()}")
        print(f"- Branches columns: {branches_df.columns.tolist()}")
        
        try:
            # Make a copy to avoid modifying the original dataframes
            buses_copy = buses_df.copy()
            branches_copy = branches_df.copy()
            
            # Ensure critical columns exist
            if 'BUS_NUMBER' not in buses_copy.columns:
                if 'Bus_Number' in buses_copy.columns:
                    buses_copy['BUS_NUMBER'] = buses_copy['Bus_Number']
                elif 'BUS' in buses_copy.columns:
                    buses_copy['BUS_NUMBER'] = buses_copy['BUS']
                else:
                    print("❌ ERROR: No BUS_NUMBER column found!")
            
            # Additional mapping to ensure compatibility with data_viz_fall.py
            # Bus numbering fixes
            if 'BUS_NUMBER' in buses_copy.columns:
                buses_copy['BUS_NUMBER'] = buses_copy['BUS_NUMBER'].astype(int)
                
            # Branch From/To fixes
            for col in ['FROM_BUS', 'TO_BUS']:
                if col in branches_copy.columns:
                    branches_copy[col] = branches_copy[col].astype(int)
            
            # Special debugging info
            print(f"⚠️ Debug final data before visualization:")
            print(f"- Buses head: {buses_copy[['BUS_NUMBER']].head(3).to_dict()}")
            print(f"- Branches head: {branches_copy[['FROM_BUS', 'TO_BUS']].head(3).to_dict() if 'FROM_BUS' in branches_copy.columns and 'TO_BUS' in branches_copy.columns else 'Missing FROM_BUS/TO_BUS columns'}")
            
            # Call the create_network_graph function with extra error handling
            try:
                viz_start = time.time()
                fig = data_viz_fall.create_network_graph(
                    buses_copy, branches_copy, title, min_load, max_load, case_id
                )
                viz_time = time.time() - viz_start
                total_time = time.time() - start_time
                print(f"⏱️ Visualization took {viz_time:.2f} seconds")
                print(f"⏱️ Total time: {total_time:.2f} seconds")
                print(f"✅ Successfully created network graph for {title}")
                return fig
            except Exception as e:
                print(f"❌ Error in data_viz_fall.create_network_graph: {e}")
                traceback.print_exc()
                
                # Create a simple fallback figure
                fallback_fig = go.Figure()
                fallback_fig.add_annotation(
                    text=f"Error in network graph visualization: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14, color="red")
                )
                return fallback_fig
            
        except Exception as e:
            print(f"❌ Error creating network graph: {e}")
            traceback.print_exc()
            
            # Create a fallback figure with error message
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating network graph: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            return fig
        
    except Exception as e:
        print(f"❌ Error creating network graph: {e}")
        traceback.print_exc()
        
        # Create error figure
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error creating network graph: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(title="Network Graph Error")
        return fig

# Test function to verify the module works correctly
def test_network_graph():
    """Test creating a network graph with a default case"""
    print("\n=== Testing Network Graph Creation ===")
    
    # Try with default case
    case_id = 42
    fig = create_network_graph(case_id)
    
    if fig is None:
        print("❌ Test failed: create_network_graph returned None")
        return False
        
    print("✅ Test passed: Network graph created successfully")
    
    # Save to HTML for verification
    try:
        output_file = "test_network_graph_direct.html"
        fig.write_html(output_file)
        print(f"✅ Saved test graph to {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving test graph: {e}")
        return False

if __name__ == "__main__":
    # Run test when executed directly
    test_network_graph()