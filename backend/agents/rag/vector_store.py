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


class PineconeVectorStore(VectorStore):
    """Pinecone vector store implementation - Managed cloud vector DB"""

    def __init__(
        self,
        api_key: str,
        environment: str = "us-west1-gcp",
        index_name: str = "medical-protocols",
        namespace: str = "ai4sdg",
        embedding_dim: int = 768,
    ):
        """
        Initialize Pinecone vector store.
        
        Args:
            api_key: Pinecone API key (get from https://app.pinecone.io)
            environment: Pinecone environment (e.g., 'us-west1-gcp')
            index_name: Name of the Pinecone index
            namespace: Namespace for data isolation
            embedding_dim: Dimension of embeddings (should match model)
        """
        try:
            from pinecone import Pinecone
        except ImportError:
            raise ImportError("Please install pinecone-client: pip install pinecone-client")

        if not api_key:
            raise ValueError(
                "Pinecone API key required. Set via PINECONE_API_KEY environment variable "
                "or pass api_key parameter. Get key from https://app.pinecone.io"
            )

        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.namespace = namespace
        self.embedding_dim = embedding_dim

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=api_key)

        # Get or create index
        self._init_index()
        
        logger.info(
            f"Initialized Pinecone vector store: {index_name} "
            f"(env: {environment}, namespace: {namespace}, dim: {embedding_dim})"
        )

    def _init_index(self):
        """Initialize or connect to Pinecone index"""
        try:
            # List existing indexes
            existing_indexes = self.pc.list_indexes()
            
            # Check if index exists
            index_exists = any(idx.name == self.index_name for idx in existing_indexes)
            
            if not index_exists:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dim,
                    metric="cosine",
                    spec={"serverless": {"cloud": "gcp", "region": self.environment.split("-")[-1]}},
                )
                logger.info("Index created. Waiting for readiness...")
                import time
                time.sleep(2)  # Wait for index to be ready
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone index: {e}")
            raise

    def add_documents(self, documents: List[MedicalDocument], embeddings_provider: EmbeddingProvider) -> None:
        """Add documents and embeddings to Pinecone"""
        if not documents:
            logger.warning("No documents to add")
            return

        logger.info(f"Generating embeddings for {len(documents)} documents...")
        
        # Extract texts and generate embeddings
        texts = [doc.content for doc in documents]
        embeddings = embeddings_provider.embed_batch(texts)

        # Prepare vectors with metadata for Pinecone
        vectors_to_upsert = []
        for doc, embedding in zip(documents, embeddings):
            # Prepare metadata
            metadata = {
                "title": doc.title,
                "source": doc.source,
                "content": doc.content[:1000],  # Truncate for metadata size limits
            }
            if doc.pubmed_id:
                metadata["pubmed_id"] = doc.pubmed_id
            if doc.authors:
                metadata["authors"] = ", ".join(doc.authors)
            if doc.published_date:
                metadata["published_date"] = doc.published_date

            vectors_to_upsert.append((doc.id, embedding, metadata))

        # Upsert to Pinecone in batches
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i : i + batch_size]
            try:
                self.index.upsert(vectors=batch, namespace=self.namespace)
                logger.debug(f"Upserted batch {i//batch_size + 1} ({len(batch)} documents)")
            except Exception as e:
                logger.error(f"Error upserting batch: {e}")
                raise

        logger.info(f"Successfully added {len(documents)} documents to Pinecone")

    def search(
        self,
        query: str,
        embeddings_provider: EmbeddingProvider,
        k: int = 5,
    ) -> List[Tuple[MedicalDocument, float]]:
        """Search Pinecone for similar documents"""
        # Generate query embedding
        query_embedding = embeddings_provider.embed_text(query)

        # Query Pinecone
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=k,
                include_metadata=True,
                namespace=self.namespace,
            )
        except Exception as e:
            logger.error(f"Error querying Pinecone: {e}")
            return []

        # Format results
        output = []
        for match in results.get("matches", []):
            metadata = match.get("metadata", {})
            doc = MedicalDocument(
                id=match["id"],
                title=metadata.get("title", ""),
                content=metadata.get("content", ""),
                source=metadata.get("source", ""),
                pubmed_id=metadata.get("pubmed_id"),
                authors=metadata.get("authors", "").split(", ") if metadata.get("authors") else None,
                published_date=metadata.get("published_date"),
                relevance_score=float(match.get("score", 0.0)),
            )
            output.append((doc, doc.relevance_score))

        logger.info(f"Retrieved {len(output)} documents from Pinecone")
        return output

    def delete(self, doc_id: str) -> None:
        """Delete document from Pinecone"""
        try:
            self.index.delete(ids=[doc_id], namespace=self.namespace)
            logger.info(f"Deleted document {doc_id} from Pinecone")
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")

    def clear(self) -> None:
        """Clear all documents from namespace"""
        try:
            self.index.delete(delete_all=True, namespace=self.namespace)
            logger.info(f"Cleared all documents from namespace: {self.namespace}")
        except Exception as e:
            logger.error(f"Error clearing namespace: {e}")

    def save(self, path: Path) -> None:
        """Save operation (Pinecone maintains persistence automatically)"""
        logger.info("Pinecone maintains persistence automatically - no local save needed")

    def load(self, path: Path) -> None:
        """Load operation (Pinecone loads from cloud automatically)"""
        logger.info("Connected to Pinecone cloud index")

    def get_size(self) -> int:
        """Get number of documents in Pinecone index"""
        try:
            stats = self.index.describe_index_stats(namespace=self.namespace)
            total_vectors = stats.total_vector_count
            logger.debug(f"Pinecone index contains {total_vectors} vectors in namespace '{self.namespace}'")
            return total_vectors
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return 0


def create_vector_store(store_type: str, **kwargs) -> "VectorStore":
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
    elif store_type.lower() == "pinecone":
        api_key = kwargs.get("api_key")
        environment = kwargs.get("environment", "us-west1-gcp")
        index_name = kwargs.get("index_name", "medical-protocols")
        namespace = kwargs.get("namespace", "ai4sdg")
        embedding_dim = kwargs.get("embedding_dim", 768)
        return PineconeVectorStore(
            api_key=api_key,
            environment=environment,
            index_name=index_name,
            namespace=namespace,
            embedding_dim=embedding_dim,
        )
    else:
        raise ValueError(f"Unknown vector store type: {store_type}")
