#!/usr/bin/env python3
"""
Test script to verify direct_network_integration functionality
"""

import os
import sys
import traceback

def test_direct_network():
    """Test the direct network integration module"""
    print("\n=== Testing Direct Network Integration ===")
    
    try:
        # Try to import the module
        import direct_network_integration
        print("✅ Successfully imported direct_network_integration")
        
        # Test with a specific case ID
        case_id = 42
        print(f"Testing create_network_graph with case_id={case_id}")
        
        try:
            # Create a network graph
            fig = direct_network_integration.create_network_graph(case_id)
            if fig is not None:
                print("✅ Successfully created network graph")
                
                # Save to HTML for verification
                output_file = "test_network_direct.html"
                fig.write_html(output_file)
                print(f"✅ Saved test graph to {output_file}")
                
                # Open the file in the default browser
                abs_path = os.path.abspath(output_file)
                print(f"Graph saved to: {abs_path}")
                
                return True
            else:
                print("❌ Network graph is None")
                return False
                
        except Exception as e:
            print(f"❌ Error creating network graph: {e}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Error importing direct_network_integration: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test
    result = test_direct_network()
    print(f"\nTest result: {'PASS' if result else 'FAIL'}")
    
    # Exit with appropriate code
    sys.exit(0 if result else 1)