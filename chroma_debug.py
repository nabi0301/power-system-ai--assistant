"""
Deep ChromaDB Investigation
==========================
"""

import chromadb
from chromadb.config import Settings

# Connect to the ChromaDB collection
client = chromadb.PersistentClient(
    path="rag_demo_storage/vector_db",
    settings=Settings(anonymized_telemetry=False)
)

try:
    collection = client.get_collection(name="power_system_knowledge")
    print(f"Collection loaded: {collection.name}")
    print(f"Document count: {collection.count()}")
    
    # Peek at some documents
    peek_result = collection.peek(limit=5)
    print(f"\nSample documents:")
    
    ids = peek_result.get('ids', [])
    documents = peek_result.get('documents', [])
    embeddings = peek_result.get('embeddings', [])
    metadatas = peek_result.get('metadatas', [])
    
    for i in range(min(3, len(ids))):
        print(f"\n{i+1}. ID: {ids[i]}")
        print(f"   Document length: {len(documents[i]) if documents[i] else 0}")
        
        # Safe check for embeddings
        has_embedding = False
        embedding_len = 0
        try:
            if embeddings is not None and i < len(embeddings):
                if embeddings[i] is not None and hasattr(embeddings[i], '__len__'):
                    embedding_len = len(embeddings[i])
                    has_embedding = True
        except Exception as e:
            print(f"   Embedding check error: {e}")
            pass
        
        print(f"   Has embedding: {'Yes' if has_embedding else 'No'}")
        print(f"   Embedding length: {embedding_len}")
        print(f"   Metadata: {metadatas[i] if metadatas and i < len(metadatas) else 'None'}")
        if documents[i]:
            print(f"   Content preview: {documents[i][:100]}...")
    
    # Try a direct query
    print(f"\n--- Testing Direct Query ---")
    try:
        query_result = collection.query(
            query_texts=["voltage"],
            n_results=5,
            include=['documents', 'distances', 'metadatas']
        )
        
        print(f"Query results: {len(query_result.get('ids', [[]])[0])}")
        
        if query_result.get('ids') and len(query_result['ids'][0]) > 0:
            print("First few results:")
            for i in range(min(3, len(query_result['ids'][0]))):
                print(f"  {i+1}. ID: {query_result['ids'][0][i]}")
                print(f"      Distance: {query_result['distances'][0][i]}")
                print(f"      Content: {query_result['documents'][0][i][:100]}...")
        else:
            print("No results returned from direct query")
            
    except Exception as e:
        print(f"Direct query failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if there are specific search issues
    print(f"\n--- Testing with different queries ---")
    test_queries = ["bus", "power", "voltage", "data"]
    
    for query in test_queries:
        try:
            result = collection.query(
                query_texts=[query],
                n_results=1,
                include=['distances']
            )
            count = len(result.get('ids', [[]])[0])
            print(f"Query '{query}': {count} results")
            
        except Exception as e:
            print(f"Query '{query}' failed: {e}")

except Exception as e:
    print(f"Failed to connect to collection: {e}")
    import traceback
    traceback.print_exc()