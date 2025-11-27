#!/usr/bin/env python3
"""Quick test of local LLaMA integration"""

import asyncio
from local_llama_integration import LocalLlamaIntegration

async def test_llama():
    """Test local LLaMA integration"""
    print("🧪 Testing Local LLaMA Integration...")
    
    # Create integration
    llama = LocalLlamaIntegration()
    
    if not llama.available:
        print("❌ LLaMA not available")
        return
    
    print(f"✅ Using model: {llama.model_name}")
    
    # Test simple generation
    try:
        result = await llama.generate_response(
            "What is voltage in power systems? Be very brief (1-2 sentences)."
        )
        print(f"🤖 Response: {result}")
        print("✅ Test successful!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_llama())