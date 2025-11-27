#!/usr/bin/env python3
"""
Test script to verify AI assistant visualization integration
"""

import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

def test_ai_visualization():
    """Test the AI assistant's visualization capabilities"""
    
    try:
        from intelligent_chat_engine import PowerSystemIntelligentAssistant
        
        print("🧪 Testing AI Assistant Visualization Integration")
        print("=" * 60)
        
        # Initialize the intelligent assistant
        db_path = "data.db"  # Use the main database
        ai_assistant = PowerSystemIntelligentAssistant(db_path)
        
        print("✅ AI Assistant initialized successfully")
        
        # Test cases with visualization requests
        test_messages = [
            "Show me the voltage profile",
            "Plot the system loading",
            "Visualize the power flow analysis", 
            "Can you display a thermal loading chart?",
            "Create a voltage stability plot"
        ]
        
        print("\n📊 Testing Visualization Requests:")
        print("-" * 40)
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n🔍 Test {i}: '{message}'")
            
            try:
                # Test the enhanced processing with visualization
                result = ai_assistant.process_with_visualization(message)
                
                text_response = result.get("text_response", "")
                visualization = result.get("visualization", None)
                intent = result.get("intent", {})
                
                print(f"📝 Text Response: {text_response[:100]}...")
                print(f"📊 Visualization Generated: {'Yes' if visualization else 'No'}")
                print(f"🎯 Intent Detected: {intent.get('primary_focus', 'general')}")
                print(f"🖼️ Visualization Request: {intent.get('visualization_request', False)}")
                
                if visualization:
                    print(f"   📈 Visualization Type: {type(visualization).__name__}")
                    
            except Exception as e:
                print(f"❌ Error processing message: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 AI Visualization Integration Test Complete!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

if __name__ == "__main__":
    success = test_ai_visualization()
    sys.exit(0 if success else 1)