#!/usr/bin/env python3
"""
Test Local LLaMA Integration with RAG System
==========================================

This script tests the local LLaMA integration and RAG system
to ensure everything is working properly.

Usage:
    python test_local_llama_rag.py
"""

import asyncio
import sys
import time

async def test_ollama_standalone():
    """Test Ollama integration standalone"""
    print("🦙 Testing Local LLaMA Integration")
    print("=" * 50)
    
    try:
        from local_llama_integration import create_local_llama_integration
        
        print("🔍 Creating LLaMA integration...")
        llama = create_local_llama_integration()
        
        print(f"📋 Model info: {llama.get_model_info()}")
        
        if not llama.available:
            print("❌ Ollama not available!")
            print("\n🛠️ Setup instructions:")
            print("1. Run: setup_local_llama.bat")
            print("2. Or manually:")
            print("   - Install Ollama: https://ollama.ai/")
            print("   - Run: ollama pull llama2")
            print("   - Start: ollama serve")
            return False
        
        print("✅ Ollama is available!")
        
        # Test simple generation
        print("\n🧪 Testing simple generation...")
        start_time = time.time()
        
        response = await llama.generate_response(
            "What is voltage in electrical power systems? Give a brief technical explanation.",
            system_prompt="You are a power systems engineer. Provide concise, technical answers."
        )
        
        end_time = time.time()
        
        print(f"🤖 Response ({end_time - start_time:.1f}s):")
        print(f"   {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}")
        return False

async def test_rag_with_llama():
    """Test RAG system with LLaMA integration"""
    print("\n🔍 Testing RAG System with Local LLaMA")
    print("=" * 50)
    
    try:
        from power_system_rag_core import PowerSystemRAG
        
        print("🚀 Initializing RAG system...")
        rag = PowerSystemRAG(
            db_path="data.db",
            embedding_model="all-MiniLM-L6-v2",
            persist_directory="rag_demo_storage"
        )
        
        print(f"📊 RAG indexed: {rag.is_indexed}")
        
        if not rag.is_indexed:
            print("⚠️ Database not indexed. RAG search may not work optimally.")
        
        # Test RAG query
        print("\n🧪 Testing RAG query with LLaMA...")
        start_time = time.time()
        
        response = await rag.query(
            question="What are the voltage levels in the power system data?",
            max_results=3,
            include_sources=True
        )
        
        end_time = time.time()
        
        print(f"\n📝 RAG Response ({end_time - start_time:.1f}s):")
        print(f"   Answer: {response['answer']}")
        print(f"   Confidence: {response['confidence']:.1%}")
        print(f"   Sources: {len(response['sources'])}")
        
        if response['sources']:
            print("\n📚 Top sources:")
            for i, source in enumerate(response['sources'][:2], 1):
                print(f"   {i}. {source.get('chunk_id', 'Unknown')} (Score: {source.get('score', 0):.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing RAG: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🦙 Local LLaMA + RAG Integration Test")
    print("=" * 60)
    print()
    
    # Test 1: Ollama standalone
    ollama_ok = await test_ollama_standalone()
    
    if not ollama_ok:
        print("\n⚠️ Ollama test failed. Fix Ollama setup before testing RAG.")
        return
    
    # Test 2: RAG with LLaMA
    rag_ok = await test_rag_with_llama()
    
    print("\n" + "=" * 60)
    if ollama_ok and rag_ok:
        print("🎉 All tests passed! Your local LLaMA + RAG system is working!")
        print("\n🚀 You can now use:")
        print("   python power_system_rag_demo.py --query 'Your question'")
        print("   python data_viz_fall.py  # (with RAG chat enabled)")
    else:
        print("❌ Some tests failed. Check the errors above.")
    print()

if __name__ == "__main__":
    asyncio.run(main())