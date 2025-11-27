#!/usr/bin/env python3
"""
Test script to verify that branch and bus analysis work for contingency cases
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import pandas as pd

# Import only the analysis functions, not the whole app
try:
    from branch_analysis import create_branch_analysis_plot
    from bus_analysis import create_bus_analysis_plot
    print("✅ Successfully imported analysis functions")
except ImportError as e:
    print(f"❌ Failed to import analysis functions: {e}")
    sys.exit(1)

def test_contingency_analysis():
    """Test branch and bus analysis with contingency data"""
    
    # Connect to database
    conn = sqlite3.connect('data.db')
    
    # Get a sample contingency case
    # First, find a valid case_id and contingency_id
    query = """
        SELECT DISTINCT base_case_id, contingency_case_id 
        FROM ContingencyBusData 
        LIMIT 1
    """
    result = pd.read_sql_query(query, conn)
    
    if result.empty:
        print("❌ No contingency data found in database")
        conn.close()
        return
    
    case_id = result['base_case_id'].iloc[0]
    contingency_id = result['contingency_case_id'].iloc[0]
    
    print(f"Testing with case_id={case_id}, contingency_id={contingency_id}")
    
    # Load contingency bus data
    bus_query = f"""
        SELECT * FROM ContingencyBusData 
        WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
    """
    buses_df = pd.read_sql_query(bus_query, conn)
    
    # Load contingency branch data
    branch_query = f"""
        SELECT * FROM ContingencyBranchData 
        WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
    """
    branches_df = pd.read_sql_query(branch_query, conn)
    
    conn.close()
    
    print(f"✅ Loaded {len(buses_df)} buses and {len(branches_df)} branches")
    print(f"Bus columns: {buses_df.columns.tolist()}")
    print(f"Branch columns: {branches_df.columns.tolist()}")
    
    # Normalize column names
    if 'bus_number' in buses_df.columns and 'BUS_NUMBER' not in buses_df.columns:
        buses_df['BUS_NUMBER'] = buses_df['bus_number']
        print("✅ Normalized bus_number -> BUS_NUMBER")
    
    # Test bus analysis
    print("\n=== Testing Bus Analysis ===")
    try:
        bus_fig = create_bus_analysis_plot(buses_df, case_id=case_id, contingency_id=contingency_id)
        print(f"✅ Bus analysis successful! Figure type: {type(bus_fig)}")
        print(f"   Figure has {len(bus_fig.data)} traces")
    except Exception as e:
        print(f"❌ Bus analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test branch analysis
    print("\n=== Testing Branch Analysis ===")
    try:
        branch_fig = create_branch_analysis_plot(branches_df, case_id=case_id, contingency_id=contingency_id)
        print(f"✅ Branch analysis successful! Figure type: {type(branch_fig)}")
        print(f"   Figure has {len(branch_fig.data)} traces")
    except Exception as e:
        print(f"❌ Branch analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_contingency_analysis()
