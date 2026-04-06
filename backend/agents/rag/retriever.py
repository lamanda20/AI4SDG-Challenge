"""
Retriever Module

Core retrieval logic for RAG pipeline.
Handles query expansion, document retrieval, and result ranking.
"""

import logging
from typing import List, Optional, Dict, Tuple
import json

from .schemas import RAGQuery, RAGQueryResult, MedicalDocument, RiskAssessment, MedicalGuideline
from .vector_store import VectorStore
from .embeddings import EmbeddingProvider
from .prompts import RETRIEVAL_QUERY_EXPANSION
from .config import rag_config

logger = logging.getLogger(__name__)


class MedicalRetriever:
    """
    Retriever for medical documents using semantic search.
    
    Supports:
    - Query expansion for better retrieval
    - Multi-query retrieval
    - Result filtering and ranking
    - Hybrid retrieval strategies
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embeddings_provider: EmbeddingProvider,
        use_query_expansion: bool = True,
    ):
        """
        Initialize medical retriever

        Args:
            vector_store: VectorStore instance
            embeddings_provider: EmbeddingProvider instance
            use_query_expansion: Enable query expansion
        """
        self.vector_store = vector_store
        self.embeddings_provider = embeddings_provider
        self.use_query_expansion = use_query_expansion
        logger.info("Initialized MedicalRetriever")

    def retrieve(
        self,
        query: RAGQuery,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None,
    ) -> RAGQueryResult:
        """
        Retrieve relevant medical documents for a query

        Args:
            query: RAGQuery object
            top_k: Number of top results to return (defaults to config)
            min_similarity: Minimum similarity threshold (defaults to config)

        Returns:
            RAGQueryResult with retrieved documents
        """
        import time

        start_time = time.time()
        top_k = top_k or rag_config.top_k_results
        min_similarity = min_similarity or rag_config.similarity_threshold

        logger.info(f"Retrieving documents for condition: {query.user_condition}")

        # Build search queries
        search_queries = self._build_search_queries(query)
        logger.info(f"Generated {len(search_queries)} search queries")

        # Retrieve documents for each query
        all_results = []
        for search_query in search_queries:
            logger.debug(f"Searching for: {search_query}")
            results = self.vector_store.search(search_query, self.embeddings_provider, k=top_k)
            all_results.extend(results)

        # Deduplicate and rank
        unique_docs = self._deduplicate_results(all_results)
        unique_docs = self._filter_by_similarity(unique_docs, min_similarity)
        unique_docs = sorted(unique_docs, key=lambda x: x[1], reverse=True)[:top_k]

        # Extract documents
        documents = [doc for doc, score in unique_docs]

        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms

        logger.info(f"Retrieved {len(documents)} documents in {elapsed_time:.1f}ms")

        return RAGQueryResult(
            query=query,
            retrieved_documents=documents,
            total_retrieved=len(documents),
            retrieval_time_ms=elapsed_time,
        )

    def _build_search_queries(self, query: RAGQuery) -> List[str]:
        """
        Build multiple search queries from user query

        Returns list of search queries for retrieval
        """
        queries = []

        # Primary query
        primary_query = f"{query.user_condition} exercise protocol"
        queries.append(primary_query)

        # Age-specific query
        if query.user_age < 40:
            age_group = "young adult"
        elif query.user_age < 65:
            age_group = "middle aged"
        else:
            age_group = "elderly senior"

        queries.append(f"{query.user_condition} {age_group} exercise")

        # Activity level query
        queries.append(f"{query.user_condition} {query.activity_level} activity")

        # Comorbidity queries
        if query.user_comorbidities:
            for comorbidity in query.user_comorbidities[:2]:  # Limit to 2
                queries.append(f"{query.user_condition} {comorbidity} exercise")

        # Safety-focused query
        if query.contraindications:
            queries.append(f"{query.user_condition} safe exercise {query.contraindications}")

        # Evidence query
        queries.append(f"evidence based {query.user_condition} intervention")

        logger.debug(f"Built {len(queries)} search queries: {queries}")

        return queries

    @staticmethod
    def _deduplicate_results(results: List[tuple]) -> List[tuple]:
        """
        Deduplicate results by document ID, keeping highest similarity

        Args:
            results: List of (MedicalDocument, similarity_score) tuples

        Returns:
            Deduplicated results
        """
        seen = {}
        for doc, score in results:
            if doc.id not in seen or score > seen[doc.id][1]:
                seen[doc.id] = (doc, score)

        return list(seen.values())

    @staticmethod
    def _filter_by_similarity(
        results: List[tuple],
        min_similarity: float,
    ) -> List[tuple]:
        """Filter results by similarity threshold"""
        return [(doc, score) for doc, score in results if score >= min_similarity]

    def retrieve_with_safety_check(
        self,
        query: RAGQuery,
        contraindication_keywords: Optional[List[str]] = None,
    ) -> RAGQueryResult:
        """
        Retrieve documents with safety filtering

        Filters out documents that mention contraindications
        """
        results = self.retrieve(query)

        if not contraindication_keywords:
            contraindication_keywords = query.contraindications.split(",") if query.contraindications else []

        # Filter documents that mention contraindications
        safe_docs = []
        for doc in results.retrieved_documents:
            doc_text_lower = doc.content.lower()
            is_safe = True

            for keyword in contraindication_keywords:
                if keyword.lower() in doc_text_lower and ("avoid" in doc_text_lower or "contraindicated" in doc_text_lower):
                    is_safe = False
                    break

            if is_safe:
                safe_docs.append(doc)

        results.retrieved_documents = safe_docs
        results.total_retrieved = len(safe_docs)

        logger.info(f"Retrieved {len(safe_docs)} safe documents after filtering")

        return results

    def retrieve_by_risk_assessment(
        self,
        risk_assessment: RiskAssessment,
        top_k: Optional[int] = None,
    ) -> Tuple[List[MedicalGuideline], str]:
        """
        Retrieve medical guidelines based on risk assessment

        This is the core interface for the RAG Medical Engine:
        Input: RiskAssessment
        Output: List[MedicalGuideline]

        Args:
            risk_assessment: RiskAssessment object with patient risk data
            top_k: Number of guidelines to retrieve

        Returns:
            Tuple of (guidelines, safety_summary)
        """
        import time

        start_time = time.time()
        top_k = top_k or rag_config.top_k_results

        logger.info(
            f"Retrieving guidelines for user {risk_assessment.user_id} "
            f"with risk_level={risk_assessment.risk_level}"
        )

        # STEP 1: Adjust retrieval parameters based on risk level
        similarity_threshold, intensity_filter, evidence_filter = self._get_risk_parameters(
            risk_assessment.risk_level
        )

        # STEP 2: Build risk-aware search queries
        search_queries = self._build_risk_aware_queries(risk_assessment)
        logger.info(f"Generated {len(search_queries)} risk-aware search queries")

        # STEP 3: Retrieve base documents
        all_results = []
        for search_query in search_queries:
            logger.debug(f"Risk-aware search: {search_query}")
            results = self.vector_store.search(search_query, self.embeddings_provider, k=top_k * 2)
            all_results.extend(results)

        # STEP 4: Deduplicate and filter by similarity
        unique_docs = self._deduplicate_results(all_results)
        unique_docs = self._filter_by_similarity(unique_docs, similarity_threshold)
        unique_docs = sorted(unique_docs, key=lambda x: x[1], reverse=True)[:top_k]

        documents = [doc for doc, score in unique_docs]

        # STEP 5: Convert documents to risk-appropriate MedicalGuideline objects
        guidelines = self._convert_documents_to_guidelines(
            documents, risk_assessment, intensity_filter, evidence_filter
        )

        # STEP 6: Generate safety summary
        safety_summary = self._generate_safety_summary(risk_assessment, guidelines)

        elapsed_time = (time.time() - start_time) * 1000

        logger.info(
            f"Retrieved {len(guidelines)} risk-appropriate guidelines for user {risk_assessment.user_id} "
            f"in {elapsed_time:.1f}ms"
        )

        return guidelines, safety_summary

    def _get_risk_parameters(self, risk_level: str) -> Tuple[float, str, str]:
        """
        Get retrieval parameters adjusted for risk level

        Returns:
            (similarity_threshold, intensity_filter, evidence_filter)
        """
        risk_params = {
            "low": {
                "similarity_threshold": 0.5,  # More lenient
                "intensity": "light_to_vigorous",
                "evidence": "any",  # Accept all evidence levels
            },
            "moderate": {
                "similarity_threshold": 0.65,
                "intensity": "light_to_moderate",
                "evidence": "cohort_or_better",  # Cohort studies and above
            },
            "high": {
                "similarity_threshold": 0.75,  # Stricter
                "intensity": "light",  # Only light intensity
                "evidence": "rct_only",  # Randomized controlled trials only
            },
            "critical": {
                "similarity_threshold": 0.85,  # Very strict
                "intensity": "light",
                "evidence": "rct_or_meta_analysis",
            },
        }

        params = risk_params.get(risk_level, risk_params["moderate"])
        logger.debug(f"Risk level '{risk_level}' -> params: {params}")

        return (
            params["similarity_threshold"],
            params["intensity"],
            params["evidence"],
        )

    def _build_risk_aware_queries(self, risk_assessment: RiskAssessment) -> List[str]:
        """Build search queries tailored to risk assessment"""
        queries = []

        # Primary condition query
        queries.append(f"{risk_assessment.risk_level} risk exercise protocol")

        # Risk factor specific queries
        for risk_factor in risk_assessment.risk_factors[:2]:
            queries.append(f"{risk_factor} exercise {risk_assessment.risk_level} risk")

        # Comorbidity queries
        for comorbidity in risk_assessment.comorbidities[:2]:
            queries.append(f"{comorbidity} exercise safety")

        # Age-specific safety query
        if risk_assessment.age:
            if risk_assessment.age > 65:
                queries.append("elderly senior exercise safety")
            elif risk_assessment.age > 40:
                queries.append("middle aged exercise program")

        # Activity level query
        if risk_assessment.activity_level:
            queries.append(f"sedentary to active progression {risk_assessment.activity_level}")

        # Contraindication query
        if risk_assessment.contraindications:
            queries.append(f"safe exercise {risk_assessment.contraindications}")

        # Evidence-based query
        queries.append("evidence based chronic disease exercise intervention")

        logger.debug(f"Built {len(queries)} risk-aware queries")
        return queries

    def _convert_documents_to_guidelines(
        self,
        documents: List[MedicalDocument],
        risk_assessment: RiskAssessment,
        intensity_filter: str,
        evidence_filter: str,
    ) -> List[MedicalGuideline]:
        """
        Convert retrieved documents to MedicalGuideline objects

        Applies risk-level-appropriate adjustments (frequency, duration, intensity)
        """
        guidelines = []

        for doc in documents:
            # Extract or derive protocol information from document
            intensity_mapping = {
                "light_to_vigorous": "moderate",
                "light_to_moderate": "light",
                "light": "light",
            }

            frequency_mapping = {
                "low": "5-7 times per week",
                "moderate": "3-5 times per week",
                "high": "2-3 times per week",
                "critical": "1-2 times per week",
            }

            duration_mapping = {
                "low": "30-60 minutes",
                "moderate": "20-40 minutes",
                "high": "10-20 minutes",
                "critical": "5-15 minutes",
            }

            # Create MedicalGuideline from document
            guideline = MedicalGuideline(
                protocol_id=doc.id,
                protocol_name=doc.metadata.get("protocol_name", doc.source.title()) + " Program",
                description=doc.content[:200] + "..."
                if len(doc.content) > 200
                else doc.content,
                frequency=frequency_mapping.get(risk_assessment.risk_level, "3-4 times per week"),
                duration=duration_mapping.get(risk_assessment.risk_level, "20-30 minutes"),
                intensity=intensity_mapping.get(intensity_filter, "light"),
                safety_precautions=[
                    "Get medical clearance before starting",
                    "Start with low intensity and progress gradually",
                    "Monitor for any adverse symptoms",
                    "Keep medical professionals informed",
                ],
                contraindications=risk_assessment.contraindications.split(",")
                if risk_assessment.contraindications
                else [],
                monitoring_parameters={
                    "heart_rate": "stay within prescribed zone",
                    "symptoms": "watch for chest pain, shortness of breath",
                    "fatigue": "rate perceived exertion",
                },
                evidence_level="observational",
                citations=doc.metadata.get("citations", []),
                adaptability="yes",
                progression_path="Progress duration by 5-10% per week if tolerated",
                risk_level_applied=risk_assessment.risk_level,
            )

            guidelines.append(guideline)

        logger.info(f"Converted {len(documents)} documents to {len(guidelines)} risk-appropriate guidelines")
        return guidelines

    def _generate_safety_summary(
        self,
        risk_assessment: RiskAssessment,
        guidelines: List[MedicalGuideline],
    ) -> str:
        """Generate overall safety summary for the patient"""
        risk_summaries = {
            "low": "Patient cleared for standard exercise protocols with normal progression.",
            "moderate": "Patient should follow moderate-intensity protocols with medical supervision.",
            "high": "Patient requires light-intensity programs with careful monitoring and frequent check-ins.",
            "critical": "Patient requires supervised exercise in clinical setting. Start very conservatively. "
            "Continuous monitoring essential.",
        }

        base_summary = risk_summaries.get(
            risk_assessment.risk_level,
            "Exercise program should be supervised by healthcare provider.",
        )

        # Add specific contraindication warning
        if risk_assessment.contraindications:
            base_summary += f" AVOID: {risk_assessment.contraindications}."

        # Add comorbidity note
        if risk_assessment.comorbidities:
            base_summary += (
                f" Note: Comorbidities present - {', '.join(risk_assessment.comorbidities)}. "
                "Close coordination with specialist care required."
            )

        return base_summary
