"""
Embeddings System for Power System RAG
=====================================

This module implements a flexible embeddings system supporting both OpenAI API
and local models optimized for power system technical content.

Key Features:
- OpenAI text-embedding-3-small (primary)
- Local Sentence-Transformers fallback (all-MiniLM-L6-v2, all-mpnet-base-v2)
- Power system domain adaptation
- Batch processing for efficiency
- Caching and persistence

Author: Power System Analysis Team
Date: September 2025
"""

import numpy as np
import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional, Union, Tuple
import logging
import pickle
import os
from datetime import datetime, timedelta
import hashlib
from dataclasses import dataclass
import sqlite3

# Try OpenAI import
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available, falling back to local models")

# Try sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("Sentence Transformers not available")

# Try scikit-learn for fallback
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResult:
    """Result of embedding operation"""
    embedding: np.ndarray
    model_name: str
    dimension: int
    processing_time: float
    success: bool
    error_message: Optional[str] = None

class PowerSystemEmbeddingsEngine:
    """
    Advanced embeddings engine for power system RAG.
    
    Supports multiple embedding models with intelligent fallback:
    1. OpenAI text-embedding-3-small (preferred)
    2. Local Sentence-Transformers models
    3. TF-IDF fallback
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model_preference: List[str] = None,
        cache_dir: str = "embeddings_cache",
        batch_size: int = 100,
        max_retries: int = 3
    ):
        """
        Initialize the embeddings engine.
        
        Args:
            openai_api_key: OpenAI API key (if available)
            model_preference: List of preferred models in order
            cache_dir: Directory for embedding cache
            batch_size: Batch size for processing
            max_retries: Maximum retry attempts
        """
        self.openai_api_key = openai_api_key
        self.cache_dir = cache_dir
        self.batch_size = batch_size
        self.max_retries = max_retries
        
        # Default model preference
        if model_preference is None:
            model_preference = [
                "text-embedding-3-small",  # OpenAI
                "all-mpnet-base-v2",       # Sentence-Transformers (best quality)
                "all-MiniLM-L6-v2",        # Sentence-Transformers (fast)
                "tfidf"                     # Fallback
            ]
        
        self.model_preference = model_preference
        self.current_model = None
        self.local_models = {}
        
        # Setup cache
        self._setup_cache()
        
        # Initialize models
        self._initialize_models()
        
        logger.info(f"Embeddings engine initialized with models: {model_preference}")
    
    def _setup_cache(self):
        """Setup embedding cache directory and database"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Create cache database
        self.cache_db_path = os.path.join(self.cache_dir, "embeddings_cache.db")
        self._create_cache_db()
    
    def _create_cache_db(self):
        """Create cache database schema"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings_cache (
                content_hash TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                embedding BLOB NOT NULL,
                dimension INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 1,
                last_accessed TEXT
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_model_hash 
            ON embeddings_cache(model_name, content_hash)
        ''')
        
        conn.commit()
        conn.close()
    
    def _initialize_models(self):
        """Initialize available embedding models"""
        # Initialize OpenAI
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                openai.api_key = self.openai_api_key
                self.current_model = "text-embedding-3-small"
                logger.info("OpenAI embedding model initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        
        # Initialize Sentence-Transformers models
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            for model_name in ["all-mpnet-base-v2", "all-MiniLM-L6-v2"]:
                try:
                    if model_name in self.model_preference:
                        logger.info(f"Loading Sentence-Transformers model: {model_name}")
                        model = SentenceTransformer(model_name)
                        self.local_models[model_name] = model
                        
                        if self.current_model is None:
                            self.current_model = model_name
                        
                        logger.info(f"Loaded {model_name}")
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")
        
        # Fallback to TF-IDF
        if SKLEARN_AVAILABLE and self.current_model is None:
            self.current_model = "tfidf"
            self.tfidf_vectorizer = None
            logger.info("Using TF-IDF as fallback embedding method")
        
        if self.current_model is None:
            raise RuntimeError("No embedding models available!")
        
        logger.info(f"Active embedding model: {self.current_model}")
    
    async def embed_documents(self, documents: List[str]) -> List[EmbeddingResult]:
        """
        Embed multiple documents efficiently.
        
        Args:
            documents: List of document texts to embed
            
        Returns:
            List of embedding results
        """
        logger.info(f"Embedding {len(documents)} documents using {self.current_model}")
        
        results = []
        
        # Process in batches
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            batch_results = await self._embed_batch(batch)
            results.extend(batch_results)
            
            # Log progress
            if (i + self.batch_size) % 100 == 0:
                logger.info(f"Embedded {min(i + self.batch_size, len(documents))}/{len(documents)} documents")
        
        success_count = sum(1 for r in results if r.success)
        logger.info(f"Successfully embedded {success_count}/{len(documents)} documents")
        
        return results
    
    async def _embed_batch(self, documents: List[str]) -> List[EmbeddingResult]:
        """Embed a batch of documents"""
        # Check cache first
        cached_results, uncached_docs = self._check_cache(documents)
        results = cached_results.copy()
        
        if not uncached_docs:
            return results
        
        # Embed uncached documents
        start_time = datetime.now()
        
        try:
            if self.current_model == "text-embedding-3-small":
                embeddings = await self._embed_openai(uncached_docs)
            elif self.current_model in self.local_models:
                embeddings = await self._embed_sentence_transformers(uncached_docs)
            elif self.current_model == "tfidf":
                embeddings = await self._embed_tfidf(uncached_docs)
            else:
                raise ValueError(f"Unknown model: {self.current_model}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create results
            for i, (doc, embedding) in enumerate(zip(uncached_docs, embeddings)):
                result = EmbeddingResult(
                    embedding=embedding,
                    model_name=self.current_model,
                    dimension=len(embedding),
                    processing_time=processing_time / len(uncached_docs),
                    success=True
                )
                results.append(result)
                
                # Cache the result
                self._cache_embedding(doc, result)
        
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            # Return failed results
            for doc in uncached_docs:
                results.append(EmbeddingResult(
                    embedding=np.zeros(384),  # Default dimension
                    model_name=self.current_model,
                    dimension=384,
                    processing_time=0,
                    success=False,
                    error_message=str(e)
                ))
        
        return results
    
    async def _embed_openai(self, documents: List[str]) -> List[np.ndarray]:
        """Embed using OpenAI API"""
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI not available")
        
        # Preprocess documents for power system content
        processed_docs = [self._preprocess_power_system_text(doc) for doc in documents]
        
        try:
            response = await openai.Embedding.acreate(
                model="text-embedding-3-small",
                input=processed_docs
            )
            
            embeddings = []
            for item in response.data:
                embeddings.append(np.array(item.embedding, dtype=np.float32))
            
            return embeddings
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    async def _embed_sentence_transformers(self, documents: List[str]) -> List[np.ndarray]:
        """Embed using Sentence-Transformers"""
        model = self.local_models[self.current_model]
        
        # Preprocess documents
        processed_docs = [self._preprocess_power_system_text(doc) for doc in documents]
        
        # Run in thread pool to avoid blocking
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                executor, model.encode, processed_docs
            )
        
        return [emb.astype(np.float32) for emb in embeddings]
    
    async def _embed_tfidf(self, documents: List[str]) -> List[np.ndarray]:
        """Embed using TF-IDF (fallback method)"""
        if self.tfidf_vectorizer is None:
            # Initialize with power system vocabulary
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                vocabulary=self._get_power_system_vocabulary()
            )
        
        processed_docs = [self._preprocess_power_system_text(doc) for doc in documents]
        
        # Fit or transform
        if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
            # First time - fit and transform
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(processed_docs)
        else:
            # Transform only
            tfidf_matrix = self.tfidf_vectorizer.transform(processed_docs)
        
        # Convert to dense numpy arrays
        embeddings = []
        for i in range(tfidf_matrix.shape[0]):
            embedding = tfidf_matrix[i].toarray().flatten().astype(np.float32)
            embeddings.append(embedding)
        
        return embeddings
    
    def _preprocess_power_system_text(self, text: str) -> str:
        """Preprocess text for power system domain"""
        # Convert to lowercase for consistency
        text = text.lower()
        
        # Expand power system abbreviations
        replacements = {
            'mw': 'megawatt',
            'mvar': 'megavolt-ampere reactive',
            'kv': 'kilovolt', 
            'mva': 'megavolt-ampere',
            'pu': 'per unit',
            'vm': 'voltage magnitude',
            'va': 'voltage angle',
            'pf': 'power factor',
            'dlr': 'dynamic line rating',
            'slr': 'static line rating',
            'scada': 'supervisory control and data acquisition'
        }
        
        for abbrev, full_form in replacements.items():
            text = text.replace(abbrev, full_form)
        
        return text
    
    def _get_power_system_vocabulary(self) -> List[str]:
        """Get power system specific vocabulary for TF-IDF"""
        return [
            'voltage', 'current', 'power', 'bus', 'branch', 'line', 'transformer',
            'generator', 'load', 'megawatt', 'megavolt', 'kilovolt', 'reactive',
            'active', 'apparent', 'impedance', 'admittance', 'rating', 'thermal',
            'loading', 'contingency', 'outage', 'flow', 'angle', 'magnitude',
            'per unit', 'base', 'static', 'dynamic', 'transmission', 'distribution',
            'substation', 'feeder', 'conductor', 'ampacity', 'temperature'
        ]
    
    def _check_cache(self, documents: List[str]) -> Tuple[List[EmbeddingResult], List[str]]:
        """Check cache for existing embeddings"""
        cached_results = []
        uncached_docs = []
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        for doc in documents:
            doc_hash = self._hash_content(doc)
            
            cursor.execute('''
                SELECT embedding, dimension, created_at 
                FROM embeddings_cache 
                WHERE content_hash = ? AND model_name = ?
            ''', (doc_hash, self.current_model))
            
            result = cursor.fetchone()
            
            if result:
                # Load cached embedding
                embedding_blob, dimension, created_at = result
                embedding = pickle.loads(embedding_blob)
                
                cached_result = EmbeddingResult(
                    embedding=embedding,
                    model_name=self.current_model,
                    dimension=dimension,
                    processing_time=0,
                    success=True
                )
                cached_results.append(cached_result)
                
                # Update access count
                cursor.execute('''
                    UPDATE embeddings_cache 
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE content_hash = ? AND model_name = ?
                ''', (datetime.now().isoformat(), doc_hash, self.current_model))
                
            else:
                uncached_docs.append(doc)
                cached_results.append(None)  # Placeholder
        
        conn.commit()
        conn.close()
        
        # Filter out None placeholders
        actual_cached = [r for r in cached_results if r is not None]
        
        return actual_cached, uncached_docs
    
    def _cache_embedding(self, document: str, result: EmbeddingResult):
        """Cache an embedding result"""
        if not result.success:
            return
        
        doc_hash = self._hash_content(document)
        embedding_blob = pickle.dumps(result.embedding)
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO embeddings_cache
                (content_hash, model_name, embedding, dimension, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                doc_hash,
                result.model_name, 
                embedding_blob,
                result.dimension,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to cache embedding: {e}")
        
        finally:
            conn.close()
    
    def _hash_content(self, content: str) -> str:
        """Create hash of content for caching"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings for current model"""
        if self.current_model == "text-embedding-3-small":
            return 1536
        elif self.current_model == "all-mpnet-base-v2":
            return 768
        elif self.current_model == "all-MiniLM-L6-v2":
            return 384
        elif self.current_model == "tfidf":
            return 1000  # max_features
        else:
            return 384  # default
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding cache"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total cached embeddings
        cursor.execute("SELECT COUNT(*) FROM embeddings_cache")
        stats['total_cached'] = cursor.fetchone()[0]
        
        # By model
        cursor.execute('''
            SELECT model_name, COUNT(*) 
            FROM embeddings_cache 
            GROUP BY model_name
        ''')
        stats['by_model'] = dict(cursor.fetchall())
        
        # Cache hit rate (approximate)
        cursor.execute('''
            SELECT AVG(access_count) 
            FROM embeddings_cache
        ''')
        avg_access = cursor.fetchone()[0] or 0
        stats['avg_access_count'] = avg_access
        
        # Storage size
        cache_size = os.path.getsize(self.cache_db_path) if os.path.exists(self.cache_db_path) else 0
        stats['cache_size_mb'] = cache_size / (1024 * 1024)
        
        conn.close()
        
        return stats
    
    def clear_cache(self, model_name: Optional[str] = None):
        """Clear embedding cache"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        if model_name:
            cursor.execute("DELETE FROM embeddings_cache WHERE model_name = ?", (model_name,))
            logger.info(f"Cleared cache for model: {model_name}")
        else:
            cursor.execute("DELETE FROM embeddings_cache")
            logger.info("Cleared entire embedding cache")
        
        conn.commit()
        conn.close()


# Export the main class
__all__ = ['PowerSystemEmbeddingsEngine', 'EmbeddingResult']