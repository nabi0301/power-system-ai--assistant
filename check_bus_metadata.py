#!/usr/bin/env python3
"""
Check bus_ids metadata in ChromaDB
"""

import chromadb
from chromadb.config import Settings

def check_bus_metadata():
    """Check how bus_ids are stored in metadata"""
    
    # Connect to ChromaDB
    client = chromadb.PersistentClient(
        path="rag_demo_storage/vector_db",
        settings=Settings(
            anonymized_telemetry=False,
            is_persistent=True
        )
    )
    
    # List all collections first
    collections = client.list_collections()
    print(f"Available collections: {[c.name for c in collections]}")
    
    if not collections:
        print("No collections found!")
        return
    
    # Use the first collection
    collection = collections[0]
    
    print(f"Collection: {collection.name}")
    print(f"Document count: {collection.count()}")
    
    # Get all documents and check bus_ids format
    all_docs = collection.get(include=['metadatas'])
    
    bus_id_formats = {}
    non_empty_bus_ids = []
    
    for metadata in all_docs['metadatas']:
        bus_ids = metadata.get('bus_ids', '')
        
        # Track format
        if bus_ids in bus_id_formats:
            bus_id_formats[bus_ids] += 1
        else:
            bus_id_formats[bus_ids] = 1
        
        # Collect non-empty examples
        if bus_ids and bus_ids != '[]':
            non_empty_bus_ids.append(bus_ids)
    
    print(f"\nBus ID formats found:")
    for format_str, count in sorted(bus_id_formats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  '{format_str}': {count} documents")
    
    print(f"\nNon-empty bus_ids examples:")
    for i, bus_id in enumerate(non_empty_bus_ids[:10]):
        print(f"  {i+1}. {bus_id}")
    
    # Try to find documents with specific bus IDs
    print(f"\nSearching for documents mentioning bus 1...")
    results = collection.query(
        query_texts=["bus 1"],
        n_results=5,
        include=['metadatas', 'documents']
    )
    
    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"  {i+1}. bus_ids: {meta.get('bus_ids', 'N/A')}")
        print(f"      Content: {doc[:100]}...")

if __name__ == "__main__":
    check_bus_metadata()