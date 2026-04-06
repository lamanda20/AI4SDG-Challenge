"""
Medical Guidelines API Endpoints

RAG Medical Engine integration endpoints for fetching risk-aware exercise protocols.

Endpoints:
    POST /api/rag/medical-guidelines - Get personalized medical guidelines based on risk assessment
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from backend.agents.rag import (
    MedicalRAGPipeline,
    get_rag_pipeline,
    RiskAssessment,
    MedicalGuideline,
    MedicalGuidelinesResponse,
)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create router
router = APIRouter(prefix="/api/rag", tags=["Medical Guidelines"])

# Global RAG pipeline instance
_rag_pipeline: Optional[MedicalRAGPipeline] = None


def get_medical_rag_pipeline() -> MedicalRAGPipeline:
    """
    Get or initialize the RAG Medical Engine pipeline

    Returns:
        MedicalRAGPipeline instance
    """
    global _rag_pipeline

    if _rag_pipeline is None:
        logger.info("Initializing RAG Medical Engine pipeline...")
        try:
            _rag_pipeline = get_rag_pipeline()
            logger.info("RAG Medical Engine pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"RAG pipeline initialization failed: {str(e)}",
            )

    return _rag_pipeline


@router.post(
    "/medical-guidelines",
    response_model=MedicalGuidelinesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Medical Guidelines",
    description="Retrieve personalized medical guidelines based on patient risk assessment",
)
async def get_medical_guidelines(
    risk_assessment: RiskAssessment,
    use_cache: bool = True,
) -> MedicalGuidelinesResponse:
    """
    Get personalized medical guidelines based on risk assessment

    This endpoint receives a risk assessment from the ML Agent and returns
    risk-appropriate exercise protocols from the RAG Medical Engine.

    Args:
        risk_assessment: Patient risk assessment with risk_level, risk_score, comorbidities
        use_cache: Whether to use cached guidelines if available

    Returns:
        MedicalGuidelinesResponse with recommended protocols

    Raises:
        HTTPException: If RAG pipeline fails or validation errors occur
    """

    logger.info(
        f"Processing medical guidelines request for user {risk_assessment.user_id} "
        f"with risk_level={risk_assessment.risk_level}"
    )

    try:
        # Validate risk assessment
        if risk_assessment.risk_level not in ["low", "moderate", "high", "critical"]:
            raise ValueError(f"Invalid risk_level: {risk_assessment.risk_level}")

        if not 0.0 <= risk_assessment.risk_score <= 1.0:
            raise ValueError(f"risk_score must be between 0.0 and 1.0, got {risk_assessment.risk_score}")

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )

    try:
        # Get RAG pipeline
        rag_pipeline = get_medical_rag_pipeline()

        # Retrieve guidelines using RAG
        logger.debug(f"Querying RAG pipeline for user {risk_assessment.user_id}")

        guidelines, safety_summary = rag_pipeline.retriever.retrieve_by_risk_assessment(
            risk_assessment=risk_assessment,
        )

        logger.info(f"Retrieved {len(guidelines)} guidelines for user {risk_assessment.user_id}")

        # Build response
        response = MedicalGuidelinesResponse(
            status="success",
            user_id=risk_assessment.user_id,
            risk_level_applied=risk_assessment.risk_level,
            medical_guidelines=guidelines,
            safety_summary=safety_summary,
            confidence_score=min(1.0, len(guidelines) * 0.2) if guidelines else 0.5,  # Simple confidence metric
            retrieved_document_count=len(guidelines),
        )

        logger.info(
            f"Successfully generated response for user {risk_assessment.user_id} "
            f"with {len(guidelines)} guidelines"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving medical guidelines: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve medical guidelines: {str(e)}",
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="RAG Pipeline Health Check",
)
async def health_check():
    """
    Health check for RAG Medical Engine pipeline

    Returns:
        Status and configuration information
    """
    try:
        rag_pipeline = get_medical_rag_pipeline()
        return {
            "status": "healthy",
            "service": "RAG Medical Engine",
            "version": "1.0.0",
            "llm_provider": rag_pipeline.config.llm_provider,
            "embedding_provider": rag_pipeline.config.embedding_provider,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "RAG Medical Engine",
            "error": str(e),
        }


@router.post(
    "/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset RAG Pipeline",
)
async def reset_rag_pipeline():
    """
    Reset the RAG pipeline (useful for development/debugging)

    Returns:
        Confirmation message
    """
    global _rag_pipeline
    logger.info("Resetting RAG Medical Engine pipeline")
    _rag_pipeline = None
    return {"status": "success", "message": "RAG pipeline reset"}


# Optional: Add this router to your main FastAPI app:
# from fastapi import FastAPI
# from backend.api.medical_guidelines import router as rag_router
#
# app = FastAPI()
# app.include_router(rag_router)
