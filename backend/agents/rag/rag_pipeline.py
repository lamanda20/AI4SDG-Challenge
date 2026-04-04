"""
RAG Pipeline Orchestration

Main entry point for the RAG Medical Engine.
Coordinates document loading, embedding, retrieval, and response generation.
"""

import logging
import json
from typing import Optional, List
from pathlib import Path

from .config import rag_config
from .schemas import RAGQuery, RAGOutput, MedicalProtocol, RAGQueryResult
from .document_loader import create_document_loader
from .embeddings import create_embedding_provider
from .vector_store import create_vector_store
from .retriever import MedicalRetriever
from .prompts import format_extraction_prompt, get_system_prompt

logger = logging.getLogger(__name__)


class MedicalRAGPipeline:
    """
    Orchestrates the complete RAG pipeline for medical exercise protocols.
    
    Workflow:
    1. Load documents (PubMed, PDFs, etc.)
    2. Generate embeddings
    3. Store in vector database
    4. Retrieve relevant documents for queries
    5. Format output as structured JSON
    """

    def __init__(
        self,
        vector_db_type: str = "faiss",
        embedding_provider: str = "openai",
        use_cache: bool = True,
    ):
        """
        Initialize RAG pipeline

        Args:
            vector_db_type: Type of vector database ('faiss', 'chroma')
            embedding_provider: Embedding provider ('openai', 'huggingface')
            use_cache: Use cached vector store if available
        """
        logger.info("Initializing MedicalRAGPipeline")

        # Initialize components
        self.embeddings_provider = create_embedding_provider(
            provider=embedding_provider,
            model=rag_config.embedding_model,
        )

        # Create vector store
        if vector_db_type.lower() == "faiss":
            self.vector_store = create_vector_store(
                store_type="faiss",
                embedding_dim=self.embeddings_provider.get_dimension(),
            )
        else:
            self.vector_store = create_vector_store(
                store_type="chroma",
                collection_name=rag_config.chroma_collection_name,
                persist_dir=rag_config.vector_db_path,
            )

        # Load cached index if available
        if use_cache:
            self._load_cached_index()
        else:
            self.index_loaded = False

        # Initialize retriever
        self.retriever = MedicalRetriever(
            vector_store=self.vector_store,
            embeddings_provider=self.embeddings_provider,
            use_query_expansion=True,
        )

        self.llm_client = None
        self._initialize_llm()

        logger.info("RAG pipeline initialized successfully")

    def _load_cached_index(self) -> bool:
        """Try to load cached vector store"""
        try:
            if rag_config.vector_db_path.exists():
                logger.info(f"Loading cached index from {rag_config.vector_db_path}")
                self.vector_store.load(rag_config.vector_db_path)
                self.index_loaded = self.vector_store.get_size() > 0

                if self.index_loaded:
                    logger.info(f"Loaded {self.vector_store.get_size()} documents from cache")
                    return True
        except Exception as e:
            logger.warning(f"Could not load cached index: {e}")

        self.index_loaded = False
        return False

    def _initialize_llm(self):
        """Initialize LLM client for protocol extraction"""
        try:
            if rag_config.llm_provider == "openai":
                from openai import OpenAI

                self.llm_client = OpenAI()
                logger.info("Initialized OpenAI LLM client")

            elif rag_config.llm_provider == "anthropic":
                from anthropic import Anthropic

                self.llm_client = Anthropic()
                logger.info("Initialized Anthropic LLM client")

            elif rag_config.llm_provider == "ollama":
                import requests
                # Test connection to Ollama
                try:
                    response = requests.get(f"{rag_config.ollama_base_url}/api/tags", timeout=5)
                    if response.status_code == 200:
                        self.llm_client = {"type": "ollama", "url": rag_config.ollama_base_url}
                        logger.info(f"Initialized Ollama LLM client at {rag_config.ollama_base_url}")
                    else:
                        logger.warning(f"Ollama server returned {response.status_code}")
                        self.llm_client = None
                except Exception as e:
                    logger.warning(f"Could not connect to Ollama: {e}. Make sure Ollama is running.")
                    self.llm_client = None

        except ImportError as e:
            logger.warning(f"Could not initialize LLM: {e}")
            self.llm_client = None

    def build_index(self, document_sources: List[dict]):
        """
        Build vector index from document sources

        Args:
            document_sources: List of dicts with 'type' and other params
                Example: [
                    {'type': 'pdf', 'pdf_dir': Path('docs/pdfs')},
                    {'type': 'pubmed', 'query': 'diabetes exercise', 'email': 'user@example.com'}
                ]
        """
        logger.info("Starting index build process...")
        all_documents = []

        for source in document_sources:
            source_type = source.pop("type")
            logger.info(f"Loading documents from source: {source_type}")

            try:
                loader = create_document_loader(source_type, **source)
                documents = loader.load()
                all_documents.extend(documents)
                logger.info(f"Loaded {len(documents)} documents from {source_type}")

            except Exception as e:
                logger.error(f"Error loading from {source_type}: {e}")
                continue

        if not all_documents:
            logger.warning("No documents loaded")
            return

        logger.info(f"Building index from {len(all_documents)} total documents...")

        # Add to vector store
        self.vector_store.add_documents(all_documents, self.embeddings_provider)

        # Save index
        logger.info(f"Saving index to {rag_config.vector_db_path}")
        rag_config.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.vector_store.save(rag_config.vector_db_path)

        self.index_loaded = True
        logger.info(f"Index built successfully with {self.vector_store.get_size()} documents")

    def retrieve_protocols(
        self,
        query: RAGQuery,
        top_k: Optional[int] = None,
        with_safety_filter: bool = True,
    ) -> RAGQueryResult:
        """
        Retrieve relevant medical protocols for a query

        Args:
            query: RAGQuery object
            top_k: Number of top results
            with_safety_filter: Apply safety filtering

        Returns:
            RAGQueryResult with retrieved documents
        """
        if not self.index_loaded:
            logger.warning("Index not loaded. Cannot retrieve documents.")
            return None

        if with_safety_filter:
            return self.retriever.retrieve_with_safety_check(query)
        else:
            return self.retriever.retrieve(query, top_k=top_k)

    def generate_rag_response(self, query: RAGQuery) -> RAGOutput:
        """
        Generate complete RAG response with protocol recommendations

        Args:
            query: RAGQuery object

        Returns:
            RAGOutput with structured recommendations
        """
        logger.info(f"Generating RAG response for condition: {query.user_condition}")

        # Retrieve documents
        retrieval_result = self.retrieve_protocols(query)

        if not retrieval_result or not retrieval_result.retrieved_documents:
            logger.warning("No documents retrieved")
            return self._create_empty_response(query)

        # Format documents for LLM
        documents_text = self._format_documents_for_llm(retrieval_result.retrieved_documents)

        # Extract protocols using LLM
        if self.llm_client:
            protocols = self._extract_protocols_with_llm(query, documents_text)
        else:
            logger.warning("LLM client not available. Using basic extraction.")
            protocols = self._extract_protocols_basic(retrieval_result.retrieved_documents)

        # Build response
        response = RAGOutput(
            query=query,
            recommended_protocols=protocols,
            safety_considerations=self._generate_safety_considerations(protocols, query),
            contraindicated_exercises=self._extract_contraindicated_exercises(retrieval_result.retrieved_documents),
            supporting_evidence={
                "pubmed_ids": [
                    doc.pubmed_id for doc in retrieval_result.retrieved_documents if doc.pubmed_id
                ],
                "sources": list(set(doc.source for doc in retrieval_result.retrieved_documents)),
            },
            confidence_score=self._calculate_confidence_score(retrieval_result),
            retrieved_document_count=len(retrieval_result.retrieved_documents),
        )

        logger.info(f"Generated RAG response with {len(protocols)} protocols")
        return response

    def _format_documents_for_llm(self, documents: List) -> str:
        """Format retrieved documents for LLM consumption"""
        formatted = []

        for i, doc in enumerate(documents, 1):
            formatted.append(
                f"""
Document {i}: {doc.title}
Source: {doc.source}
Relevance: {doc.relevance_score:.2%}

{doc.content[:1000]}...
"""
            )

        return "\n---\n".join(formatted)

    def _extract_protocols_with_llm(self, query: RAGQuery, documents: str) -> List[MedicalProtocol]:
        """Extract protocols using LLM"""
        try:
            prompt = format_extraction_prompt(
                condition=query.user_condition,
                age=query.user_age,
                comorbidities=", ".join(query.user_comorbidities or []),
                activity_level=query.activity_level,
                contraindications=query.contraindications or "None",
                documents=documents,
            )

            system_prompt = get_system_prompt(query.user_condition)

            if rag_config.llm_provider == "openai":
                response = self.llm_client.chat.completions.create(
                    model=rag_config.llm_model,
                    temperature=rag_config.llm_temperature,
                    max_tokens=rag_config.llm_max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                )
                content = response.choices[0].message.content

            elif rag_config.llm_provider == "anthropic":
                response = self.llm_client.messages.create(
                    model=rag_config.llm_model,
                    max_tokens=rag_config.llm_max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0].text

            elif rag_config.llm_provider == "ollama":
                import requests
                # Call Ollama API
                full_prompt = f"{system_prompt}\n\n{prompt}"
                response = requests.post(
                    f"{rag_config.ollama_base_url}/api/generate",
                    json={"model": rag_config.llm_model, "prompt": full_prompt, "stream": False},
                    timeout=60,
                )
                if response.status_code == 200:
                    content = response.json()["response"]
                else:
                    logger.error(f"Ollama error: {response.status_code}")
                    return []
            else:
                logger.error(f"Unknown LLM provider: {rag_config.llm_provider}")
                return []

            # Parse JSON response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)

                protocols = [MedicalProtocol(**p) for p in data.get("protocols", [])]
                logger.info(f"Extracted {len(protocols)} protocols from LLM")
                return protocols

        except Exception as e:
            logger.error(f"Error extracting protocols with LLM: {e}")

        return []

    def _extract_protocols_basic(self, documents: List) -> List[MedicalProtocol]:
        """Basic protocol extraction without LLM"""
        # Simplistic fallback: create generic protocol from top document
        if not documents:
            return []

        doc = documents[0]
        protocol = MedicalProtocol(
            protocol_name=doc.title,
            description=doc.content[:500],
            frequency="3-4 times per week",
            duration="30-45 minutes",
            intensity="moderate",
            citations=[doc.pubmed_id] if doc.pubmed_id else [],
        )

        return [protocol]

    def _generate_safety_considerations(self, protocols: List[MedicalProtocol], query: RAGQuery) -> str:
        """Generate overall safety considerations"""
        considerations = [
            f"Age: {query.user_age} years",
            f"Condition: {query.user_condition}",
        ]

        if query.user_comorbidities:
            considerations.append(f"Comorbidities: {', '.join(query.user_comorbidities)}")

        considerations.append(
            "Consult with healthcare provider before starting any exercise program. "
            "Monitor for adverse symptoms during exercise sessions."
        )

        return " | ".join(considerations)

    @staticmethod
    def _extract_contraindicated_exercises(documents: List) -> List[str]:
        """Extract contraindicated exercises from documents"""
        contraindicated = set()

        for doc in documents:
            # Look for keywords
            if "avoid" in doc.content.lower() or "contraindicated" in doc.content.lower():
                # Very basic extraction - would need more sophisticated NLP
                contraindicated.add("High-impact activities")
                contraindicated.add("Exercises requiring rapid directional changes")

        return list(contraindicated)

    @staticmethod
    def _calculate_confidence_score(retrieval_result: RAGQueryResult) -> float:
        """Calculate confidence score based on retrieval results"""
        if not retrieval_result.retrieved_documents:
            return 0.0

        # Average relevance score of top documents
        avg_relevance = sum(doc.relevance_score for doc in retrieval_result.retrieved_documents) / len(
            retrieval_result.retrieved_documents
        )

        # Factor in document count
        doc_count_factor = min(1.0, len(retrieval_result.retrieved_documents) / 5.0)

        # Combined confidence
        confidence = (avg_relevance * 0.7) + (doc_count_factor * 0.3)

        return min(1.0, max(0.0, confidence))

    @staticmethod
    def _create_empty_response(query: RAGQuery) -> RAGOutput:
        """Create empty response when no documents found"""
        return RAGOutput(
            query=query,
            recommended_protocols=[],
            safety_considerations="Unable to retrieve medical literature for your condition. Consult healthcare provider.",
            confidence_score=0.0,
            retrieved_document_count=0,
        )


# Global pipeline instance (initialized on first use)
_pipeline_instance = None


def get_rag_pipeline() -> MedicalRAGPipeline:
    """Get or create global RAG pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = MedicalRAGPipeline(
            vector_db_type=rag_config.vector_db_type,
            embedding_provider=rag_config.embedding_provider,
            use_cache=True,
        )
    return _pipeline_instance
