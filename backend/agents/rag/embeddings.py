"""
Embeddings Module

Abstraction layer for embedding generation supporting multiple providers.
Handles model initialization, caching, and batch processing.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional
import os

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass


class OpenAIEmbeddings(EmbeddingProvider):
    """OpenAI embedding provider"""

    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None):
        """
        Initialize OpenAI embeddings client

        Args:
            model: Model name (e.g., 'text-embedding-3-small', 'text-embedding-3-large')
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")

        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=self.api_key)
        self._dimension = None
        logger.info(f"Initialized OpenAI embeddings with model: {model}")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        response = self.client.embeddings.create(input=text, model=self.model)
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        if not texts:
            return []

        response = self.client.embeddings.create(input=texts, model=self.model)
        # Sort by index to maintain order
        embeddings = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in embeddings]

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        if self._dimension is None:
            # For text-embedding-3-small: 1536, text-embedding-3-large: 3072
            dimension_map = {
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
                "text-embedding-ada-002": 1536,
            }
            self._dimension = dimension_map.get(self.model, 1536)
        return self._dimension


class HuggingFaceEmbeddings(EmbeddingProvider):
    """HuggingFace embedding provider (local, no API calls)"""

    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize HuggingFace embeddings

        Args:
            model: HuggingFace model name
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Please install sentence-transformers: pip install sentence-transformers")

        self.model_name = model
        self.model = SentenceTransformer(model)
        self._dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Initialized HuggingFace embeddings with model: {model}")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        if not texts:
            return []

        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension


class NomicEmbeddings(EmbeddingProvider):
    """Nomic embedding provider (local, superior semantic search)"""

    def __init__(self, model: str = "nomic-embed-text-v1.5"):
        """
        Initialize Nomic embeddings

        Args:
            model: Nomic model name (e.g., 'nomic-embed-text-v1.5')
        """
        try:
            from nomicembedding import NomicEmbedding
        except ImportError:
            raise ImportError(
                "Please install nomic: pip install nomic\n"
                "Or install with: pip install 'nomic>=0.4.0'"
            )

        self.model_name = model
        self.embedding = NomicEmbedding(model=model, inference_mode="local")
        self._dimension = 768  # Nomic embed-text is 768-dimensional
        logger.info(f"Initialized Nomic embeddings with model: {model}")

    def embed_text(self, text: str) -> list:
        """Generate embedding for single text"""
        try:
            result = self.embedding.query([text])
            # Extract embedding from result
            embedding = result["embeddings"][0] if result.get("embeddings") else result[0]
            if isinstance(embedding, list):
                return embedding
            else:
                return embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            # Fallback to zeros
            return [0.0] * self._dimension

    def embed_batch(self, texts: list) -> list:
        """Generate embeddings for batch of texts"""
        if not texts:
            return []

        try:
            result = self.embedding.query(texts)
            embeddings = result.get("embeddings", result) if isinstance(result, dict) else result
            
            # Convert to list format
            return [
                emb.tolist() if hasattr(emb, "tolist") else list(emb)
                for emb in embeddings
            ]
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            # Fallback to zeros
            return [[0.0] * self._dimension for _ in texts]

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension


def create_embedding_provider(provider: str = "openai", **kwargs) -> EmbeddingProvider:
    """
    Factory function to create embedding provider

    Args:
        provider: Provider name ('openai', 'huggingface', or 'nomic')
        **kwargs: Arguments to pass to provider constructor

    Returns:
        EmbeddingProvider instance
    """
    if provider.lower() == "openai":
        return OpenAIEmbeddings(**kwargs)
    elif provider.lower() == "huggingface":
        return HuggingFaceEmbeddings(**kwargs)
    elif provider.lower() == "nomic":
        return NomicEmbeddings(**kwargs)
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
