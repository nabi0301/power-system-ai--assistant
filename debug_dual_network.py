#!/usr/bin/env python3
"""
Debug dual network function
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import the function
import sys
sys.path.append('.')

def debug_dual_network():
    print("🔍 Debugging dual network function...")
    
    # Test with basic data
    case_id = 0
    contingency_id = 1
    
    try:
        print(f"📊 Testing with case_id={case_id}, contingency_id={contingency_id}")
        
        # Connect to database
        conn = sqlite3.connect('data.db')
        
        # Get base case data
        base_buses_query = f"SELECT * FROM BaseBusData WHERE base_case_id = {case_id}"
        base_branches_query = f"SELECT * FROM BaseBranchData WHERE base_case_id = {case_id}"
        
        base_buses_df = pd.read_sql_query(base_buses_query, conn)
        base_branches_df = pd.read_sql_query(base_branches_query, conn)
        
        print(f"✅ Base data: {len(base_buses_df)} buses, {len(base_branches_df)} branches")
        print(f"✅ Base bus columns: {list(base_buses_df.columns)}")
        
        # Get contingency case data  
        cont_buses_query = f"""
            SELECT * FROM ContingencyBusData 
            WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
        """
        cont_branches_query = f"""
            SELECT * FROM ContingencyBranchData 
            WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
        """
        
        cont_buses_df = pd.read_sql_query(cont_buses_query, conn)
        cont_branches_df = pd.read_sql_query(cont_branches_query, conn)
        
        print(f"✅ Contingency data: {len(cont_buses_df)} buses, {len(cont_branches_df)} branches")
        
        if cont_buses_df.empty or cont_branches_df.empty:
            print("⚠️ No contingency data found, using base case as contingency simulation")
            cont_buses_df = base_buses_df.copy()
            cont_branches_df = base_branches_df.copy()
            
            # Modify slightly to show difference
            if 'PF' in cont_branches_df.columns:
                cont_branches_df['PF'] = cont_branches_df['PF'] * 1.1
                print("📊 Modified contingency data to increase loading by 10%")
        
        # Normalize column names
        def normalize_columns(buses_df, branches_df):
            if 'bus_number' in buses_df.columns and 'BUS_NUMBER' not in buses_df.columns:
                buses_df = buses_df.rename(columns={'bus_number': 'BUS_NUMBER'})
            if 'From_Bus' in branches_df.columns and 'FROM_BUS' not in branches_df.columns:
                branches_df = branches_df.rename(columns={'From_Bus': 'FROM_BUS', 'To_Bus': 'TO_BUS'})
            
            # Add coordinates
            if 'x_coord' not in buses_df.columns:
                buses_df['x_coord'] = (buses_df['BUS_NUMBER'] % 12) * 30
                buses_df['y_coord'] = (buses_df['BUS_NUMBER'] // 12) * 25
            
            return buses_df, branches_df
        
        base_buses_df, base_branches_df = normalize_columns(base_buses_df, base_branches_df)
        cont_buses_df, cont_branches_df = normalize_columns(cont_buses_df, cont_branches_df)
        
        print(f"✅ After normalization:")
        print(f"✅ Base columns: {list(base_buses_df.columns)}")
        print(f"✅ Cont columns: {list(cont_buses_df.columns)}")
        
        # Test if we can create individual network graphs
        from data_viz_fall import create_network_graph
        
        print("🎯 Creating base network graph...")
        base_fig = create_network_graph(
            buses=base_buses_df,
            branches=base_branches_df,
            title="Base Case",
            min_load=0,
            max_load=100,
            case_id=0
        )
        
        print("🎯 Creating contingency network graph...")
        cont_fig = create_network_graph(
            buses=cont_buses_df,
            branches=cont_branches_df,
            title="Contingency Case",
            min_load=0,
            max_load=100,
            case_id=1
        )
        
        if base_fig is None:
            print("❌ Base figure creation failed")
            return False
            
        if cont_fig is None:
            print("❌ Contingency figure creation failed")
            return False
        
        print(f"✅ Base figure: {len(base_fig.data)} traces")
        print(f"✅ Contingency figure: {len(cont_fig.data)} traces")
        
        # Create dual subplot
        print("🔄 Creating dual subplot...")
        dual_fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=["Base Case", "Contingency Case"],
            specs=[[{"type": "scatter"}, {"type": "scatter"}]],
            horizontal_spacing=0.1
        )
        
        # Add traces
        for trace in base_fig.data:
            dual_fig.add_trace(trace, row=1, col=1)
        
        for trace in cont_fig.data:
            dual_fig.add_trace(trace, row=1, col=2)
        
        # Update layout
        dual_fig.update_layout(
            title="Dual Network Test",
            height=600,
            width=1200,
            showlegend=False
        )
        
        print(f"✅ Dual figure created with {len(dual_fig.data)} traces")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = debug_dual_network()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Dual network debug test")