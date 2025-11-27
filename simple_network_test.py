#!/usr/bin/env python3
"""
Simple standalone test for network graph detection
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_network_graphs import has_network_graph_request
    
    test_messages = [
        "show network graph",
        "display network",
        "show the network topology",
        "can you show me voltage?",  # Should be False
        "I want to see the network",
    ]
    
    print("Testing Network Graph Detection:")
    print("-" * 50)
    
    for msg in test_messages:
        result = has_network_graph_request(msg)
        status = "✅ DETECTED" if result else "❌ NOT DETECTED"
        print(f"{status}: '{msg}'")
    
    print("-" * 50)
    print("Test complete!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
