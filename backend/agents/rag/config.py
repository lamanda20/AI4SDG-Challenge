"""
RAG Configuration Management

This module centralizes all RAG-related configuration including:
- LLM and embedding models
- Vector database settings
- Document retrieval parameters
- API credentials
"""

from pydantic_settings import BaseSettings
from typing import Literal
from pathlib import Path


class RAGConfig(BaseSettings):
    """Configuration for RAG Medical Engine"""

    # ======================== LLM SETTINGS ========================
    # Use 'ollama' for free local models (requires Ollama running)
    # Models: 'mistral', 'neural-chat', 'orca-mini', 'llama2'
    llm_provider: Literal["openai", "anthropic", "ollama"] = "ollama"
    llm_model: str = "mistral"  # Free local model via Ollama
    llm_temperature: float = 0.2  # Low temp for medical accuracy
    llm_max_tokens: int = 1024
    ollama_base_url: str = "http://localhost:11434"  # Ollama API endpoint

    # ======================== EMBEDDING SETTINGS ========================
    # NOMIC for better semantic search (local, free, 768D vectors)
    # Options: 'openai', 'huggingface', 'nomic'
    embedding_provider: Literal["openai", "huggingface", "nomic"] = "nomic"
    embedding_model: str = "nomic-embed-text-v1.5"  # Superior semantic search, 768D
    embedding_dimension: int = 768  # Nomic dimension (was 384 for MiniLM)
    batch_size_embeddings: int = 100

    # ======================== VECTOR DATABASE SETTINGS ========================
    # CHROMA: Modern vector DB with persistence and built-in operations
    # Options: 'faiss', 'chroma', 'pinecone'
    vector_db_type: Literal["faiss", "chroma", "pinecone"] = "chroma"
    vector_db_path: Path = Path("backend/agents/rag/data/vector_store")
    chroma_collection_name: str = "medical_protocols"
    chroma_persist_dir: Path = Path("backend/agents/rag/data/chroma_db")
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # ======================== DOCUMENT RETRIEVAL SETTINGS ========================
    chunk_size: int = 500  # Characters per chunk
    chunk_overlap: int = 100  # Overlap for continuity
    top_k_results: int = 5  # Retrieved documents for RAG
    similarity_threshold: float = 0.6  # Min similarity for results
    max_retrieved_tokens: int = 4000  # Max context window from retrieval

    # ======================== PUBMED SETTINGS ========================
    pubmed_api_key: str = ""  # Optional, for higher rate limits
    pubmed_max_results: int = 100
    pubmed_batch_size: int = 10

    # ======================== DOCUMENT PATHS ========================
    medical_docs_path: Path = Path("backend/agents/rag/data/documents")
    index_cache_path: Path = Path("backend/agents/rag/data/cache")

    # ======================== LOGGING ========================
    debug_mode: bool = False
    log_retrievals: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global config instance
rag_config = RAGConfig()
