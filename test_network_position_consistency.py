#!/usr/bin/env python3
"""
Test script to verify that network graph positions are consistent between base case and contingency case
"""

import sqlite3
import pandas as pd
import numpy as np

def test_network_position_consistency():
    """Test that base case and contingency case have the same node positions"""
    
    try:
        # Import the fixed dual network graph function
        from network_graph_dual_view import create_dual_network_graph
        
        print("🧪 Testing network graph position consistency...")
        
        # Create a dual network graph
        fig = create_dual_network_graph(case_id=0, contingency_id=1)
        
        if fig is None:
            print("❌ create_dual_network_graph returned None")
            return False
        
        print(f"✅ Successfully created dual network graph with {len(fig.data)} traces")
        
        # Extract node positions from both subplots
        base_nodes = []
        cont_nodes = []
        
        for trace in fig.data:
            # Check if this is a node trace (has markers)
            if hasattr(trace, 'mode') and 'markers' in trace.mode:
                if trace.xaxis == 'x':  # First subplot (base case)
                    base_nodes.extend(list(zip(trace.x, trace.y)))
                elif trace.xaxis == 'x2':  # Second subplot (contingency)
                    cont_nodes.extend(list(zip(trace.x, trace.y)))
        
        print(f"Base case nodes: {len(base_nodes)}")
        print(f"Contingency nodes: {len(cont_nodes)}")
        
        # Check if we have the same number of nodes
        if len(base_nodes) != len(cont_nodes):
            print(f"⚠️ Different number of nodes: {len(base_nodes)} vs {len(cont_nodes)}")
            # This might be expected if some nodes are missing in contingency case
        
        # Check if positions are identical for overlapping nodes
        # Since we're using consistent positions, all corresponding nodes should have the same coordinates
        min_nodes = min(len(base_nodes), len(cont_nodes))
        position_matches = 0
        
        for i in range(min_nodes):
            base_pos = base_nodes[i]
            cont_pos = cont_nodes[i]
            
            # Check if positions are close (allowing for small floating point differences)
            if abs(base_pos[0] - cont_pos[0]) < 1e-10 and abs(base_pos[1] - cont_pos[1]) < 1e-10:
                position_matches += 1
        
        consistency_ratio = position_matches / min_nodes if min_nodes > 0 else 0
        
        print(f"Position consistency: {position_matches}/{min_nodes} nodes ({consistency_ratio:.1%})")
        
        if consistency_ratio > 0.95:  # Allow for some small differences
            print("✅ Network graph positions are consistent!")
            return True
        else:
            print("❌ Network graph positions are inconsistent!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing network position consistency: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_network_position_consistency()
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")