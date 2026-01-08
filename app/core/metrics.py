from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

# Create custom registry
registry = CollectorRegistry()

# Define metrics
rag_requests_total = Counter(
    'rag_requests_total',
    'Total number of RAG requests',
    ['status'],  # success or failure
    registry=registry
)

rag_latency_seconds = Histogram(
    'rag_latency_seconds',
    'RAG request latency in seconds',
    ['operation'],  # query, ingest, etc.
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    registry=registry
)

retrieval_no_results_total = Counter(
    'retrieval_no_results_total',
    'Total number of retrievals with no results',
    registry=registry
)

llm_errors_total = Counter(
    'llm_errors_total',
    'Total number of LLM API errors',
    ['error_type'],
    registry=registry
)

ingested_documents_total = Counter(
    'ingested_documents_total',
    'Total number of ingested documents',
    ['status'],  # success or failure
    registry=registry
)

ingested_chunks_total = Counter(
    'ingested_chunks_total',
    'Total number of ingested chunks',
    registry=registry
)

feedback_total = Counter(
    'feedback_total',
    'Total number of user feedback submissions',
    ['rating'],  # positive (1) or negative (-1)
    registry=registry
)

active_documents_gauge = Gauge(
    'active_documents_total',
    'Total number of active documents in database',
    registry=registry
)

active_chunks_gauge = Gauge(
    'active_chunks_total',
    'Total number of active chunks in database',
    registry=registry
)


def track_time(operation: str):
    """Decorator to track operation latency."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                rag_latency_seconds.labels(operation=operation).observe(time.time() - start_time)
                return result
            except Exception as e:
                rag_latency_seconds.labels(operation=operation).observe(time.time() - start_time)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                rag_latency_seconds.labels(operation=operation).observe(time.time() - start_time)
                return result
            except Exception as e:
                rag_latency_seconds.labels(operation=operation).observe(time.time() - start_time)
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


def get_metrics() -> bytes:
    """Get metrics in Prometheus text format."""
    return generate_latest(registry)
