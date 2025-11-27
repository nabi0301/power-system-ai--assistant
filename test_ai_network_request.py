#!/usr/bin/env python3
"""
Test script to verify AI assistant can detect and respond to network graph requests
"""

from enhanced_network_graphs import (
    has_network_graph_request,
    extract_network_graph_request,
    get_available_network_graphs,
    generate_network_graph_response
)

def test_network_requests():
    """Test various network graph request patterns"""
    test_messages = [
        "show network graph",
        "display network",
        "show the network topology",
        "can you show me the network diagram?",
        "I want to see the network",
        "display network graph for case 42",
        "show network for contingency 5",
    ]
    
    print("=" * 60)
    print("Testing Network Graph Request Detection")
    print("=" * 60)
    
    for message in test_messages:
        print(f"\n📝 Test message: '{message}'")
        
        # Test detection
        detected = has_network_graph_request(message)
        print(f"   Detected: {detected}")
        
        if detected:
            # Extract request details
            request_info = extract_network_graph_request(message)
            print(f"   Request info: {request_info}")
            
            # Get available cases
            available_cases = get_available_network_graphs()
            print(f"   Available cases: {len(available_cases)} cases found")
            
            # Generate response
            response, viz_type, case_id, contingency_id = generate_network_graph_response(
                request_info, available_cases
            )
            print(f"   Response preview: {response[:100]}...")
            print(f"   Viz type: {viz_type}")
            print(f"   Case ID: {case_id}")
            print(f"   Contingency ID: {contingency_id}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_network_requests()
