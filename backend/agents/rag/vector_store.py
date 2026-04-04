"""
Vector Store Module

Abstraction layer for vector database backends (FAISS, Chroma, Pinecone).
Handles document storage, retrieval, and similarity search.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

from .schemas import MedicalDocument
from .embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract base class for vector stores"""

    @abstractmethod
    def add_documents(self, documents: List[MedicalDocument], embeddings_provider: EmbeddingProvider) -> None:
        """Add documents to vector store"""
        pass

    @abstractmethod
    def search(self, query: str, embeddings_provider: EmbeddingProvider, k: int = 5) -> List[Tuple[MedicalDocument, float]]:
        """Search for similar documents"""
        pass

    @abstractmethod
    def delete(self, doc_id: str) -> None:
        """Delete document from store"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all documents"""
        pass

    @abstractmethod
    def save(self, path: Path) -> None:
        """Persist vector store to disk"""
        pass

    @abstractmethod
    def load(self, path: Path) -> None:
        """Load vector store from disk"""
        pass

    @abstractmethod
    def get_size(self) -> int:
        """Get number of documents in store"""
        pass


class FAISSVectorStore(VectorStore):
    """FAISS (Facebook AI Similarity Search) vector store implementation"""

    def __init__(self, embedding_dim: int):
        """
        Initialize FAISS vector store

        Args:
            embedding_dim: Dimension of embeddings
        """
        try:
            import faiss
        except ImportError:
            raise ImportError("Please install faiss-cpu: pip install faiss-cpu")

        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.documents: Dict[int, MedicalDocument] = {}
        self.doc_counter = 0
        logger.info(f"Initialized FAISS vector store with dimension {embedding_dim}")

    def add_documents(self, documents: List[MedicalDocument], embeddings_provider: EmbeddingProvider) -> None:
        """Add documents and their embeddings to FAISS index"""
        if not documents:
            logger.warning("No documents to add")
            return

        # Extract texts
        texts = [doc.content for doc in documents]

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} documents...")
        embeddings = embeddings_provider.embed_batch(texts)

        # Add to FAISS
        import numpy as np
        embeddings_array = np.array(embeddings, dtype=np.float32)
        self.index.add(embeddings_array)

        # Store document metadata
        for i, doc in enumerate(documents):
            self.documents[self.doc_counter + i] = doc

        self.doc_counter += len(documents)
        logger.info(f"Added {len(documents)} documents to FAISS index")

    def search(self, query: str, embeddings_provider: EmbeddingProvider, k: int = 5) -> List[Tuple[MedicalDocument, float]]:
        """Search FAISS index for similar documents"""
        if self.index.ntotal == 0:
            logger.warning("Vector store is empty")
            return []

        # Generate query embedding
        query_embedding = embeddings_provider.embed_text(query)

        # Search
        import numpy as np
        query_array = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query_array, min(k, self.index.ntotal))

        # Convert L2 distances to similarity scores
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx in self.documents:
                # Convert L2 distance to similarity (lower distance = higher similarity)
                # Normalize: similarity = 1 / (1 + distance)
                similarity = 1.0 / (1.0 + distance)
                doc = self.documents[idx]
                doc.relevance_score = float(similarity)
                results.append((doc, float(similarity)))

        logger.info(f"Retrieved {len(results)} documents for query")
        return sorted(results, key=lambda x: x[1], reverse=True)

    def delete(self, doc_id: str) -> None:
        """Note: FAISS doesn't support deletion. Mark document as inactive instead."""
        for idx, doc in self.documents.items():
            if doc.id == doc_id:
                logger.warning("FAISS doesn't support deletion. Consider rebuilding index.")
                # Could mark as deleted in metadata
                return

    def clear(self) -> None:
        """Clear all documents"""
        import faiss
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.documents.clear()
        self.doc_counter = 0
        logger.info("Cleared FAISS vector store")

    def save(self, path: Path) -> None:
        """Save index to disk"""
        import faiss
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / "faiss_index.bin"))
        
        # Also save documents metadata as JSON
        import json
        docs_metadata = {
            str(idx): {
                "id": doc.id,
                "title": doc.title,
                "source": doc.source,
                "pubmed_id": doc.pubmed_id,
            }
            for idx, doc in self.documents.items()
        }
        with open(path / "documents.json", "w") as f:
            json.dump(docs_metadata, f)
        
        logger.info(f"Saved FAISS index to {path}")

    def load(self, path: Path) -> None:
        """Load index from disk"""
        import faiss
        import json

        if not (path / "faiss_index.bin").exists():
            logger.warning(f"No saved index found at {path}")
            return

        self.index = faiss.read_index(str(path / "faiss_index.bin"))
        
        # Reload documents metadata
        with open(path / "documents.json", "r") as f:
            docs_metadata = json.load(f)
            self.documents = {int(k): MedicalDocument(**v) for k, v in docs_metadata.items()}
        
        logger.info(f"Loaded FAISS index from {path}")

    def get_size(self) -> int:
        """Get number of documents"""
        return self.index.ntotal


class ChromaVectorStore(VectorStore):
    """Chroma vector store implementation"""

    def __init__(self, collection_name: str = "medical_protocols", persist_dir: Optional[Path] = None):
        """
        Initialize Chroma vector store

        Args:
            collection_name: Name of the collection
            persist_dir: Directory for persistence
        """
        try:
            import chromadb
        except ImportError:
            raise ImportError("Please install chroma-db: pip install chromadb")

        self.collection_name = collection_name
        self.persist_dir = persist_dir

        # Initialize Chroma client
        if persist_dir:
            persist_dir.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(persist_dir))
        else:
            self.client = chromadb.EphemeralClient()

        self.collection = None
        logger.info(f"Initialized Chroma vector store: {collection_name}")

    def add_documents(self, documents: List[MedicalDocument], embeddings_provider: EmbeddingProvider) -> None:
        """Add documents to Chroma collection"""
        if not documents:
            logger.warning("No documents to add")
            return

        # Get or create collection
        if self.collection is None:
            self.collection = self.client.get_or_create_collection(name=self.collection_name)

        # Extract data
        ids = [doc.id for doc in documents]
        documents_content = [doc.content for doc in documents]
        metadatas = [
            {
                "title": doc.title,
                "source": doc.source,
                "pubmed_id": doc.pubmed_id or "",
            }
            for doc in documents
        ]

        # Generate embeddings
        embeddings = embeddings_provider.embed_batch(documents_content)

        # Add to Chroma
        self.collection.add(ids=ids, embeddings=embeddings, documents=documents_content, metadatas=metadatas)
        logger.info(f"Added {len(documents)} documents to Chroma collection")

    def search(self, query: str, embeddings_provider: EmbeddingProvider, k: int = 5) -> List[Tuple[MedicalDocument, float]]:
        """Search Chroma collection"""
        if self.collection is None or self.collection.count() == 0:
            logger.warning("Collection is empty")
            return []

        # Generate query embedding
        query_embedding = embeddings_provider.embed_text(query)

        # Search
        results = self.collection.query(query_embeddings=[query_embedding], n_results=k)

        # Format results
        output = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                doc = MedicalDocument(
                    id=doc_id,
                    title=results["metadatas"][0][i].get("title", ""),
                    content=results["documents"][0][i],
                    source=results["metadatas"][0][i].get("source", ""),
                    pubmed_id=results["metadatas"][0][i].get("pubmed_id"),
                    relevance_score=1.0 - (results["distances"][0][i] / 2),  # Convert distance to similarity
                )
                output.append((doc, doc.relevance_score))

        return output

    def delete(self, doc_id: str) -> None:
        """Delete document from collection"""
        if self.collection:
            self.collection.delete(ids=[doc_id])

    def clear(self) -> None:
        """Clear collection"""
        if self.collection:
            self.client.delete_collection(name=self.collection_name)
            self.collection = None

    def save(self, path: Path) -> None:
        """Save collection (Chroma handles persistence automatically)"""
        logger.info("Chroma persists automatically")

    def load(self, path: Path) -> None:
        """Load collection"""
        if self.collection is None:
            self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def get_size(self) -> int:
        """Get number of documents"""
        return self.collection.count() if self.collection else 0


def create_vector_store(store_type: str = "faiss", **kwargs) -> VectorStore:
    """
    Factory function to create vector store

    Args:
        store_type: Type of store ('faiss', 'chroma', 'pinecone')
        **kwargs: Arguments for store constructor

    Returns:
        VectorStore instance
    """
    if store_type.lower() == "faiss":
        embedding_dim = kwargs.get("embedding_dim", 1536)
        return FAISSVectorStore(embedding_dim)
    elif store_type.lower() == "chroma":
        collection_name = kwargs.get("collection_name", "medical_protocols")
        persist_dir = kwargs.get("persist_dir")
        return ChromaVectorStore(collection_name, persist_dir)
    else:
        raise ValueError(f"Unknown vector store type: {store_type}")
