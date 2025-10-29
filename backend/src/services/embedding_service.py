"""Sentence Transformers Embedding Service for FNA Backend.

This module handles text embeddings using sentence-transformers/all-MiniLM-L6-v2
as specified in research.md for vector similarity search.
"""

import numpy as np
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
from pydantic import BaseSettings

# Sentence Transformers imports
try:
    from sentence_transformers import SentenceTransformer
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingSettings(BaseSettings):
    """Embedding service configuration from environment variables."""
    
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
    device: str = "auto"
    cache_dir: str = "./model_cache/embeddings"
    
    class Config:
        env_prefix = "EMBEDDING_"


class EmbeddingServiceError(Exception):
    """Exception raised when embedding operations fail."""
    pass


class EmbeddingService:
    """Manages text embeddings using sentence-transformers."""
    
    def __init__(self, settings: Optional[EmbeddingSettings] = None):
        self.settings = settings or EmbeddingSettings()
        self.model: Optional[SentenceTransformer] = None
        self._is_loaded = False
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not available. Install with: pip install sentence-transformers"
            )
    
    def _ensure_cache_dir(self) -> Path:
        """Ensure embedding model cache directory exists."""
        cache_path = Path(self.settings.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path
    
    def load_model(self) -> bool:
        """Load the sentence-transformers model.
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            if self._is_loaded:
                return True
            
            print(f"Loading embedding model: {self.settings.model}")
            print(f"Cache directory: {self.settings.cache_dir}")
            
            cache_dir = self._ensure_cache_dir()
            
            # Determine device
            device = self.settings.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Load the sentence transformer model
            self.model = SentenceTransformer(
                self.settings.model,
                cache_folder=str(cache_dir),
                device=device
            )
            
            self._is_loaded = True
            print(f"✅ Embedding model loaded successfully on {device}")
            print(f"Embedding dimension: {self.settings.dimension}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            return False
    
    def encode_texts(
        self, 
        texts: Union[str, List[str]], 
        normalize_embeddings: bool = True,
        show_progress_bar: bool = False
    ) -> np.ndarray:
        """Generate embeddings for input texts.
        
        Args:
            texts: Single text or list of texts to embed
            normalize_embeddings: Whether to normalize embeddings to unit length
            show_progress_bar: Whether to show progress for batch processing
            
        Returns:
            np.ndarray: Array of embeddings, shape (n_texts, embedding_dim)
            
        Raises:
            EmbeddingServiceError: If encoding fails
        """
        if not self._is_loaded:
            raise EmbeddingServiceError("Model not loaded. Call load_model() first.")
        
        try:
            # Convert single text to list
            if isinstance(texts, str):
                texts = [texts]
            
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=self.settings.batch_size,
                normalize_embeddings=normalize_embeddings,
                show_progress_bar=show_progress_bar,
                convert_to_numpy=True
            )
            
            return embeddings
            
        except Exception as e:
            raise EmbeddingServiceError(f"Error generating embeddings: {e}")
    
    def compute_similarity(
        self, 
        embeddings1: np.ndarray, 
        embeddings2: np.ndarray
    ) -> np.ndarray:
        """Compute cosine similarity between embeddings.
        
        Args:
            embeddings1: First set of embeddings
            embeddings2: Second set of embeddings
            
        Returns:
            np.ndarray: Similarity scores matrix
        """
        try:
            # Ensure embeddings are 2D
            if embeddings1.ndim == 1:
                embeddings1 = embeddings1.reshape(1, -1)
            if embeddings2.ndim == 1:
                embeddings2 = embeddings2.reshape(1, -1)
            
            # Compute cosine similarity
            similarity = np.dot(embeddings1, embeddings2.T)
            
            return similarity
            
        except Exception as e:
            raise EmbeddingServiceError(f"Error computing similarity: {e}")
    
    def find_most_similar(
        self, 
        query_text: str, 
        candidate_texts: List[str], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find most similar texts to a query.
        
        Args:
            query_text: Text to search for
            candidate_texts: List of texts to search in
            top_k: Number of top results to return
            
        Returns:
            List of dicts with 'text', 'similarity', and 'index' keys
        """
        try:
            # Generate embeddings
            query_embedding = self.encode_texts(query_text)
            candidate_embeddings = self.encode_texts(candidate_texts)
            
            # Compute similarities
            similarities = self.compute_similarity(query_embedding, candidate_embeddings)[0]
            
            # Get top-k most similar
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                results.append({
                    'text': candidate_texts[idx],
                    'similarity': float(similarities[idx]),
                    'index': int(idx)
                })
            
            return results
            
        except Exception as e:
            raise EmbeddingServiceError(f"Error finding similar texts: {e}")
    
    def is_loaded(self) -> bool:
        """Check if the embedding model is loaded."""
        return self._is_loaded
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded embedding model."""
        return {
            "model_name": self.settings.model,
            "is_loaded": self._is_loaded,
            "embedding_dimension": self.settings.dimension,
            "batch_size": self.settings.batch_size,
            "cache_dir": self.settings.cache_dir,
            "device": self.model.device if self.model else None
        }


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def initialize_embedding_service() -> bool:
    """Initialize the embedding service on application startup."""
    service = get_embedding_service()
    return service.load_model()


def embed_text(text: Union[str, List[str]]) -> np.ndarray:
    """Convenience function to embed text using the global service."""
    service = get_embedding_service()
    return service.encode_texts(text)
