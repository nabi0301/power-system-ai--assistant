#!/usr/bin/env python3
"""
Test Network Integration

This script tests the integration between data_viz_fall.py and the direct_network_integration module
to ensure network graph visualization is working correctly.
"""

import os
import sys
import traceback

def print_banner(message):
    """Print a nice banner with the given message"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80 + "\n")

def test_direct_integration():
    """Test direct network integration module"""
    print_banner("Testing Direct Network Integration")
    
    try:
        from direct_network_integration import test_network_graph, create_network_graph
        
        # Test basic network graph creation
        test_result = test_network_graph()
        if test_result:
            print("✅ Basic network graph test passed")
        else:
            print("❌ Basic network graph test failed")
            return False
        
        # Test with specific cases
        print("\nTesting with specific cases...")
        
        # Test with default case (should succeed)
        print("\nTest 1: Default case")
        case_id = 42
        fig = create_network_graph(case_id)
        if fig is not None:
            print(f"✅ Successfully created network graph for case {case_id}")
            try:
                output_file = f"test_case_{case_id}_network.html"
                fig.write_html(output_file)
                print(f"✅ Saved test graph to {output_file}")
            except Exception as e:
                print(f"⚠️ Could not save graph: {e}")
        else:
            print(f"❌ Failed to create network graph for case {case_id}")
            return False
        
        # Test with contingency case (may or may not succeed depending on data)
        print("\nTest 2: Contingency case")
        case_id = 42
        contingency_id = 1
        fig = create_network_graph(case_id, contingency_id)
        if fig is not None:
            print(f"✅ Successfully created network graph for case {case_id}, contingency {contingency_id}")
            try:
                output_file = f"test_case_{case_id}_contingency_{contingency_id}_network.html"
                fig.write_html(output_file)
                print(f"✅ Saved test graph to {output_file}")
            except Exception as e:
                print(f"⚠️ Could not save graph: {e}")
        else:
            print(f"⚠️ Could not create contingency graph (this might be OK if no data exists)")
        
        print("\nDirect integration tests complete")
        return True
        
    except Exception as e:
        print(f"❌ Error in direct network integration test: {e}")
        traceback.print_exc()
        return False

def test_network_comparison():
    """Test network comparison module"""
    print_banner("Testing Network Comparison")
    
    try:
        from network_comparison import create_network_comparison
        
        # Test with default case
        print("\nCreating network comparison visualization...")
        case_id = 42
        contingency_id = 1
        fig = create_network_comparison(case_id, contingency_id)
        
        if fig is not None:
            print(f"✅ Successfully created network comparison for case {case_id}, contingency {contingency_id}")
            try:
                output_file = f"test_network_comparison_{case_id}_{contingency_id}.html"
                fig.write_html(output_file)
                print(f"✅ Saved test comparison to {output_file}")
            except Exception as e:
                print(f"⚠️ Could not save comparison: {e}")
            return True
        else:
            print(f"❌ Failed to create network comparison")
            return False
    
    except Exception as e:
        print(f"❌ Error in network comparison test: {e}")
        traceback.print_exc()
        return False

def test_data_viz_fall_direct():
    """Test data_viz_fall.py directly"""
    print_banner("Testing data_viz_fall.py Directly")
    
    try:
        import sqlite3
        import pandas as pd
        
        # First, try to import data_viz_fall module
        import importlib.util
        data_viz_fall_path = 'data_viz_fall.py'
        
        if not os.path.exists(data_viz_fall_path):
            print(f"❌ Error: data_viz_fall.py not found at {data_viz_fall_path}")
            return False
        
        spec = importlib.util.spec_from_file_location("data_viz_fall", data_viz_fall_path)
        data_viz_fall = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_viz_fall)
        
        if not hasattr(data_viz_fall, 'create_network_graph'):
            print("❌ Error: create_network_graph function not found in data_viz_fall.py")
            return False
            
        print("✅ Successfully imported create_network_graph from data_viz_fall.py")
        
        # Connect to database
        conn = sqlite3.connect('data.db')
        
        # Get data for a simple test case
        case_id = 42
        buses_query = f"SELECT * FROM BaseBusData WHERE base_case_id = {case_id}"
        branches_query = f"SELECT * FROM BaseBranchData WHERE base_case_id = {case_id}"
        
        buses_df = pd.read_sql_query(buses_query, conn)
        branches_df = pd.read_sql_query(branches_query, conn)
        
        conn.close()
        
        if buses_df.empty or branches_df.empty:
            print(f"❌ No data found for case {case_id}")
            return False
            
        print(f"✅ Retrieved data for case {case_id}: {len(buses_df)} buses, {len(branches_df)} branches")
        
        # Create network graph using direct call to data_viz_fall
        print("\nCreating network graph using direct call to data_viz_fall.py...")
        title = f"Direct Test - Case {case_id}"
        min_load = 0
        max_load = 100
        
        fig = data_viz_fall.create_network_graph(buses_df, branches_df, title, min_load, max_load, case_id)
        
        if fig is not None:
            print("✅ Successfully created network graph using direct call")
            try:
                output_file = "test_direct_data_viz_fall.html"
                fig.write_html(output_file)
                print(f"✅ Saved test graph to {output_file}")
                return True
            except Exception as e:
                print(f"⚠️ Could not save graph: {e}")
                return False
        else:
            print("❌ Failed to create network graph using direct call")
            return False
        
    except Exception as e:
        print(f"❌ Error testing data_viz_fall directly: {e}")
        traceback.print_exc()
        return False
        
def main():
    """Run all tests"""
    print_banner("NETWORK VISUALIZATION INTEGRATION TESTS")
    
    all_passed = True
    
    # Test 1: Direct data_viz_fall integration
    if test_data_viz_fall_direct():
        print("\n✅ Direct data_viz_fall.py test: PASSED")
    else:
        print("\n❌ Direct data_viz_fall.py test: FAILED")
        all_passed = False
        
    # Test 2: Direct network integration module
    if test_direct_integration():
        print("\n✅ Direct network integration test: PASSED")
    else:
        print("\n❌ Direct network integration test: FAILED")
        all_passed = False
        
    # Test 3: Network comparison module
    if test_network_comparison():
        print("\n✅ Network comparison test: PASSED")
    else:
        print("\n❌ Network comparison test: FAILED")
        all_passed = False
        
    # Overall result
    print_banner("TEST RESULTS")
    if all_passed:
        print("✅ All tests PASSED! Network visualization integration is working correctly.")
        print("\nYou can now run the full application with:")
        print("python launch_with_network_graphs.py")
    else:
        print("⚠️ Some tests FAILED. Please review the issues before running the full application.")
        
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())