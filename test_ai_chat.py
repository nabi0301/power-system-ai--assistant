#!/usr/bin/env python3
"""
Test script to verify AI chat functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test the AI response function
def test_ai_response():
    print("🔍 Testing AI Response Functionality")
    print("=" * 50)
    
    try:
        # Import the AI response function
        from local_llama_integration import LocalLlamaIntegration
        
        print("✅ LocalLlamaIntegration imported successfully")
        
        # Initialize the client
        llama_client = LocalLlamaIntegration(
            model_name="llama3.2:3b",
            temperature=0.7
        )
        
        print(f"✅ LlamaClient initialized - Available: {llama_client.available}")
        
        if llama_client.available:
            # Test a simple query
            test_message = "Hello, can you help me understand power system analysis?"
            
            response = llama_client.generate(
                prompt=test_message,
                system_prompt="You are a helpful power system analysis assistant.",
                stream=False
            )
            
            print(f"✅ AI Response received:")
            print(f"User: {test_message}")
            print(f"AI: {response}")
            
        else:
            print("❌ Llama client not available")
            
    except Exception as e:
        print(f"❌ Error testing AI response: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_response()