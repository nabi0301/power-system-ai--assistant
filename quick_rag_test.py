#!/usr/bin/env python3
"""
Quick RAG test with local LLaMA
"""

import asyncio
import time
from local_llama_integration import LocalLlamaIntegration

async def test_quick_rag():
    """Test RAG with a simple query"""
    print("🦙 Quick RAG Test with Local LLaMA")
    print("="*50)
    
    # Test LLaMA integration
    llama = LocalLlamaIntegration(timeout=60, max_tokens=500)  # Shorter timeout and response
    
    print(f"📋 Model info: {llama.get_model_info()}")
    
    if not llama.available:
        print("❌ Ollama not available!")
        return False
    
    print("✅ Ollama is available!")
    
    # Simple test query
    test_query = "What is voltage? Give a short answer."
    
    print(f"\n🧪 Testing query: {test_query}")
    start_time = time.time()
    
    try:
        response = await llama.generate_response(test_query)
        elapsed = time.time() - start_time
        
        print(f"🤖 Response ({elapsed:.1f}s):")
        print(f"   {response}")
        
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.1f}s: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_quick_rag())
    
    if success:
        print("\n🎉 Local LLaMA integration working!")
        print("\n📝 Next steps:")
        print("1. Open your app at http://127.0.0.1:8050")
        print("2. Click the chat button (💬)")
        print("3. Test with short questions first")
        print("4. Use queries like: 'What is voltage?' or 'Tell me about power systems'")
    else:
        print("\n❌ Integration test failed. Check Ollama setup.")