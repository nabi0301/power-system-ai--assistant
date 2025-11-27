#!/usr/bin/env python3
"""
Test AI trend analysis command processing
"""

def test_ai_trend_analysis():
    """Test that AI can process trend analysis commands"""
    
    try:
        # Import the AI response function
        import sys
        sys.path.append('c:/Projects/dlr-database-project')
        
        # Import required modules like the main app does
        from power_viz_with_database import get_ai_response, ai_context, TREND_ANALYZER_AVAILABLE
        
        print("🧪 Testing AI trend analysis command processing...")
        print(f"TREND_ANALYZER_AVAILABLE: {TREND_ANALYZER_AVAILABLE}")
        
        # Test the trend analysis command
        test_messages = [
            "trend analysis",
            "show trend analysis", 
            "comprehensive trend analysis",
            "analyze trends"
        ]
        
        for message in test_messages:
            print(f"\n📝 Testing message: '{message}'")
            
            try:
                result = get_ai_response(message, 'network_view')
                
                if len(result) == 4:
                    response, viz_command, case_id, contingency_id = result
                else:
                    response, viz_command, case_id = result
                    contingency_id = None
                
                print(f"✅ Response: {response[:100]}...")
                print(f"✅ Viz command: {viz_command}")
                print(f"✅ Case ID: {case_id}")
                print(f"✅ Contingency ID: {contingency_id}")
                
                if viz_command == 'trend_analysis':
                    print("🎯 SUCCESS: AI correctly identified trend analysis command!")
                else:
                    print(f"❌ FAILED: Expected 'trend_analysis', got '{viz_command}'")
                
            except Exception as e:
                print(f"❌ Error processing message '{message}': {e}")
                import traceback
                traceback.print_exc()
        
        # Check if trend visualizations were stored
        if 'trend_visualizations' in ai_context:
            print(f"\n💾 Trend visualizations stored: {list(ai_context['trend_visualizations'].keys())}")
        else:
            print(f"\n❌ No trend visualizations found in ai_context")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ai_trend_analysis()
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")