"""
Test utility for data_viz_fall.py and power_viz_with_database.py integration
This script ensures that the network visualization from data_viz_fall.py works correctly
"""
import os
import sys
import importlib.util
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def load_test_data():
    """Create test data for visualization testing"""
    # Create sample bus data
    buses = pd.DataFrame({
        'BUS_NUMBER': list(range(1, 21)),
        'VM': np.random.uniform(0.9, 1.1, 20),  # Voltage magnitude
        'VA': np.random.uniform(-30, 30, 20),   # Voltage angle
        'BASE_KV': [138] * 10 + [230] * 10,     # Base voltage
        'PG': np.random.uniform(0, 200, 20),    # Generation
        'QG': np.random.uniform(0, 50, 20),     # Reactive generation
        'PD': np.random.uniform(10, 150, 20),   # Load
        'QD': np.random.uniform(0, 30, 20),     # Reactive load
        'x_coord': np.random.uniform(0, 100, 20),  # X coordinate
        'y_coord': np.random.uniform(0, 100, 20)   # Y coordinate
    })
    
    # Create sample branch data
    branches = []
    for i in range(25):
        from_bus = np.random.randint(1, 21)
        to_bus = np.random.randint(1, 21)
        while to_bus == from_bus:  # Ensure no self-loops
            to_bus = np.random.randint(1, 21)
            
        branches.append({
            'branch_number': i + 1,
            'From_Bus': from_bus,
            'To_Bus': to_bus,
            'PF': np.random.uniform(10, 100),    # Active power flow
            'QF': np.random.uniform(5, 50),      # Reactive power flow
            'MVA': np.random.uniform(20, 150),   # Apparent power
            'RATE': np.random.uniform(100, 200), # Rating
            'VIO': np.random.uniform(0, 120)     # Violation percentage
        })
    
    branches_df = pd.DataFrame(branches)
    
    return buses, branches_df

def test_data_viz_fall_visualization():
    """Test data_viz_fall.py's create_network_graph function with test data"""
    try:
        # Load data_viz_fall.py
        module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_viz_fall.py')
        spec = importlib.util.spec_from_file_location("data_viz_fall", module_path)
        data_viz_fall = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_viz_fall)
        
        # Generate test data
        buses, branches = load_test_data()
        print(f"Created test data: {len(buses)} buses, {len(branches)} branches")
        
        # Prepare data for data_viz_fall.py
        buses_renamed = buses.copy()
        branches_renamed = branches.copy()
        
        # Rename necessary columns
        if 'From_Bus' in branches_renamed.columns:
            branches_renamed.rename(columns={'From_Bus': 'FROM_BUS', 'To_Bus': 'TO_BUS'}, inplace=True)
        
        # Calculate min_load and max_load
        min_load = buses['PD'].min()
        max_load = buses['PD'].max()
        
        # Test the visualization function
        print("Testing data_viz_fall.py's create_network_graph function...")
        fig = data_viz_fall.create_network_graph(
            buses_renamed, branches_renamed, "Test Network Visualization", 
            min_load, max_load, case_id=1
        )
        
        # Save the result to an HTML file for inspection
        fig.write_html("test_viz_fall_network.html")
        print("✅ Test successful - visualization saved to test_viz_fall_network.html")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_power_viz_integration():
    """Test power_viz_with_database.py's create_power_system_plot with test data"""
    try:
        # Load power_viz_with_database.py
        module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'power_viz_with_database.py')
        spec = importlib.util.spec_from_file_location("power_viz", module_path)
        power_viz = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(power_viz)
        
        # Generate test data
        buses, branches = load_test_data()
        print(f"Created test data: {len(buses)} buses, {len(branches)} branches")
        
        # Test the power_viz_with_database.py's create_power_system_plot function
        print("Testing power_viz_with_database.py's create_power_system_plot function...")
        fig = power_viz.create_power_system_plot(buses, branches, case_id=1)
        
        # Save the result to an HTML file for inspection
        fig.write_html("test_power_viz_integration.html")
        print("✅ Test successful - visualization saved to test_power_viz_integration.html")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def run_all_tests():
    """Run all tests to verify the integration"""
    print("\n" + "="*70)
    print("🧪 Running Integration Tests")
    print("="*70 + "\n")
    
    # Test data_viz_fall.py visualization directly
    print("Test 1: data_viz_fall.py Visualization")
    test_data_viz_fall_visualization()
    
    print("\n" + "-"*70 + "\n")
    
    # Test power_viz_with_database.py with integration
    print("Test 2: power_viz_with_database.py Integration")
    test_power_viz_integration()
    
    print("\n" + "="*70)
    print("🧪 Tests Completed")
    print("="*70)
    print("\nCheck the generated HTML files to verify the visualizations:")
    print(" - test_viz_fall_network.html")
    print(" - test_power_viz_integration.html")
    print("\nIf both files display properly, the integration is working correctly.")

if __name__ == "__main__":
    run_all_tests()