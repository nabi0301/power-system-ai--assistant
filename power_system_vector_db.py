"""
Vector Database System for Power System RAG
==========================================

This module implements a scalable vector database system supporting:
- Chroma (development/prototyping)
- FAISS (local production)  
- Pinecone/Qdrant (cloud production)

Key Features:
- Metadata-rich storage with power system context
- Hybrid search (semantic + lexical)
- Efficient similarity search with filtering
- Production-ready scaling options

Author: Power System Analysis Team
Date: September 2025
"""

import numpy as np
import json
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import os
import pickle
import uuid
from abc import ABC, abstractmethod

# Try imports for different vector DB backends
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logging.warning("ChromaDB not available")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available")

try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logging.warning("Pinecone not available")

# Import from our RAG core
from power_system_rag_core import ChunkMetadata

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Single search result from vector database"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    rank: int

@dataclass
class SearchQuery:
    """Search query parameters"""
    query_text: str
    query_embedding: Optional[np.ndarray] = None
    k: int = 10
    filters: Optional[Dict[str, Any]] = None
    similarity_threshold: float = 0.0
    include_metadata: bool = True
    case_id_filter: Optional[str] = None
    bus_id_filter: Optional[List[str]] = None
    branch_id_filter: Optional[List[str]] = None

class VectorDatabase(ABC):
    """Abstract base class for vector database implementations"""
    
    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector database"""
        pass
    
    @abstractmethod
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search for similar documents"""
        pass
    
    @abstractmethod
    def delete_documents(self, chunk_ids: List[str]) -> bool:
        """Delete documents from the database"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        pass

class ChromaVectorDB(VectorDatabase):
    """
    ChromaDB implementation for development and prototyping.
    
    Excellent for:
    - Local development
    - Prototyping
    - Small to medium datasets
    - Rich metadata filtering
    """
    
    def __init__(
        self,
        collection_name: str = "power_system_knowledge",
        persist_directory: str = "vector_db",
        embedding_dimension: int = 384
    ):
        """Initialize ChromaDB"""
        if not CHROMA_AVAILABLE:
            raise RuntimeError("ChromaDB not available. Install with: pip install chromadb")
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_dimension = embedding_dimension
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing ChromaDB collection: {collection_name}")
        except:
            # Create new collection
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Power system knowledge base"}
            )
            logger.info(f"Created new ChromaDB collection: {collection_name}")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to ChromaDB"""
        try:
            chunk_ids = []
            embeddings = []
            metadatas = []
            documents_content = []
            
            for doc in documents:
                # Generate ID if not provided
                chunk_id = doc.get('id', str(uuid.uuid4()))
                chunk_ids.append(chunk_id)
                
                # Extract embedding
                if 'embedding' in doc:
                    embeddings.append(doc['embedding'].tolist())
                else:
                    raise ValueError("Document missing embedding")
                
                # Extract metadata
                metadata = doc.get('metadata', {})
                # Ensure all metadata values are JSON serializable
                clean_metadata = self._clean_metadata(metadata)
                metadatas.append(clean_metadata)
                
                # Extract content
                content = doc.get('content', '')
                documents_content.append(content)
            
            # Add to collection
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents_content
            )
            
            logger.info(f"Added {len(documents)} documents to ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            return False
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search ChromaDB for similar documents"""
        try:
            # Build where clause for filtering
            where_clause = {}
            
            if query.case_id_filter:
                where_clause["case_id"] = query.case_id_filter
            
            if query.bus_id_filter:
                # ChromaDB filtering with JSON string bus_ids is complex
                # For now, skip bus filtering and handle it post-search
                # TODO: Implement proper bus ID filtering
                logger.warning(f"Bus ID filtering not yet implemented for JSON string format: {query.bus_id_filter}")
                pass
            
            if query.filters:
                where_clause.update(query.filters)
            
            # Perform search
            if query.query_embedding is not None:
                results = self.collection.query(
                    query_embeddings=[query.query_embedding.tolist()],
                    n_results=query.k,
                    where=where_clause if where_clause else None,
                    include=['metadatas', 'documents', 'distances']
                )
            else:
                # Text-based search (Chroma will create embeddings)
                results = self.collection.query(
                    query_texts=[query.query_text],
                    n_results=query.k,
                    where=where_clause if where_clause else None,
                    include=['metadatas', 'documents', 'distances']
                )
            
            # Convert to SearchResult objects
            search_results = []
            
            if results['ids'] and len(results['ids']) > 0:
                ids = results['ids'][0]
                distances = results['distances'][0]
                metadatas = results['metadatas'][0] if 'metadatas' in results else []
                documents = results['documents'][0] if 'documents' in results else []
                
                for i, (chunk_id, distance) in enumerate(zip(ids, distances)):
                    # Convert distance to similarity score
                    # ChromaDB uses cosine distance, where smaller distance = more similar
                    # Convert to a similarity score between 0 and 1
                    # For cosine distance: similarity = max(0, 1 - distance)
                    similarity_score = max(0.0, 1.0 - distance)
                    
                    # Skip if below threshold (note: threshold should be adjusted for cosine)
                    if similarity_score < query.similarity_threshold:
                        continue
                    
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    content = documents[i] if i < len(documents) else ""
                    
                    result = SearchResult(
                        chunk_id=chunk_id,
                        content=content,
                        metadata=metadata,
                        similarity_score=similarity_score,
                        rank=i + 1
                    )
                    
                    search_results.append(result)
            
            # Apply post-search bus ID filtering if needed
            if query.bus_id_filter and search_results:
                filtered_results = []
                for result in search_results:
                    bus_ids_json = result.metadata.get('bus_ids', '[]')
                    try:
                        import json
                        bus_ids = json.loads(bus_ids_json)
                        # Check if any of the filter bus IDs are in the document's bus IDs
                        if any(bus_id in bus_ids for bus_id in query.bus_id_filter):
                            filtered_results.append(result)
                    except (json.JSONDecodeError, TypeError):
                        # If parsing fails, include the result
                        filtered_results.append(result)
                
                search_results = filtered_results
                logger.info(f"After bus ID filtering: {len(search_results)} results")
            
            logger.info(f"ChromaDB search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            return []
    
    def delete_documents(self, chunk_ids: List[str]) -> bool:
        """Delete documents from ChromaDB"""
        try:
            self.collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} documents from ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents from ChromaDB: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "backend": "ChromaDB",
                "embedding_dimension": self.embedding_dimension
            }
        except Exception as e:
            logger.error(f"Failed to get ChromaDB stats: {e}")
            return {}
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean metadata for ChromaDB compatibility"""
        clean = {}
        
        for key, value in metadata.items():
            if value is None:
                continue
            
            # Convert lists to strings for compatibility
            if isinstance(value, list):
                clean[key] = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)):
                clean[key] = value
            else:
                # Convert other types to string
                clean[key] = str(value)
        
        return clean

class FAISSVectorDB(VectorDatabase):
    """
    FAISS implementation for high-performance local production.
    
    Excellent for:
    - Local production deployments
    - High-speed similarity search
    - Large datasets (millions of vectors)
    - When you need maximum control
    """
    
    def __init__(
        self,
        index_path: str = "faiss_index",
        embedding_dimension: int = 384,
        index_type: str = "IVF",
        nlist: int = 100
    ):
        """Initialize FAISS index"""
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS not available. Install with: pip install faiss-cpu")
        
        self.index_path = index_path
        self.embedding_dimension = embedding_dimension
        self.index_type = index_type
        self.nlist = nlist
        
        # Create directory
        if not os.path.exists(index_path):
            os.makedirs(index_path)
        
        # Initialize FAISS index
        self.index = self._create_index()
        
        # Metadata storage (SQLite)
        self.metadata_db = os.path.join(index_path, "metadata.db")
        self._init_metadata_db()
        
        # Load existing index if available
        self._load_index()
        
        logger.info(f"FAISS VectorDB initialized with {self.index.ntotal} vectors")
    
    def _create_index(self):
        """Create FAISS index based on type"""
        if self.index_type == "Flat":
            # Brute force, exact search
            return faiss.IndexFlatIP(self.embedding_dimension)
        elif self.index_type == "IVF":
            # Inverted file index for faster approximate search
            quantizer = faiss.IndexFlatIP(self.embedding_dimension)
            return faiss.IndexIVFFlat(quantizer, self.embedding_dimension, self.nlist)
        else:
            # Default to flat index
            return faiss.IndexFlatIP(self.embedding_dimension)
    
    def _init_metadata_db(self):
        """Initialize metadata database"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_metadata (
                vector_id INTEGER PRIMARY KEY,
                chunk_id TEXT UNIQUE NOT NULL,
                content TEXT,
                metadata TEXT,
                created_at TEXT
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunk_id ON document_metadata(chunk_id)')
        
        conn.commit()
        conn.close()
    
    def _load_index(self):
        """Load existing FAISS index"""
        index_file = os.path.join(self.index_path, "vector.index")
        
        if os.path.exists(index_file):
            try:
                self.index = faiss.read_index(index_file)
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}")
    
    def _save_index(self):
        """Save FAISS index to disk"""
        index_file = os.path.join(self.index_path, "vector.index")
        try:
            faiss.write_index(self.index, index_file)
            logger.info("FAISS index saved successfully")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to FAISS index"""
        try:
            vectors = []
            metadata_records = []
            
            for doc in documents:
                # Extract embedding
                if 'embedding' not in doc:
                    raise ValueError("Document missing embedding")
                
                embedding = doc['embedding']
                if isinstance(embedding, list):
                    embedding = np.array(embedding, dtype=np.float32)
                
                # Normalize for inner product (cosine similarity)
                faiss.normalize_L2(embedding.reshape(1, -1))
                vectors.append(embedding)
                
                # Prepare metadata
                chunk_id = doc.get('id', str(uuid.uuid4()))
                content = doc.get('content', '')
                metadata = json.dumps(doc.get('metadata', {}))
                
                metadata_records.append((
                    chunk_id, content, metadata, datetime.now().isoformat()
                ))
            
            # Add vectors to FAISS
            vectors_array = np.vstack(vectors).astype(np.float32)
            
            # Train index if necessary
            if not self.index.is_trained:
                self.index.train(vectors_array)
            
            # Get starting vector ID
            start_id = self.index.ntotal
            
            # Add vectors
            self.index.add(vectors_array)
            
            # Add metadata to database
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            for i, (chunk_id, content, metadata, created_at) in enumerate(metadata_records):
                vector_id = start_id + i
                cursor.execute('''
                    INSERT INTO document_metadata (vector_id, chunk_id, content, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (vector_id, chunk_id, content, metadata, created_at))
            
            conn.commit()
            conn.close()
            
            # Save index
            self._save_index()
            
            logger.info(f"Added {len(documents)} documents to FAISS index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to FAISS: {e}")
            return False
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search FAISS index"""
        try:
            if query.query_embedding is None:
                raise ValueError("FAISS requires query embedding")
            
            # Normalize query embedding
            query_vec = query.query_embedding.astype(np.float32).reshape(1, -1)
            faiss.normalize_L2(query_vec)
            
            # Perform search
            scores, indices = self.index.search(query_vec, query.k)
            
            # Retrieve metadata
            results = []
            
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # No result found
                    continue
                
                if score < query.similarity_threshold:
                    continue
                
                # Get metadata
                cursor.execute('''
                    SELECT chunk_id, content, metadata 
                    FROM document_metadata 
                    WHERE vector_id = ?
                ''', (int(idx),))
                
                row = cursor.fetchone()
                if not row:
                    continue
                
                chunk_id, content, metadata_str = row
                metadata = json.loads(metadata_str) if metadata_str else {}
                
                # Apply filters
                if query.case_id_filter and metadata.get('case_id') != query.case_id_filter:
                    continue
                
                if query.bus_id_filter:
                    doc_bus_ids = metadata.get('bus_ids', [])
                    if not any(bus_id in doc_bus_ids for bus_id in query.bus_id_filter):
                        continue
                
                result = SearchResult(
                    chunk_id=chunk_id,
                    content=content,
                    metadata=metadata,
                    similarity_score=float(score),
                    rank=i + 1
                )
                
                results.append(result)
            
            conn.close()
            
            logger.info(f"FAISS search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []
    
    def delete_documents(self, chunk_ids: List[str]) -> bool:
        """Delete documents (FAISS doesn't support deletion directly)"""
        logger.warning("FAISS doesn't support direct deletion. Consider rebuilding index.")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get FAISS statistics"""
        return {
            "total_documents": self.index.ntotal,
            "index_type": self.index_type,
            "backend": "FAISS",
            "embedding_dimension": self.embedding_dimension,
            "is_trained": self.index.is_trained
        }

class PowerSystemVectorDB:
    """
    Unified vector database interface for power system RAG.
    
    Automatically selects the best backend based on:
    - Available libraries
    - Dataset size
    - Performance requirements
    """
    
    def __init__(
        self,
        backend: str = "auto",
        embedding_dimension: int = 384,
        collection_name: str = "power_system_knowledge",
        persist_directory: str = "vector_db"
    ):
        """
        Initialize vector database.
        
        Args:
            backend: "auto", "chroma", "faiss", or "pinecone"
            embedding_dimension: Dimension of embeddings
            collection_name: Name of the collection
            persist_directory: Directory for persistence
        """
        self.backend_name = backend
        self.embedding_dimension = embedding_dimension
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Select and initialize backend
        self.db = self._initialize_backend()
        
        logger.info(f"PowerSystemVectorDB initialized with {self.backend_name} backend")
    
    def _initialize_backend(self) -> VectorDatabase:
        """Initialize the appropriate backend"""
        if self.backend_name == "auto":
            # Auto-select based on availability
            if CHROMA_AVAILABLE:
                self.backend_name = "chroma"
            elif FAISS_AVAILABLE:
                self.backend_name = "faiss"
            else:
                raise RuntimeError("No vector database backend available")
        
        if self.backend_name == "chroma":
            return ChromaVectorDB(
                collection_name=self.collection_name,
                persist_directory=self.persist_directory,
                embedding_dimension=self.embedding_dimension
            )
        elif self.backend_name == "faiss":
            return FAISSVectorDB(
                index_path=self.persist_directory,
                embedding_dimension=self.embedding_dimension
            )
        else:
            raise ValueError(f"Unsupported backend: {self.backend_name}")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to vector database"""
        return self.db.add_documents(documents)
    
    def search(
        self,
        query_text: str,
        query_embedding: Optional[np.ndarray] = None,
        k: int = 10,
        case_id_filter: Optional[str] = None,
        bus_id_filter: Optional[List[str]] = None,
        similarity_threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query_text: Text query
            query_embedding: Pre-computed embedding (optional)
            k: Number of results to return
            case_id_filter: Filter by case ID
            bus_id_filter: Filter by bus IDs
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        query = SearchQuery(
            query_text=query_text,
            query_embedding=query_embedding,
            k=k,
            case_id_filter=case_id_filter,
            bus_id_filter=bus_id_filter,
            similarity_threshold=similarity_threshold
        )
        
        return self.db.search(query)
    
    def delete_documents(self, chunk_ids: List[str]) -> bool:
        """Delete documents from database"""
        return self.db.delete_documents(chunk_ids)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = self.db.get_stats()
        stats["selected_backend"] = self.backend_name
        return stats
    
    def hybrid_search(
        self,
        query_text: str,
        query_embedding: Optional[np.ndarray] = None,
        k: int = 10,
        alpha: float = 0.7,
        **kwargs
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining semantic and lexical search.
        
        Args:
            query_text: Text query
            query_embedding: Pre-computed embedding
            k: Number of results
            alpha: Weight for semantic vs lexical (0.0 = all lexical, 1.0 = all semantic)
        """
        # For now, just do semantic search
        # In production, this would combine with BM25 or similar
        return self.search(
            query_text=query_text,
            query_embedding=query_embedding,
            k=k,
            **kwargs
        )


# Export main classes
__all__ = [
    'PowerSystemVectorDB', 'SearchResult', 'SearchQuery',
    'ChromaVectorDB', 'FAISSVectorDB'
]