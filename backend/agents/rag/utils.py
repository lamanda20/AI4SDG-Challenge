"""
RAG Utilities

Helper functions and utilities for the RAG pipeline
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class RAGCache:
    """Simple caching for RAG results"""

    def __init__(self, cache_dir: Path = Path("backend/agents/rag/data/cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, condition: str, age: int, activity_level: str) -> str:
        """Generate cache key from query parameters"""
        return f"{condition}_{age}_{activity_level}".lower().replace(" ", "_")

    def get(self, condition: str, age: int, activity_level: str) -> Dict[str, Any]:
        """Get cached result if available"""
        import json

        cache_key = self.get_cache_key(condition, age, activity_level)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading cache: {e}")

        return None

    def set(self, condition: str, age: int, activity_level: str, data: Dict[str, Any]):
        """Cache result"""
        import json

        cache_key = self.get_cache_key(condition, age, activity_level)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")


class RAGLogger:
    """Enhanced logging for RAG pipeline"""

    def __init__(self, log_file: Path = Path("backend/agents/rag/data/rag.log")):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup file handler
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Add to root logger
        logging.getLogger().addHandler(handler)

    def log_retrieval(self, condition: str, documents_retrieved: int, retrieval_time_ms: float):
        """Log retrieval operation"""
        logger.info(
            f"RETRIEVAL | Condition: {condition} | Docs: {documents_retrieved} | Time: {retrieval_time_ms:.1f}ms"
        )

    def log_protocol_generation(self, condition: str, protocols_generated: int):
        """Log protocol generation"""
        logger.info(f"GENERATION | Condition: {condition} | Protocols: {protocols_generated}")


class RAGMetrics:
    """Collect metrics from RAG operations"""

    def __init__(self):
        self.metrics = {
            "total_queries": 0,
            "total_documents_retrieved": 0,
            "avg_retrieval_time_ms": 0,
            "avg_confidence_score": 0,
            "queries_by_condition": {},
        }

    def record_query(self, condition: str, docs_retrieved: int, retrieval_time: float, confidence: float):
        """Record query metrics"""
        self.metrics["total_queries"] += 1
        self.metrics["total_documents_retrieved"] += docs_retrieved

        # Update average retrieval time
        prev_avg = self.metrics["avg_retrieval_time_ms"]
        n = self.metrics["total_queries"]
        self.metrics["avg_retrieval_time_ms"] = (prev_avg * (n - 1) + retrieval_time) / n

        # Update average confidence
        prev_conf = self.metrics["avg_confidence_score"]
        self.metrics["avg_confidence_score"] = (prev_conf * (n - 1) + confidence) / n

        # Track by condition
        if condition not in self.metrics["queries_by_condition"]:
            self.metrics["queries_by_condition"][condition] = 0
        self.metrics["queries_by_condition"][condition] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.copy()

    def print_summary(self):
        """Print metrics summary"""
        print("\n=== RAG Metrics Summary ===")
        print(f"Total Queries: {self.metrics['total_queries']}")
        print(f"Total Documents Retrieved: {self.metrics['total_documents_retrieved']}")
        print(f"Average Retrieval Time: {self.metrics['avg_retrieval_time_ms']:.1f}ms")
        print(f"Average Confidence Score: {self.metrics['avg_confidence_score']:.2%}")
        print(f"\nQueries by Condition:")

        for condition, count in self.metrics["queries_by_condition"].items():
            print(f"  - {condition}: {count}")


def validate_rag_config() -> bool:
    """Validate RAG configuration"""
    from .config import rag_config

    logger.info("Validating RAG configuration...")

    errors = []

    # Check embedding provider
    if rag_config.embedding_provider == "openai":
        import os

        if not os.getenv("OPENAI_API_KEY"):
            errors.append("OPENAI_API_KEY not found in environment")

    # Check vector DB path
    if not rag_config.vector_db_path.exists():
        logger.warning(f"Vector DB path does not exist: {rag_config.vector_db_path}")

    # Check document paths
    if not rag_config.medical_docs_path.exists():
        logger.warning(f"Medical docs path does not exist: {rag_config.medical_docs_path}")

    if errors:
        logger.error(f"RAG Configuration validation failed: {errors}")
        return False

    logger.info("RAG configuration is valid")
    return True


def estimate_index_size(num_documents: int, avg_chunk_size: int = 500) -> int:
    """Estimate memory needed for vector index"""
    from .config import rag_config

    # Rough estimation: embedding_dim * 4 bytes per value + metadata overhead
    bytes_per_embedding = rag_config.embedding_dimension * 4
    overhead_per_doc = 200  # Metadata, IDs, etc.

    total_bytes = (num_documents * (bytes_per_embedding + overhead_per_doc))

    return total_bytes


def format_file_size(bytes_size: int) -> str:
    """Format bytes to human readable size"""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"


def benchmark_retrieval(pipeline, query, iterations: int = 10) -> Dict[str, float]:
    """Benchmark retrieval performance"""
    import time

    times = []

    for _ in range(iterations):
        start = time.time()
        pipeline.retrieve_protocols(query, top_k=5)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)

    return {
        "min_ms": min(times),
        "max_ms": max(times),
        "avg_ms": sum(times) / len(times),
        "iterations": iterations,
    }
