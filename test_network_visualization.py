#!/usr/bin/env python3
"""
Test script to verify that network visualizations work correctly in the application.

This script tests:
1. Single network graph with base case
2. Single network graph with contingency case
3. Four-panel network comparison with base, contingency, SLR, DLR

Usage:
    python test_network_visualization.py
"""

import os
import sys
import importlib.util
import sqlite3
import pandas as pd
import plotly.graph_objects as go

def import_module_from_file(module_name, file_path):
    """Import a module from a file path"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error importing {module_name} from {file_path}: {e}")
        return None

def find_cases_with_complete_data():
    """Find cases that have complete data for all four case types"""
    try:
        print("Searching for cases with complete data...")
        # Import data_availability module
        data_availability = import_module_from_file("data_availability", "data_availability.py")
        
        if not data_availability:
            print("❌ Could not import data_availability module")
            return None
            
        # Connect to database
        conn = sqlite3.connect('data.db')
        
        # Get all base cases
        base_cases_query = "SELECT DISTINCT base_case_id FROM BaseBusData ORDER BY base_case_id"
        base_cases = pd.read_sql_query(base_cases_query, conn)
        
        # Get contingency cases
        cont_cases_query = "SELECT DISTINCT base_case_id, contingency_case_id FROM ContingencyBusData ORDER BY base_case_id, contingency_case_id"
        cont_cases = pd.read_sql_query(cont_cases_query, conn)
        
        conn.close()
        
        # Test for complete data
        complete_cases = []
        
        print(f"Testing {len(base_cases)} base cases and {len(cont_cases)} contingency cases...")
        
        # Test base cases (without contingency)
        for _, row in base_cases.iterrows():
            case_id = row['base_case_id']
            availability = data_availability.check_data_availability(case_id, None)
            available_count = sum(1 for available in availability.values() if available)
            
            if available_count >= 1:  # At least base case data is available
                case_info = {
                    'case_id': case_id,
                    'contingency_id': None,
                    'available_count': available_count,
                    'available_types': [key for key, available in availability.items() if available]
                }
                complete_cases.append(case_info)
                
        # Test contingency cases
        for _, row in cont_cases.iterrows():
            case_id = row['base_case_id']
            contingency_id = row['contingency_case_id']
            
            availability = data_availability.check_data_availability(case_id, contingency_id)
            available_count = sum(1 for available in availability.values() if available)
            
            if available_count >= 2:  # At least base and contingency data is available
                case_info = {
                    'case_id': case_id,
                    'contingency_id': contingency_id,
                    'available_count': available_count,
                    'available_types': [key for key, available in availability.items() if available]
                }
                complete_cases.append(case_info)
                
        # Sort cases by number of available datasets
        complete_cases.sort(key=lambda x: x['available_count'], reverse=True)
        
        print(f"Found {len(complete_cases)} cases with at least partial data")
        if complete_cases:
            print("\nTop 5 cases with most complete data:")
            for i, case in enumerate(complete_cases[:5]):
                available_types = [t.replace('_case', '').upper() for t in case['available_types']]
                print(f"{i+1}. Case {case['case_id']}, Contingency {case['contingency_id']}: {case['available_count']}/4 datasets - {', '.join(available_types)}")
        
        return complete_cases
    except Exception as e:
        print(f"Error finding complete cases: {e}")
        return None

def test_single_network_visualization():
    """Test single network visualization with base case"""
    try:
        print("\n== Testing Single Network Visualization ==")
        data_viz_fall = import_module_from_file("data_viz_fall", "data_viz_fall.py")
        
        if not data_viz_fall:
            print("❌ Could not import data_viz_fall module")
            return False
            
        # Connect to database
        conn = sqlite3.connect('data.db')
        
        # Get a base case
        case_id = 42  # Default case ID
        buses_query = f"SELECT * FROM BaseBusData WHERE base_case_id = {case_id}"
        branches_query = f"SELECT * FROM BaseBranchData WHERE base_case_id = {case_id}"
        
        buses = pd.read_sql_query(buses_query, conn)
        branches = pd.read_sql_query(branches_query, conn)
        
        conn.close()
        
        if buses.empty or branches.empty:
            print(f"❌ No data found for case ID {case_id}")
            return False
            
        print(f"✅ Found data for case ID {case_id}: {len(buses)} buses, {len(branches)} branches")
        
        # Create network graph
        fig = data_viz_fall.create_network_graph(
            buses, branches, f"Base Case {case_id}", 0, 100, case_id
        )
        
        if fig and hasattr(fig, 'data') and len(fig.data) > 0:
            print(f"✅ Successfully created network graph with {len(fig.data)} traces")
            # Save figure to HTML for verification
            html_file = "test_network_graph.html"
            fig.write_html(html_file)
            print(f"✅ Saved test figure to {html_file} for visual verification")
            return True
        else:
            print("❌ Failed to create network graph (no traces in figure)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing single network visualization: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_network_comparison():
    """Test network comparison visualization"""
    try:
        print("\n== Testing Network Comparison Visualization ==")
        network_comparison = import_module_from_file("network_comparison", "network_comparison.py")
        
        if not network_comparison:
            print("❌ Could not import network_comparison module")
            return False
        
        # Find a case with the most complete data
        complete_cases = find_cases_with_complete_data()
        
        if not complete_cases:
            print("❌ No cases with sufficient data found")
            return False
            
        # Use the case with the most available data
        test_case = complete_cases[0]
        case_id = test_case['case_id']
        contingency_id = test_case['contingency_id']
        
        print(f"Using case {case_id}, contingency {contingency_id} with {test_case['available_count']}/4 datasets")
        
        # Create network comparison
        fig = network_comparison.create_network_comparison(case_id, contingency_id)
        
        if fig and hasattr(fig, 'data') and len(fig.data) > 0:
            print(f"✅ Successfully created network comparison with {len(fig.data)} traces")
            # Save figure to HTML for verification
            html_file = "test_network_comparison.html"
            fig.write_html(html_file)
            print(f"✅ Saved comparison figure to {html_file} for visual verification")
            return True
        else:
            print("❌ Failed to create network comparison (no traces in figure)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing network comparison: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("==== NETWORK VISUALIZATION TEST SCRIPT ====")
    
    # Test single network graph
    single_test_result = test_single_network_visualization()
    
    # Test network comparison
    comparison_test_result = test_network_comparison()
    
    # Print summary
    print("\n==== TEST SUMMARY ====")
    print(f"Single Network Graph: {'✅ PASSED' if single_test_result else '❌ FAILED'}")
    print(f"Network Comparison:   {'✅ PASSED' if comparison_test_result else '❌ FAILED'}")
    
    if single_test_result and comparison_test_result:
        print("\n✅ All network visualization tests passed!")
        print("You can now use both types of network visualizations in the application.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
