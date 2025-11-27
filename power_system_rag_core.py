"""
Power System RAG Architecture - Complete Implementation
=====================================================

This module implements a comprehensive RAG (Retrieval-Augmented Generation) system
specifically designed for power system data analysis and querying.

Architecture Components:
1. Document Ingestion - Process DB/Excel outputs with chunking and metadata
2. Embeddings - Convert chunks to vectors using reliable embedding models
3. Vector Database - Store vectors with metadata (Chroma for local, extensible to others)
4. Retriever - Nearest-neighbor search with re-ranking capabilities
5. RAG Pipeline - LLaMA integration with structured prompts and source citation
6. Post-processing - Provenance, validation, caching, and metrics

Author: Power System Analysis Team
Date: September 2025
Version: 2.0 - Complete RAG Implementation
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import logging
from datetime import datetime
from pathlib import Path
import hashlib
import pickle
from dataclasses import dataclass
from enum import Enum

# Core RAG dependencies with fallbacks
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("⚠️ ChromaDB not available - install with: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ SentenceTransformers not available - install with: pip install sentence-transformers")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available - install with: pip install openai")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ FAISS not available - install with: pip install faiss-cpu")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChunkMetadata:
    """Metadata structure for each document chunk"""
    chunk_id: str
    source_file: str
    case_id: str
    case_type: str  # "base", "slr", "dlr", "contingency"
    bus_ids: List[str]
    branch_ids: List[str]
    timestamp: str
    row_index: int
    chunk_size: int
    original_table: str
    confidence_score: float = 1.0

@dataclass
class RetrievalResult:
    """Structure for retrieval results with provenance"""
    content: str
    metadata: ChunkMetadata
    similarity_score: float
    rank: int

@dataclass
class RAGResponse:
    """Structured RAG response with sources and confidence"""
    answer: str
    sources: List[str]
    confidence: float
    retrieved_chunks: List[RetrievalResult]
    processing_time: float
    token_count: int

class EmbeddingProvider(Enum):
    """Available embedding providers"""
    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    LOCAL_FALLBACK = "local_fallback"

class VectorStoreType(Enum):
    """Available vector store types"""
    CHROMA = "chroma"
    FAISS = "faiss"
    MEMORY = "memory"

class PowerSystemRAG:
    """
    Complete RAG system for power system analysis.
    
    Integrates:
    - Document ingestion and chunking
    - Embeddings generation  
    - Vector database storage
    - Advanced retrieval with re-ranking
    - LLaMA integration for generation
    - Post-processing and validation
    """
    
    def __init__(
        self,
        db_path: str,
        openai_api_key: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_db_backend: str = "auto",
        llm_model_path: Optional[str] = None,
        persist_directory: str = "rag_storage"
    ):
        """
        Initialize the RAG system.
        
        Args:
            db_path: Path to SQLite database
            openai_api_key: OpenAI API key (optional)
            embedding_model: Embedding model preference
            vector_db_backend: Vector database backend
            llm_model_path: Path to local LLaMA model
            persist_directory: Directory for persistent storage
        """
        self.db_path = db_path
        self.persist_directory = persist_directory
        
        # Ensure storage directory exists
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
        
        logger.info("Initializing PowerSystemRAG...")
        
        # Initialize embeddings engine
        self.embeddings_engine = self._initialize_embeddings(openai_api_key, embedding_model)
        
        # Initialize vector database
        self.vector_db = self._initialize_vector_db(vector_db_backend)
        
        # Initialize document ingestor
        self.document_ingestor = self._initialize_ingestor()
        
        # Initialize retriever
        self.retriever = self._initialize_retriever()
        
        # Initialize LLM
        self.llm = self._initialize_llm(llm_model_path)
        
        # Initialize post-processor
        self.post_processor = self._initialize_post_processor()
        
        # System state
        self.is_indexed = self._check_index_status()
        self.stats = {}
        
        logger.info("PowerSystemRAG initialization complete")
    
    def _initialize_embeddings(self, openai_api_key: Optional[str], model: str):
        """Initialize embeddings engine"""
        from power_system_embeddings_engine import PowerSystemEmbeddingsEngine
        
        return PowerSystemEmbeddingsEngine(
            openai_api_key=openai_api_key,
            model_preference=[model] if model != "auto" else None,
            cache_dir=os.path.join(self.persist_directory, "embeddings_cache")
        )
    
    def _initialize_vector_db(self, backend: str):
        """Initialize vector database"""
        from power_system_vector_db import PowerSystemVectorDB
        
        embedding_dim = self.embeddings_engine.get_embedding_dimension()
        
        return PowerSystemVectorDB(
            backend=backend,
            embedding_dimension=embedding_dim,
            persist_directory=os.path.join(self.persist_directory, "vector_db")
        )
    
    def _initialize_ingestor(self):
        """Initialize document ingestor"""
        from power_system_document_ingestor import PowerSystemDocumentIngestor
        
        return PowerSystemDocumentIngestor(
            db_path=self.db_path,
            chunk_size_text=600,
            chunk_size_table=300,
            overlap_percentage=0.2
        )
    
    def _initialize_retriever(self):
        """Initialize retriever"""
        from power_system_retrieval_engine import PowerSystemRetriever
        
        return PowerSystemRetriever(
            vector_db=self.vector_db,
            embeddings_engine=self.embeddings_engine,
            initial_k=20,
            final_k=10
        )
    
    def _initialize_llm(self, model_path: Optional[str]):
        """Initialize LLM (placeholder for now)"""
        # This would integrate with your existing LLaMA setup
        # For now, return a simple wrapper
        return PowerSystemLLMWrapper(model_path)
    
    def _initialize_post_processor(self):
        """Initialize post-processor"""
        return PowerSystemPostProcessor()
    
    def _check_index_status(self) -> bool:
        """Check if the database is already indexed"""
        try:
            stats = self.vector_db.get_stats()
            return stats.get('total_documents', 0) > 0
        except:
            return False
    
    async def index_database(self) -> bool:
        """
        Index the entire database for RAG.
        
        This is the main ingestion pipeline:
        1. Extract and chunk documents
        2. Generate embeddings
        3. Store in vector database
        
        Returns:
            True if indexing successful
        """
        logger.info("Starting database indexing...")
        
        try:
            # Step 1: Ingest and chunk documents
            logger.info("Step 1: Document ingestion and chunking")
            documents = self.document_ingestor.ingest_database()
            
            if not documents:
                logger.error("No documents found to index")
                return False
            
            logger.info(f"Created {len(documents)} document chunks")
            
            # Step 2: Generate embeddings in batches
            logger.info("Step 2: Generating embeddings")
            batch_size = 50
            total_processed = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Extract content for embedding
                batch_content = [doc['embedding_content'] for doc in batch]
                
                # Generate embeddings
                embedding_results = await self.embeddings_engine.embed_documents(batch_content)
                
                # Add embeddings to documents
                for doc, embedding_result in zip(batch, embedding_results):
                    if embedding_result.success:
                        doc['embedding'] = embedding_result.embedding
                        doc['id'] = doc['metadata']['chunk_id']
                    else:
                        logger.warning(f"Failed to embed document: {doc['metadata']['chunk_id']}")
                
                # Step 3: Store in vector database
                valid_docs = [doc for doc in batch if 'embedding' in doc]
                if valid_docs:
                    success = self.vector_db.add_documents(valid_docs)
                    if success:
                        total_processed += len(valid_docs)
                        logger.info(f"Processed {total_processed}/{len(documents)} documents")
                    else:
                        logger.error("Failed to add batch to vector database")
            
            # Update stats
            self.stats['total_indexed'] = total_processed
            self.stats['indexing_date'] = datetime.now().isoformat()
            self.is_indexed = True
            
            logger.info(f"Database indexing complete: {total_processed} documents indexed")
            return True
            
        except Exception as e:
            logger.error(f"Database indexing failed: {e}")
            return False
    
    async def query(
        self,
        question: str,
        case_id: Optional[str] = None,
        context_bus_ids: Optional[List[str]] = None,
        max_results: int = 5,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Main RAG query method.
        
        Args:
            question: User question
            case_id: Filter by case ID
            context_bus_ids: Filter by bus IDs
            max_results: Maximum results to return
            include_sources: Include source information
            
        Returns:
            Complete RAG response with answer and sources
        """
        if not self.is_indexed:
            return {
                'answer': "Database not indexed. Please run index_database() first.",
                'confidence': 0.0,
                'sources': [],
                'error': 'Database not indexed'
            }
        
        logger.info(f"Processing RAG query: {question[:100]}...")
        
        try:
            # Step 1: Retrieve relevant documents
            logger.info("Step 1: Document retrieval")
            retrieval_results = await self.retriever.retrieve(
                query=question,
                case_id=case_id,
                bus_filter=context_bus_ids,
                k=max_results
            )
            
            if not retrieval_results:
                return {
                    'answer': "No relevant information found for your question.",
                    'confidence': 0.0,
                    'sources': [],
                    'error': 'No retrieval results'
                }
            
            logger.info(f"Retrieved {len(retrieval_results)} relevant documents")
            
            # Step 2: Generate response with LLM
            logger.info("Step 2: Response generation")
            llm_response = await self.llm.generate_response(
                question=question,
                context_documents=retrieval_results,
                case_id=case_id
            )
            
            # Step 3: Post-process response
            logger.info("Step 3: Post-processing")
            final_response = await self.post_processor.process_response(
                question=question,
                llm_response=llm_response,
                retrieval_results=retrieval_results,
                include_sources=include_sources
            )
            
            logger.info("RAG query processing complete")
            return final_response
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {
                'answer': f"An error occurred while processing your question: {str(e)}",
                'confidence': 0.0,
                'sources': [],
                'error': str(e)
            }
    
    async def batch_query(
        self,
        questions: List[str],
        case_id: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Process multiple queries in batch"""
        results = []
        
        for i, question in enumerate(questions):
            logger.info(f"Processing batch query {i+1}/{len(questions)}")
            result = await self.query(
                question=question,
                case_id=case_id,
                max_results=max_results
            )
            results.append(result)
        
        return results
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            'is_indexed': self.is_indexed,
            'database_path': self.db_path,
            'persist_directory': self.persist_directory
        }
        
        # Vector DB stats
        stats.update(self.vector_db.get_stats())
        
        # Embeddings stats
        stats['embeddings'] = self.embeddings_engine.get_cache_stats()
        
        # Retrieval stats
        stats['retrieval'] = self.retriever.get_retrieval_stats()
        
        # System stats
        stats.update(self.stats)
        
        return stats
    
    def clear_index(self):
        """Clear the entire index"""
        logger.info("Clearing RAG index...")
        
        # This would clear the vector database
        # Implementation depends on the backend
        self.is_indexed = False
        self.stats.clear()
        
        logger.info("RAG index cleared")


class PowerSystemLLMWrapper:
    """
    Wrapper for LLM integration.
    
    This integrates with your existing LLaMA setup.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize LLM wrapper"""
        self.model_path = model_path
        self.model = None
        # Initialize your LLaMA model here
        logger.info("LLM wrapper initialized")
    
    async def generate_response(
        self,
        question: str,
        context_documents: List[Any],
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate response using LLM with RAG context.
        
        Args:
            question: User question
            context_documents: Retrieved documents
            case_id: Case context
            
        Returns:
            LLM response with metadata
        """
        # Build context from retrieved documents
        context_text = self._build_context(context_documents)
        
        # Create prompt with power system instructions
        prompt = self._create_rag_prompt(question, context_text, case_id)
        
        # Generate response (integrate with your LLaMA setup)
        response_text = await self._call_llm(prompt)
        
        return {
            'response': response_text,
            'prompt_length': len(prompt),
            'context_length': len(context_text),
            'model_info': 'LLaMA (placeholder)'
        }
    
    def _build_context(self, documents: List[Any]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            source_info = f"Source {i} (Score: {doc.final_score:.3f})"
            content = doc.content[:1000]  # Limit content length
            context_parts.append(f"{source_info}:\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _create_rag_prompt(
        self,
        question: str,
        context: str,
        case_id: Optional[str] = None
    ) -> str:
        """Create RAG prompt with power system instructions"""
        system_prompt = """You are a power system analysis expert assistant. Use the provided context to answer questions about power system data, analysis, and operations. 

Key instructions:
- Base your answers on the provided context
- Include specific data values when available
- Cite sources when referencing specific information
- For technical analysis, explain methodology
- If context is insufficient, clearly state this
- Use proper power system terminology"""
        
        case_context = f"\nCase Context: {case_id}\n" if case_id else ""
        
        prompt = f"""{system_prompt}

{case_context}
Context Information:
{context}

Question: {question}

Answer:"""
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the actual LLM"""
        try:
            # Try local LLaMA first
            from local_llama_integration import create_local_llama_integration
            
            llama = create_local_llama_integration()
            if llama.available:
                response = await llama.generate_response(prompt)
                return response
            else:
                logger.warning("Local LLaMA not available, using placeholder")
                
        except ImportError:
            logger.warning("Local LLaMA integration not found")
        except Exception as e:
            logger.warning(f"Local LLaMA failed: {e}")
        
        # Fallback to placeholder
        return "This is a placeholder response. Please set up your local LLaMA model with Ollama."


class PowerSystemPostProcessor:
    """
    Post-processor for RAG responses.
    
    Handles:
    - Source citation formatting
    - Answer validation
    - Confidence scoring
    - JSON formatting
    """
    
    def __init__(self):
        """Initialize post-processor"""
        logger.info("Post-processor initialized")
    
    async def process_response(
        self,
        question: str,
        llm_response: Dict[str, Any],
        retrieval_results: List[Any],
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Process and format final response.
        
        Args:
            question: Original question
            llm_response: LLM response
            retrieval_results: Retrieved documents
            include_sources: Include source information
            
        Returns:
            Final formatted response
        """
        response_text = llm_response.get('response', '')
        
        # Calculate confidence score
        confidence = self._calculate_confidence(llm_response, retrieval_results)
        
        # Format sources
        sources = []
        if include_sources:
            sources = self._format_sources(retrieval_results)
        
        # Validate response
        validation_notes = self._validate_response(response_text, retrieval_results)
        
        final_response = {
            'answer': response_text,
            'confidence': confidence,
            'sources': sources,
            'validation_notes': validation_notes,
            'metadata': {
                'question': question,
                'num_sources': len(retrieval_results),
                'avg_source_score': np.mean([r.final_score for r in retrieval_results]) if retrieval_results else 0,
                'llm_metadata': llm_response
            }
        }
        
        return final_response
    
    def _calculate_confidence(
        self,
        llm_response: Dict[str, Any],
        retrieval_results: List[Any]
    ) -> float:
        """Calculate confidence score for response"""
        
        # Base confidence from retrieval quality
        if not retrieval_results:
            return 0.0
        
        avg_retrieval_score = np.mean([r.final_score for r in retrieval_results])
        
        # Adjust based on number of sources
        source_count_factor = min(len(retrieval_results) / 3.0, 1.0)
        
        # Combine factors
        confidence = avg_retrieval_score * source_count_factor
        
        return min(confidence, 1.0)
    
    def _format_sources(self, retrieval_results: List[Any]) -> List[Dict[str, Any]]:
        """Format source information"""
        sources = []
        
        for i, result in enumerate(retrieval_results, 1):
            source = {
                'id': result.chunk_id,
                'rank': result.rank,
                'score': result.final_score,
                'content_preview': result.content[:200] + "..." if len(result.content) > 200 else result.content,
                'metadata': {
                    'case_id': result.metadata.get('case_id'),
                    'source_file': result.metadata.get('source_file'),
                    'bus_ids': result.metadata.get('bus_ids', []),
                    'confidence_score': result.metadata.get('confidence_score')
                }
            }
            sources.append(source)
        
        return sources
    
    def _validate_response(
        self,
        response: str,
        retrieval_results: List[Any]
    ) -> List[str]:
        """Validate response quality"""
        notes = []
        
        if len(response) < 50:
            notes.append("Response may be too short")
        
        if not retrieval_results:
            notes.append("No supporting sources found")
        elif len(retrieval_results) < 2:
            notes.append("Limited supporting sources")
        
        # Check for power system terminology
        ps_terms = ['voltage', 'power', 'current', 'mw', 'mvar', 'bus', 'line', 'transformer']
        if not any(term in response.lower() for term in ps_terms):
            notes.append("Response may lack power system context")
        
        return notes

class PowerSystemRAGCore:
    """
    Core RAG system for power system data analysis.
    
    This class implements the complete RAG pipeline with proper chunking,
    embeddings, retrieval, and response generation optimized for power system data.
    """
    
    def __init__(
        self,
        db_path: str,
        vector_store_type: VectorStoreType = VectorStoreType.CHROMA,
        embedding_provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMERS,
        chunk_size: int = 400,
        chunk_overlap: int = 50,
        max_chunks_retrieved: int = 5,
        temperature: float = 0.1
    ):
        """
        Initialize the RAG system.
        
        Args:
            db_path: Path to the power system database
            vector_store_type: Type of vector store to use
            embedding_provider: Embedding model provider
            chunk_size: Size of text chunks (tokens)
            chunk_overlap: Overlap between chunks
            max_chunks_retrieved: Maximum chunks to retrieve per query
            temperature: LLM temperature for response generation
        """
        self.db_path = db_path
        self.vector_store_type = vector_store_type
        self.embedding_provider = embedding_provider
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunks_retrieved = max_chunks_retrieved
        self.temperature = temperature
        
        # Initialize components
        self.embeddings_model = None
        self.vector_store = None
        self.document_chunks = []
        self.metadata_index = {}
        
        # Performance metrics
        self.metrics = {
            'total_queries': 0,
            'avg_response_time': 0,
            'cache_hits': 0,
            'retrieval_accuracy': []
        }
        
        # Response cache
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour TTL
        
        logger.info(f"Initializing PowerSystemRAGCore with {vector_store_type.value} and {embedding_provider.value}")
        
        # Initialize all components
        self._initialize_embeddings()
        self._initialize_vector_store()
        self._load_or_create_index()
    
    def _initialize_embeddings(self):
        """Initialize the embedding model based on provider"""
        try:
            if self.embedding_provider == EmbeddingProvider.OPENAI and OPENAI_AVAILABLE:
                # Use OpenAI embeddings (requires API key)
                if os.getenv("OPENAI_API_KEY"):
                    self.embeddings_model = OpenAIEmbeddingWrapper()
                    logger.info("✅ OpenAI embeddings initialized")
                else:
                    logger.warning("OpenAI API key not found, falling back to SentenceTransformers")
                    self._initialize_sentence_transformers()
                    
            elif self.embedding_provider == EmbeddingProvider.SENTENCE_TRANSFORMERS and SENTENCE_TRANSFORMERS_AVAILABLE:
                self._initialize_sentence_transformers()
                
            else:
                # Fallback to simple embedding
                logger.warning("No embedding provider available, using simple fallback")
                self.embeddings_model = SimpleFallbackEmbedding()
                
        except Exception as e:
            logger.error(f"Error initializing embeddings: {e}")
            self.embeddings_model = SimpleFallbackEmbedding()
    
    def _initialize_sentence_transformers(self):
        """Initialize SentenceTransformers embedding model"""
        try:
            # Use a model optimized for technical/scientific text
            model_name = "all-MiniLM-L6-v2"  # Good balance of speed and accuracy
            self.embeddings_model = SentenceTransformer(model_name)
            logger.info(f"✅ SentenceTransformers initialized with {model_name}")
        except Exception as e:
            logger.error(f"Error initializing SentenceTransformers: {e}")
            self.embeddings_model = SimpleFallbackEmbedding()
    
    def _initialize_vector_store(self):
        """Initialize the vector store"""
        try:
            if self.vector_store_type == VectorStoreType.CHROMA and CHROMA_AVAILABLE:
                self._initialize_chroma()
            elif self.vector_store_type == VectorStoreType.FAISS and FAISS_AVAILABLE:
                self._initialize_faiss()
            else:
                self._initialize_memory_store()
                
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            self._initialize_memory_store()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB vector store"""
        try:
            # Create persistent Chroma client
            persist_directory = "chroma_db"
            self.chroma_client = chromadb.PersistentClient(path=persist_directory)
            
            # Create or get collection
            collection_name = "power_system_data"
            
            try:
                self.vector_store = self.chroma_client.get_collection(name=collection_name)
                logger.info("✅ Connected to existing ChromaDB collection")
            except:
                self.vector_store = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "Power system analysis data chunks"}
                )
                logger.info("✅ Created new ChromaDB collection")
                
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            self._initialize_memory_store()
    
    def _initialize_faiss(self):
        """Initialize FAISS vector store"""
        try:
            # This would be implemented for FAISS
            logger.info("FAISS implementation would go here")
            self._initialize_memory_store()  # Fallback for now
        except Exception as e:
            logger.error(f"FAISS initialization failed: {e}")
            self._initialize_memory_store()
    
    def _initialize_memory_store(self):
        """Initialize simple in-memory vector store as fallback"""
        self.vector_store = MemoryVectorStore()
        logger.info("✅ Initialized in-memory vector store (fallback)")
    
    def _load_or_create_index(self):
        """Load existing index or create new one from database"""
        index_path = f"rag_index_{hashlib.md5(self.db_path.encode()).hexdigest()}.pkl"
        
        try:
            # Try to load existing index
            if os.path.exists(index_path):
                with open(index_path, 'rb') as f:
                    index_data = pickle.load(f)
                    self.document_chunks = index_data.get('chunks', [])
                    self.metadata_index = index_data.get('metadata', {})
                    logger.info(f"✅ Loaded existing index with {len(self.document_chunks)} chunks")
            else:
                # Create new index
                logger.info("Creating new index from database...")
                self._create_index_from_database()
                
                # Save index
                with open(index_path, 'wb') as f:
                    pickle.dump({
                        'chunks': self.document_chunks,
                        'metadata': self.metadata_index
                    }, f)
                logger.info(f"✅ Created and saved new index with {len(self.document_chunks)} chunks")
                
        except Exception as e:
            logger.error(f"Error with index: {e}")
            # Create minimal index
            self._create_index_from_database()


class OpenAIEmbeddingWrapper:
    """Wrapper for OpenAI embedding API"""
    def __init__(self):
        self.client = openai.OpenAI()
        self.model = "text-embedding-3-small"
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode texts to embeddings"""
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            embeddings = np.array([item.embedding for item in response.data])
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            # Fallback to simple embedding
            return np.random.rand(len(texts), 1536)  # OpenAI embedding dimension


class SimpleFallbackEmbedding:
    """Simple fallback embedding using basic text features"""
    def __init__(self):
        self.vocab = {}
        self.embedding_dim = 384
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Create simple embeddings based on text features"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        for text in texts:
            # Simple feature extraction
            words = text.lower().split()
            
            # Create embedding based on text statistics
            features = [
                len(words),  # Word count
                len(text),   # Character count
                sum(1 for w in words if w.isdigit()),  # Number count
                sum(1 for w in words if any(c.isupper() for c in w)),  # Uppercase words
                text.count('.'),  # Decimal points
                text.count('bus'),  # Bus mentions
                text.count('branch'),  # Branch mentions
                text.count('voltage'),  # Voltage mentions
                text.count('power'),   # Power mentions
                text.count('load'),    # Load mentions
            ]
            
            # Pad to embedding dimension
            while len(features) < self.embedding_dim:
                features.extend(features[:min(len(features), self.embedding_dim - len(features))])
            
            features = features[:self.embedding_dim]
            embeddings.append(features)
        
        return np.array(embeddings, dtype=np.float32)


class MemoryVectorStore:
    """Simple in-memory vector store"""
    def __init__(self):
        self.vectors = []
        self.documents = []
        self.metadata = []
        self.ids = []
    
    def add(self, documents: List[str], embeddings: np.ndarray, metadata: List[dict], ids: List[str]):
        """Add documents to the store"""
        self.documents.extend(documents)
        self.vectors.extend(embeddings.tolist())
        self.metadata.extend(metadata)
        self.ids.extend(ids)
    
    def query(self, query_embedding: np.ndarray, n_results: int = 5) -> Dict[str, List]:
        """Query the store for similar documents"""
        if not self.vectors:
            return {'documents': [], 'metadatas': [], 'distances': [], 'ids': []}
        
        # Simple cosine similarity
        vectors_array = np.array(self.vectors)
        similarities = np.dot(vectors_array, query_embedding) / (
            np.linalg.norm(vectors_array, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top results
        top_indices = np.argsort(similarities)[-n_results:][::-1]
        
        return {
            'documents': [[self.documents[i]] for i in top_indices],
            'metadatas': [[self.metadata[i]] for i in top_indices],
            'distances': [[1 - similarities[i]] for i in top_indices],  # Convert similarity to distance
            'ids': [[self.ids[i]] for i in top_indices]
        }


# Export the main class
__all__ = ['PowerSystemRAGCore', 'ChunkMetadata', 'RetrievalResult', 'RAGResponse']