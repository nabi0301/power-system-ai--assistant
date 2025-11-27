#!/usr/bin/env python3
"""
Test dual network functionality
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def test_dual_network():
    try:
        # Import the required functions
        from data_viz_fall import create_network_graph
        
        print("✅ Successfully imported create_network_graph")
        
        # Connect to database
        conn = sqlite3.connect('data.db')
        
        # Test with case 0 and contingency 1
        case_id = 0
        contingency_id = 1
        
        print(f"🔍 Testing dual network: Base Case {case_id} vs Contingency {contingency_id}")
        
        # Get base case data
        base_buses_query = f"SELECT * FROM BaseBusData WHERE base_case_id = {case_id}"
        base_branches_query = f"SELECT * FROM BaseBranchData WHERE base_case_id = {case_id}"
        
        base_buses_df = pd.read_sql_query(base_buses_query, conn)
        base_branches_df = pd.read_sql_query(base_branches_query, conn)
        
        print(f"✅ Base case: {len(base_buses_df)} buses, {len(base_branches_df)} branches")
        
        # Get contingency case data (if available)
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
        
        if cont_buses_df.empty or cont_branches_df.empty:
            print("⚠️ No contingency data found, using base case data as contingency")
            cont_buses_df = base_buses_df.copy()
            cont_branches_df = base_branches_df.copy()
        else:
            print(f"✅ Contingency case: {len(cont_buses_df)} buses, {len(cont_branches_df)} branches")
        
        # Fix column naming differences  
        # Contingency data uses lowercase column names, need to normalize
        if 'bus_number' in cont_buses_df.columns:
            cont_buses_df['BUS_NUMBER'] = cont_buses_df['bus_number']
            
        # Add coordinates
        for df in [base_buses_df, cont_buses_df]:
            if 'x_coord' not in df.columns:
                df['x_coord'] = (df['BUS_NUMBER'] % 12) * 30
                df['y_coord'] = (df['BUS_NUMBER'] // 12) * 25
        
        # Calculate load ranges
        all_loads = []
        for branches in [base_branches_df, cont_branches_df]:
            if 'PF' in branches.columns:
                all_loads.extend(branches['PF'].dropna().tolist())
        
        if all_loads:
            min_load = min(all_loads)
            max_load = max(all_loads)
        else:
            min_load, max_load = 0, 100
        
        print(f"🔍 Load range: {min_load:.2f} to {max_load:.2f}")
        
        # Create individual network graphs
        print("🎯 Creating base case network graph...")
        base_fig = create_network_graph(
            buses=base_buses_df,
            branches=base_branches_df,
            title="Base Case",
            min_load=min_load,
            max_load=max_load,
            case_id=case_id
        )
        
        print("🎯 Creating contingency case network graph...")
        cont_fig = create_network_graph(
            buses=cont_buses_df,
            branches=cont_branches_df,
            title=f"Contingency {contingency_id}",
            min_load=min_load,
            max_load=max_load,
            case_id=contingency_id
        )
        
        if base_fig is not None and cont_fig is not None:
            print("✅ Both network graphs created successfully!")
            
            # Create dual network subplot
            print("🔄 Creating dual network comparison...")
            dual_fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=[f"Base Case {case_id}", f"Contingency {contingency_id}"],
                specs=[[{"type": "scatter"}, {"type": "scatter"}]]
            )
            
            # Add base case traces
            for trace in base_fig.data:
                dual_fig.add_trace(trace, row=1, col=1)
            
            # Add contingency case traces  
            for trace in cont_fig.data:
                dual_fig.add_trace(trace, row=1, col=2)
            
            # Update layout
            dual_fig.update_layout(
                title=f"Dual Network Comparison: Base {case_id} vs Contingency {contingency_id}",
                showlegend=False,
                height=600
            )
            
            print("✅ Dual network comparison created successfully!")
            return True
        else:
            print("❌ Failed to create one or both network graphs")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_dual_network()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Dual network test completed")