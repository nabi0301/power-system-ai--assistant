#!/usr/bin/env python3
"""
Utility to directly display a network graph from the database
"""

import os
import sys
import traceback
import webbrowser

def show_network_graph():
    """Display a network graph from the database"""
    try:
        # Import direct_network_integration
        import direct_network_integration
        
        # Get a default case ID from command line or use 42
        case_id = int(sys.argv[1]) if len(sys.argv) > 1 else 42
        
        print(f"Creating network graph for case {case_id}...")
        
        # Create the network graph
        fig = direct_network_integration.create_network_graph(case_id)
        
        if fig is not None:
            # Save to HTML
            output_file = "network_graph.html"
            fig.write_html(output_file)
            
            # Open in browser
            abs_path = os.path.abspath(output_file)
            print(f"Opening network graph in browser: {abs_path}")
            webbrowser.open('file://' + abs_path)
            
            print("✅ Network graph displayed successfully")
            return True
        else:
            print("❌ Failed to create network graph (None returned)")
            return False
    
    except Exception as e:
        print(f"❌ Error displaying network graph: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    show_network_graph()