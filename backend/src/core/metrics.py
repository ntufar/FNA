"""
Performance monitoring and metrics collection for FNA Platform.

Provides Prometheus-compatible metrics for monitoring application performance,
API usage, and system health.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Dict
from datetime import datetime

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy metrics classes
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args): pass
        def time(self): return lambda: None
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args): pass
        def inc(self, *args): pass
        def dec(self, *args): pass
    def generate_latest(): return b""

from ..core.config import get_settings

logger = logging.getLogger(__name__)

# API Metrics
api_requests_total = Counter(
    'fna_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'fna_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# Model Inference Metrics
sentiment_analysis_total = Counter(
    'fna_sentiment_analysis_total',
    'Total number of sentiment analyses performed',
    ['status']
)

sentiment_analysis_duration = Histogram(
    'fna_sentiment_analysis_duration_seconds',
    'Sentiment analysis duration in seconds'
)

# Embedding Metrics
embedding_generation_total = Counter(
    'fna_embedding_generation_total',
    'Total number of embeddings generated',
    ['status']
)

embedding_generation_duration = Histogram(
    'fna_embedding_generation_duration_seconds',
    'Embedding generation duration in seconds'
)

# Database Metrics
database_queries_total = Counter(
    'fna_database_queries_total',
    'Total number of database queries',
    ['operation']
)

database_query_duration = Histogram(
    'fna_database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation']
)

# Cache Metrics
cache_hits_total = Counter(
    'fna_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'fna_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

# System Health Metrics
active_connections = Gauge(
    'fna_active_connections',
    'Number of active database connections'
)

active_analyses = Gauge(
    'fna_active_analyses',
    'Number of active sentiment analyses'
)

# Error Metrics
api_errors_total = Counter(
    'fna_api_errors_total',
    'Total number of API errors',
    ['error_type', 'endpoint']
)


def record_api_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """
    Record API request metrics.
    
    Args:
        method: HTTP method
        endpoint: API endpoint path
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    try:
        # Normalize endpoint (remove IDs, etc.)
        normalized_endpoint = endpoint.split('/')[0] if '/' in endpoint else endpoint
        
        api_requests_total.labels(
            method=method,
            endpoint=normalized_endpoint,
            status=status_code
        ).inc()
        
        api_request_duration.labels(
            method=method,
            endpoint=normalized_endpoint
        ).observe(duration)
        
        if status_code >= 400:
            api_errors_total.labels(
                error_type='http_error',
                endpoint=normalized_endpoint
            ).inc()
    except Exception as e:
        logger.warning(f"Failed to record API metrics: {e}")


def record_sentiment_analysis(status: str, duration: float):
    """
    Record sentiment analysis metrics.
    
    Args:
        status: Analysis status ("success", "error")
        duration: Analysis duration in seconds
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    try:
        sentiment_analysis_total.labels(status=status).inc()
        sentiment_analysis_duration.observe(duration)
    except Exception as e:
        logger.warning(f"Failed to record sentiment metrics: {e}")


def record_embedding_generation(status: str, duration: float):
    """
    Record embedding generation metrics.
    
    Args:
        status: Generation status ("success", "error")
        duration: Generation duration in seconds
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    try:
        embedding_generation_total.labels(status=status).inc()
        embedding_generation_duration.observe(duration)
    except Exception as e:
        logger.warning(f"Failed to record embedding metrics: {e}")


def record_cache_operation(cache_type: str, hit: bool):
    """
    Record cache operation metrics.
    
    Args:
        cache_type: Type of cache ("sentiment", "embedding", "analysis")
        hit: Whether it was a cache hit
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    try:
        if hit:
            cache_hits_total.labels(cache_type=cache_type).inc()
        else:
            cache_misses_total.labels(cache_type=cache_type).inc()
    except Exception as e:
        logger.warning(f"Failed to record cache metrics: {e}")


def record_database_query(operation: str, duration: float):
    """
    Record database query metrics.
    
    Args:
        operation: Database operation type ("select", "insert", "update", "delete")
        duration: Query duration in seconds
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    try:
        database_queries_total.labels(operation=operation).inc()
        database_query_duration.labels(operation=operation).observe(duration)
    except Exception as e:
        logger.warning(f"Failed to record database metrics: {e}")


def track_performance(metric_type: str = "api"):
    """
    Decorator to track function performance.
    
    Args:
        metric_type: Type of metric ("api", "sentiment", "embedding", "database")
    
    Example:
        @track_performance(metric_type="sentiment")
        def analyze_sentiment(text: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                if metric_type == "sentiment":
                    record_sentiment_analysis(status, duration)
                elif metric_type == "embedding":
                    record_embedding_generation(status, duration)
                elif metric_type == "database":
                    record_database_query("query", duration)
        
        return wrapper
    return decorator


def get_metrics() -> bytes:
    """
    Get Prometheus metrics in text format.
    
    Returns:
        bytes: Prometheus metrics text
    """
    if not PROMETHEUS_AVAILABLE:
        return b"# Prometheus metrics not available (prometheus-client not installed)\n"
    
    try:
        return generate_latest()
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return b""


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get human-readable metrics summary.
    
    Returns:
        dict: Metrics summary
    """
    # This would require exposing metrics values, which Prometheus doesn't do directly
    # In production, you'd query Prometheus API or use a metrics exporter
    return {
        "prometheus_available": PROMETHEUS_AVAILABLE,
        "note": "Detailed metrics available at /metrics endpoint",
        "timestamp": datetime.utcnow().isoformat()
    }

