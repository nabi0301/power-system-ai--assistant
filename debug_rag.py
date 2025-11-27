"""
Debug RAG Retrieval Issues
=========================

This script helps debug why queries aren't returning results.
"""

import asyncio
import logging
import sys
import os
sys.path.append(os.getcwd())

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from power_system_rag_core import PowerSystemRAG

async def debug_rag():
    """Debug the RAG retrieval pipeline"""
    
    print("🔍 Starting RAG Debug Session...")
    
    # Initialize RAG system
    rag = PowerSystemRAG(
        db_path="data.db",
        embedding_model="all-MiniLM-L6-v2",
        vector_db_backend="chroma",
        persist_directory="rag_demo_storage"
    )
    
    # Check system status
    print("\n📊 System Status:")
    stats = rag.get_system_stats()
    print(f"   Indexed: {stats.get('is_indexed')}")
    print(f"   Total documents: {stats.get('total_documents', 0)}")
    print(f"   Backend: {stats.get('selected_backend')}")
    
    if not stats.get('is_indexed') or stats.get('total_documents', 0) == 0:
        print("❌ No documents indexed! Run --index first.")
        return
    
    # Test direct vector database search
    print("\n🔍 Testing Direct Vector Search:")
    try:
        # Test with simple query
        results = rag.vector_db.search(
            query_text="voltage",
            k=5,
            similarity_threshold=0.0  # No threshold to see all results
        )
        
        print(f"   Direct search results: {len(results)}")
        
        if results:
            for i, result in enumerate(results[:3], 1):
                print(f"   {i}. ID: {result.chunk_id}")
                print(f"      Score: {result.similarity_score:.4f}")
                print(f"      Preview: {result.content[:100]}...")
                print()
        else:
            print("   ❌ No results from direct search")
            
            # Try to peek at what's actually in the database
            print("\n🔍 Checking ChromaDB collection:")
            try:
                collection = rag.vector_db.db.collection
                count = collection.count()
                print(f"   ChromaDB document count: {count}")
                
                if count > 0:
                    # Get a sample of documents
                    sample = collection.peek(limit=3)
                    print(f"   Sample documents: {len(sample.get('ids', []))}")
                    
                    for i, (doc_id, doc) in enumerate(zip(sample.get('ids', []), sample.get('documents', []))):
                        print(f"   Sample {i+1}: {doc_id}")
                        print(f"      Content: {doc[:100] if doc else 'No content'}...")
                        
            except Exception as e:
                print(f"   ❌ Error accessing ChromaDB: {e}")
    
    except Exception as e:
        print(f"   ❌ Direct search failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test embeddings generation
    print("\n🔢 Testing Embeddings:")
    try:
        embedding_results = await rag.embeddings_engine.embed_documents(["voltage violations"])
        if embedding_results and len(embedding_results) > 0:
            result = embedding_results[0]
            print(f"   Embedding success: {result.success}")
            print(f"   Embedding dimension: {result.dimension}")
            print(f"   Model: {result.model_name}")
            
            if result.success:
                # Test search with the embedding
                search_results = rag.vector_db.search(
                    query_text="voltage violations",
                    query_embedding=result.embedding,
                    k=10,
                    similarity_threshold=0.0
                )
                print(f"   Search with embedding: {len(search_results)} results")
                
        else:
            print("   ❌ No embedding results")
            
    except Exception as e:
        print(f"   ❌ Embedding test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test retriever directly
    print("\n🎯 Testing Retriever:")
    try:
        retrieval_results = await rag.retriever.retrieve(
            query="voltage violations",
            k=5
        )
        print(f"   Retriever results: {len(retrieval_results)}")
        
        if retrieval_results:
            for i, result in enumerate(retrieval_results[:2], 1):
                print(f"   {i}. ID: {result.chunk_id}")
                print(f"      Final Score: {result.final_score:.4f}")
                print(f"      Vector Score: {result.vector_score:.4f}")
                print(f"      Rerank Score: {result.rerank_score:.4f}")
                print()
        
    except Exception as e:
        print(f"   ❌ Retriever test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Debug session complete!")

if __name__ == "__main__":
    asyncio.run(debug_rag())