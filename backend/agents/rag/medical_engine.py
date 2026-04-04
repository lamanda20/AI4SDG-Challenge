"""
RAG Medical Engine - Abd elghani
Pipeline de recherche documentaire (PubMed) pour extraire les protocoles d'exercices sécurisés.

This module provides:
1. Document retrieval from PubMed API
2. PDF document extraction
3. Vector database storage for efficient searching
4. Safety protocol extraction and filtering
5. Structured medical document output

Usage:
    - Initialize vector DB with PDFs and PubMed papers
    - Query for exercise protocols by condition
    - Extract safe exercise recommendations
    - Return ranked, filtered protocols
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RAGMedicalEngine:
    """
    RAG Medical Engine - Core document retrieval system for safe exercise protocols
    
    Responsibilities:
    - PubMed document search and retrieval
    - PDF document loading and processing
    - Vector embedding generation
    - Similarity-based protocol search
    - Safety filtering and protocol extraction
    """

    def __init__(
        self,
        vector_db_type: str = "pinecone",
        embedding_provider: str = "nomic",
    ):
        """
        Initialize RAG Medical Engine
        
        Args:
            vector_db_type: 'pinecone', 'chroma', or 'faiss'
            embedding_provider: 'nomic' (recommended), 'openai', or 'huggingface'
        """
        logger.info("Initializing RAG Medical Engine (Abd elghani)")
        
        from backend.agents.rag.config import rag_config
        from backend.agents.rag.embeddings import create_embedding_provider
        from backend.agents.rag.vector_store import create_vector_store
        
        self.config = rag_config
        self.vector_db_type = vector_db_type or rag_config.vector_db_type
        self.embedding_provider_name = embedding_provider or rag_config.embedding_provider
        
        # Initialize embeddings
        logger.info(f"Loading embeddings provider: {self.embedding_provider_name}")
        self.embeddings_provider = create_embedding_provider(
            provider=self.embedding_provider_name,
            model=rag_config.embedding_model,
        )
        
        # Initialize vector store
        logger.info(f"Connecting to vector store: {self.vector_db_type}")
        if self.vector_db_type.lower() == "pinecone":
            self.vector_store = create_vector_store(
                store_type="pinecone",
                api_key=rag_config.pinecone_api_key,
                environment=rag_config.pinecone_environment,
                index_name=rag_config.pinecone_index_name,
                namespace=rag_config.pinecone_namespace,
                embedding_dim=rag_config.embedding_dimension,
            )
        elif self.vector_db_type.lower() == "chroma":
            self.vector_store = create_vector_store(
                store_type="chroma",
                collection_name=rag_config.chroma_collection_name,
                persist_dir=rag_config.chroma_persist_dir,
            )
        else:
            raise ValueError(f"Unsupported vector DB: {self.vector_db_type}")
        
        logger.info(f"✓ RAG Medical Engine initialized")
        logger.info(f"  Vector DB: {self.vector_db_type}")
        logger.info(f"  Embeddings: {self.embedding_provider_name} ({rag_config.embedding_dimension}D)")
    
    def search_protocols(
        self,
        condition: str,
        age: Optional[int] = None,
        activity_level: str = "moderate",
        contraindications: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for safe exercise protocols for a medical condition.
        
        Args:
            condition: Medical condition (e.g., 'Type 2 Diabetes', 'Hypertension')
            age: Patient age (optional, for context)
            activity_level: Current activity level (sedentary/light/moderate/vigorous)
            contraindications: Specific contraindications (e.g., 'knee pain', 'high BP')
            top_k: Number of top results to return
            
        Returns:
            List of ranked protocols with safety information
        """
        logger.info(f"Searching protocols for: {condition}")
        
        # Build search query
        query_parts = [condition]
        if activity_level != "moderate":
            query_parts.append(f"for {activity_level} activity level")
        if contraindications:
            query_parts.append(f"avoiding {contraindications}")
        
        search_query = " ".join(query_parts)
        logger.debug(f"Search query: {search_query}")
        
        # Search vector store
        try:
            results = self.vector_store.search(
                query=search_query,
                embeddings_provider=self.embeddings_provider,
                k=top_k,
            )
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
        
        # Format results as protocols
        protocols = []
        for doc, relevance_score in results:
            protocol = self._extract_protocol_from_document(
                doc=doc,
                relevance_score=relevance_score,
                condition=condition,
                contraindications=contraindications,
            )
            if protocol:
                protocols.append(protocol)
        
        logger.info(f"Retrieved {len(protocols)} safe protocols")
        return protocols
    
    def _extract_protocol_from_document(
        self,
        doc,
        relevance_score: float,
        condition: str,
        contraindications: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract structured protocol information from a document.
        
        Args:
            doc: Medical document
            relevance_score: Similarity score (0-1)
            condition: Medical condition
            contraindications: Patient's contraindications
            
        Returns:
            Structured protocol dict or None if not safe
        """
        try:
            # Basic safety check
            if not self._is_safe_protocol(doc, contraindications):
                logger.debug(f"Protocol '{doc.title}' flagged as unsafe")
                return None
            
            protocol = {
                "document_id": doc.id,
                "title": doc.title,
                "source": doc.source,
                "pubmed_id": doc.pubmed_id,
                "relevance_score": float(relevance_score),
                "condition": condition,
                "excerpt": doc.content[:500],
                "evidence_level": self._estimate_evidence_level(doc),
                "safety_notes": self._extract_safety_notes(doc),
                "protocol_type": self._classify_protocol(doc),
            }
            
            return protocol
            
        except Exception as e:
            logger.error(f"Error extracting protocol from document: {e}")
            return None
    
    def _is_safe_protocol(self, doc, contraindications: Optional[str] = None) -> bool:
        """
        Check if protocol is safe given contraindications.
        
        Args:
            doc: Medical document
            contraindications: Patient's contraindications
            
        Returns:
            True if protocol is safe, False if contraindicated
        """
        if not contraindications:
            return True
        
        # Check for contraindication warnings in document
        content_lower = doc.content.lower()
        contraindications_lower = contraindications.lower()
        
        # List of warning phrases indicating contraindications
        warning_phrases = [
            "contraindicated",
            "avoid",
            "do not",
            "should not",
            "stop if",
            "not recommended",
            "not suitable",
        ]
        
        # Check if contraindication is mentioned with warning phrase
        for warning in warning_phrases:
            if f"{warning}" in content_lower and contraindications_lower in content_lower:
                # Check proximity of warning and contraindication
                warning_idx = content_lower.find(warning)
                contra_idx = content_lower.find(contraindications_lower)
                
                if abs(warning_idx - contra_idx) < 100:  # Within 100 chars
                    logger.debug(f"Found contraindication warning: {warning} near {contraindications}")
                    return False
        
        return True
    
    def _extract_safety_notes(self, doc) -> List[str]:
        """Extract safety considerations from document"""
        safety_notes = []
        
        safety_keywords = [
            "contraindication",
            "caution",
            "warning",
            "monitor",
            "check",
            "inspect",
            "avoid",
            "stop if",
            "emergency",
        ]
        
        content_lower = doc.content.lower()
        for keyword in safety_keywords:
            if keyword in content_lower:
                # Try to extract the full sentence
                idx = content_lower.find(keyword)
                if idx > 0:
                    start = max(0, idx - 50)
                    end = min(len(doc.content), idx + 150)
                    sentence = doc.content[start:end].strip()
                    if sentence and sentence not in safety_notes:
                        safety_notes.append(sentence)
        
        return safety_notes[:5]  # Limit to 5 notes
    
    def _estimate_evidence_level(self, doc) -> str:
        """
        Estimate evidence level based on document source.
        
        Returns: 'high', 'medium', 'low'
        """
        source_lower = (doc.source or "").lower()
        
        # High evidence: RCT, systematic review
        if any(phrase in source_lower for phrase in ["randomized", "rct", "systematic review", "meta-analysis"]):
            return "high"
        
        # Medium evidence: cohort, guideline
        if any(phrase in source_lower for phrase in ["cohort", "guideline", "consensus"]):
            return "medium"
        
        # Low evidence: observational, case study
        return "low"
    
    def _classify_protocol(self, doc) -> str:
        """Classify the type of exercise protocol"""
        content_lower = doc.content.lower()
        
        if "aerobic" in content_lower or "cardio" in content_lower:
            return "aerobic"
        elif "resistance" in content_lower or "strength" in content_lower or "weight" in content_lower:
            return "resistance"
        elif "flexibility" in content_lower or "stretch" in content_lower:
            return "flexibility"
        elif "balance" in content_lower:
            return "balance"
        else:
            return "mixed"
    
    def get_condition_protocols(self, condition: str) -> List[str]:
        """
        Get all available protocols for a specific condition.
        
        Args:
            condition: Medical condition
            
        Returns:
            List of protocol titles
        """
        logger.info(f"Retrieving all protocols for: {condition}")
        
        protocols = self.search_protocols(condition, top_k=20)
        return [p["title"] for p in protocols]
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            size = self.vector_store.get_size()
            return {
                "total_documents": size,
                "vector_db_type": self.vector_db_type,
                "embedding_model": self.config.embedding_model,
                "embedding_dimension": self.config.embedding_dimension,
                "status": "ready" if size > 0 else "empty",
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"status": "error", "error": str(e)}


def get_rag_engine() -> RAGMedicalEngine:
    """Get or create singleton RAG engine"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGMedicalEngine()
    return _rag_engine


_rag_engine: Optional[RAGMedicalEngine] = None
