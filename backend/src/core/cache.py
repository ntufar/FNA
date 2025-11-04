"""
Caching infrastructure for FNA Platform.

Provides caching for expensive operations like model inference and embeddings
to improve performance and reduce costs.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, Dict
from datetime import datetime, timedelta

try:
    from cachetools import TTLCache, LRUCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

from ..core.config import get_settings

logger = logging.getLogger(__name__)

# Global cache instances
_sentiment_cache: Optional[TTLCache] = None
_embedding_cache: Optional[LRUCache] = None
_analysis_cache: Optional[TTLCache] = None


def get_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        str: Hash-based cache key
    """
    # Create a dictionary representation
    cache_data = {
        'args': str(args),
        'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
    }
    
    # Generate hash
    cache_str = json.dumps(cache_data, sort_keys=True)
    return hashlib.sha256(cache_str.encode()).hexdigest()


def init_caches():
    """
    Initialize cache instances based on configuration.
    
    Uses in-memory caches by default. Can be extended to support Redis.
    """
    global _sentiment_cache, _embedding_cache, _analysis_cache
    
    if not CACHE_AVAILABLE:
        logger.warning("cachetools not available, caching disabled")
        return
    
    settings = get_settings()
    
    # TTL cache for sentiment analysis results (24 hour TTL)
    # Cache key: text hash, value: SentimentAnalysisResult
    _sentiment_cache = TTLCache(
        maxsize=1000,  # Cache up to 1000 sentiment analyses
        ttl=86400  # 24 hours
    )
    
    # LRU cache for embeddings (384-dim vectors, ~1.5KB each)
    # Cache up to 10,000 embeddings (~15MB memory)
    _embedding_cache = LRUCache(maxsize=10000)
    
    # TTL cache for complete analysis results (1 hour TTL)
    _analysis_cache = TTLCache(
        maxsize=500,  # Cache up to 500 complete analyses
        ttl=3600  # 1 hour
    )
    
    logger.info("Caches initialized successfully")


def get_sentiment_cache() -> Optional[TTLCache]:
    """Get sentiment analysis cache instance."""
    if _sentiment_cache is None:
        init_caches()
    return _sentiment_cache


def get_embedding_cache() -> Optional[LRUCache]:
    """Get embedding cache instance."""
    if _embedding_cache is None:
        init_caches()
    return _embedding_cache


def get_analysis_cache() -> Optional[TTLCache]:
    """Get analysis result cache instance."""
    if _analysis_cache is None:
        init_caches()
    return _analysis_cache


def cache_sentiment_result(cache_key: str, result: Any):
    """
    Cache sentiment analysis result.
    
    Args:
        cache_key: Cache key (typically text hash)
        result: SentimentAnalysisResult to cache
    """
    cache = get_sentiment_cache()
    if cache:
        try:
            cache[cache_key] = result
            logger.debug(f"Cached sentiment result for key: {cache_key[:16]}...")
        except Exception as e:
            logger.warning(f"Failed to cache sentiment result: {e}")


def get_cached_sentiment(cache_key: str) -> Optional[Any]:
    """
    Get cached sentiment analysis result.
    
    Args:
        cache_key: Cache key (typically text hash)
        
    Returns:
        Cached result if available, None otherwise
    """
    cache = get_sentiment_cache()
    if cache:
        try:
            result = cache.get(cache_key)
            if result:
                logger.debug(f"Cache hit for sentiment key: {cache_key[:16]}...")
            return result
        except Exception as e:
            logger.warning(f"Failed to retrieve cached sentiment: {e}")
    return None


def cache_embedding(cache_key: str, embedding: Any):
    """
    Cache embedding vector.
    
    Args:
        cache_key: Cache key (typically text hash)
        embedding: Embedding vector to cache
    """
    cache = get_embedding_cache()
    if cache:
        try:
            cache[cache_key] = embedding
            logger.debug(f"Cached embedding for key: {cache_key[:16]}...")
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {e}")


def get_cached_embedding(cache_key: str) -> Optional[Any]:
    """
    Get cached embedding vector.
    
    Args:
        cache_key: Cache key (typically text hash)
        
    Returns:
        Cached embedding if available, None otherwise
    """
    cache = get_embedding_cache()
    if cache:
        try:
            embedding = cache.get(cache_key)
            if embedding:
                logger.debug(f"Cache hit for embedding key: {cache_key[:16]}...")
            return embedding
        except Exception as e:
            logger.warning(f"Failed to retrieve cached embedding: {e}")
    return None


def cache_analysis_result(cache_key: str, result: Any):
    """
    Cache complete analysis result.
    
    Args:
        cache_key: Cache key (report ID or hash)
        result: Complete analysis result to cache
    """
    cache = get_analysis_cache()
    if cache:
        try:
            cache[cache_key] = result
            logger.debug(f"Cached analysis result for key: {cache_key[:16]}...")
        except Exception as e:
            logger.warning(f"Failed to cache analysis result: {e}")


def get_cached_analysis(cache_key: str) -> Optional[Any]:
    """
    Get cached analysis result.
    
    Args:
        cache_key: Cache key (report ID or hash)
        
    Returns:
        Cached result if available, None otherwise
    """
    cache = get_analysis_cache()
    if cache:
        try:
            result = cache.get(cache_key)
            if result:
                logger.debug(f"Cache hit for analysis key: {cache_key[:16]}...")
            return result
        except Exception as e:
            logger.warning(f"Failed to retrieve cached analysis: {e}")
    return None


def cached(ttl: int = 3600, cache_type: str = "analysis"):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds (for TTL caches)
        cache_type: Type of cache to use ("sentiment", "embedding", "analysis")
    
    Example:
        @cached(ttl=3600, cache_type="sentiment")
        def analyze_sentiment(text: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = get_cache_key(*args, **kwargs)
            
            # Try to get from cache
            if cache_type == "sentiment":
                cached_result = get_cached_sentiment(cache_key)
            elif cache_type == "embedding":
                cached_result = get_cached_embedding(cache_key)
            else:
                cached_result = get_cached_analysis(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            if cache_type == "sentiment":
                cache_sentiment_result(cache_key, result)
            elif cache_type == "embedding":
                cache_embedding(cache_key, result)
            else:
                cache_analysis_result(cache_key, result)
            
            return result
        
        return wrapper
    return decorator


def clear_all_caches():
    """Clear all cache instances."""
    global _sentiment_cache, _embedding_cache, _analysis_cache
    
    if _sentiment_cache:
        _sentiment_cache.clear()
    if _embedding_cache:
        _embedding_cache.clear()
    if _analysis_cache:
        _analysis_cache.clear()
    
    logger.info("All caches cleared")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about cache usage.
    
    Returns:
        dict: Cache statistics
    """
    stats = {
        "sentiment_cache": {
            "size": len(_sentiment_cache) if _sentiment_cache else 0,
            "maxsize": _sentiment_cache.maxsize if _sentiment_cache else 0,
            "type": "TTLCache"
        },
        "embedding_cache": {
            "size": len(_embedding_cache) if _embedding_cache else 0,
            "maxsize": _embedding_cache.maxsize if _embedding_cache else 0,
            "type": "LRUCache"
        },
        "analysis_cache": {
            "size": len(_analysis_cache) if _analysis_cache else 0,
            "maxsize": _analysis_cache.maxsize if _analysis_cache else 0,
            "type": "TTLCache"
        }
    }
    
    return stats

