#!/usr/bin/env python3
"""
Quick verification script to test network graph integration.
This file tests the direct_network_integration module and creates a test visualization.
"""

import os
import sys

def main():
    print("Testing network graph integration...")
    
    # Test direct network integration
    try:
        from direct_network_integration import create_network_graph
        print("✅ Successfully imported create_network_graph from direct_network_integration")
        
        # Create a test graph with default case
        case_id = 42
        print(f"Creating test graph for case {case_id}...")
        fig = create_network_graph(case_id)
        
        if fig is None:
            print("❌ create_network_graph returned None")
            return False
            
        # Save the figure to HTML for verification
        output_file = "network_graph_test.html"
        fig.write_html(output_file)
        print(f"✅ Successfully created network graph and saved to {output_file}")
        print(f"Open {output_file} in a browser to verify the visualization")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during network graph test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Network graph integration is working correctly!")
    else:
        print("\n❌ Network graph integration test failed. See errors above.")