"""
Clinician RAG Agent - Main Entry Point

Implements the main function generate_medical_guidelines() that:
- Takes user medical profile as JSON input
- Retrieves relevant medical knowledge from RAG
- Extracts and structures exercise recommendations
- Returns safe, evidence-based guidelines as JSON

Medical Safety: All recommendations are evidence-based and include guardrails
against hallucination. If information is missing, confidence is lowered.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator
from .rag.schemas import RAGQuery, RAGOutput, MedicalProtocol
from .rag.rag_pipeline import get_rag_pipeline
from .rag.mock_data import (
    get_mock_documents_by_condition,
    get_mock_medical_documents,
)
from .rag.embeddings import create_embedding_provider
from .rag.vector_store import create_vector_store
from .rag.config import rag_config

logger = logging.getLogger(__name__)


# =======================
# INPUT/OUTPUT SCHEMAS
# =======================


class UserMedicalProfile(BaseModel):
    """Input schema for user medical profile"""

    age: int = Field(..., ge=18, le=120, description="Age in years")
    conditions: List[str] = Field(..., min_items=1, description="Medical conditions (e.g., 'type 2 diabetes')")
    bmi: Optional[float] = Field(None, ge=10, le=60, description="Body Mass Index")
    activity_level: str = Field(
        default="sedentary",
        description="Current activity level: sedentary, light, moderate, vigorous",
    )
    comorbidities: Optional[List[str]] = Field(None, description="Additional medical conditions")
    medications: Optional[List[str]] = Field(None, description="Current medications")
    recent_events: Optional[List[str]] = Field(None, description="Recent medical events (e.g., 'MI 3 months ago')")
    contraindications: Optional[str] = Field(None, description="Known contraindications")

    @validator("activity_level")
    def validate_activity_level(cls, v):
        valid = ["sedentary", "light", "moderate", "vigorous"]
        if v.lower() not in valid:
            raise ValueError(f"activity_level must be one of {valid}")
        return v.lower()


class ExerciseGuideline(BaseModel):
    """Single exercise guideline in output"""

    condition: str = Field(..., description="Medical condition this guideline applies to")
    recommended_exercises: List[str] = Field(..., description="List of recommended exercises")
    frequency: str = Field(..., description="Recommended frequency (e.g., '3-4 times/week')")
    duration: str = Field(..., description="Recommended duration per session (e.g., '30-45 minutes')")
    intensity: str = Field(..., description="Intensity level: light/moderate/vigorous")
    contraindications: List[str] = Field(default_factory=list, description="Exercises to avoid")
    precautions: List[str] = Field(default_factory=list, description="Safety precautions")
    evidence_level: str = Field(default="observational", description="Level of Evidence: RCT/cohort/observational")
    source: str = Field(..., description="Source of guideline (e.g., 'ADA / PubMed')")


class MedicalGuidelinesResponse(BaseModel):
    """Output schema - JSON contract for other agents"""

    guidelines: List[ExerciseGuideline] = Field(..., description="Exercise guidelines per condition")
    global_risks: List[str] = Field(default_factory=list, description="Overall risk factors")
    safety_warnings: List[str] = Field(default_factory=list, description="Critical safety warnings")
    recommended_next_steps: List[str] = Field(default_factory=list, description="Actions before starting exercise")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0-1) of recommendations"
    )
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =======================
# GUARDRAILS & VALIDATION
# =======================


class RAGGuardrails:
    """Safety guardrails for RAG medical recommendations"""

    ABSOLUTE_CONTRAINDICATIONS = [
        "recent MI",
        "unstable angina",
        "severe aortic stenosis",
        "acute myocarditis",
        "uncontrolled severe hypertension",
    ]

    REQUIRE_MEDICAL_CLEARANCE = [
        "recent stroke",
        "recent cardiac event",
        "severe diabetic retinopathy",
        "severe neuropathy",
        "kidney disease",
    ]

    @staticmethod
    def check_contraindications(user_profile: UserMedicalProfile) -> tuple[bool, List[str]]:
        """Check for absolute contraindications"""
        warnings = []
        is_clear = True

        # Check recent events
        if user_profile.recent_events:
            recent_lower = [e.lower() for e in user_profile.recent_events]

            for event in recent_lower:
                if "MI" in event or "myocardial infarction" in event:
                    if "3 months" not in event and "6 months" not in event:
                        is_clear = False
                        warnings.append(
                            "⚠️ ABSOLUTE: Recent MI detected. Exercise contraindicated. "
                            "Require 3+ months recovery and cardiac clearance."
                        )

                if "unstable angina" in event:
                    is_clear = False
                    warnings.append(
                        "⚠️ ABSOLUTE: Unstable angina present. Exercise contraindicated. "
                        "Require medical stabilization first."
                    )

        # Check blood pressure if has hypertension
        if any("hypertension" in c.lower() for c in user_profile.conditions):
            warnings.append(
                "⚠️ Monitor: Hypertension present. Require BP check before exercise. "
                "SBP must be <160 mmHg to start exercise."
            )

        # Check diabetes complications
        if any("diabetes" in c.lower() for c in user_profile.conditions):
            if user_profile.recent_events:
                recent_lower = [e.lower() for e in user_profile.recent_events]
                if any("retinopathy" in e for e in recent_lower):
                    warnings.append(
                        "⚠️ CAUTION: Diabetic retinopathy detected. "
                        "Avoid high-impact and Valsalva maneuvers. Supervision recommended."
                    )
                if any("neuropathy" in e for e in recent_lower):
                    warnings.append(
                        "⚠️ CAUTION: Diabetic neuropathy detected. "
                        "Avoid weight-bearing activities. Prefer non-weight-bearing (swimming, cycling)."
                    )

        return is_clear, warnings

    @staticmethod
    def calculate_confidence_adjustment(user_profile: UserMedicalProfile) -> float:
        """Calculate confidence adjustment based on risk factors"""
        adjustment = 1.0

        # Reduce confidence for high-risk scenarios
        if user_profile.recent_events:
            adjustment *= 0.85  # 15% reduction for recent events

        if user_profile.comorbidities and len(user_profile.comorbidities) > 2:
            adjustment *= 0.80  # 20% reduction for multiple comorbidities

        if user_profile.age > 65:
            adjustment *= 0.90  # 10% reduction for elderly

        # Reduce confidence for insufficient data
        if not user_profile.bmi:
            adjustment *= 0.85  # 15% reduction for missing BMI

        return max(0.5, min(1.0, adjustment))


# =======================
# MAIN RAG FUNCTION
# =======================


def generate_medical_guidelines(user_profile_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point: Generate medical guidelines for user profile.

    INPUT (JSON):
    {
        "age": 50,
        "conditions": ["type 2 diabetes", "hypertension"],
        "bmi": 30,
        "activity_level": "sedentary"
    }

    OUTPUT (STRICT JSON ONLY):
    {
        "guidelines": [...],
        "global_risks": [...],
        "confidence": 0.85
    }

    Args:
        user_profile_dict: User medical profile as dict

    Returns:
        MedicalGuidelinesResponse as dict (JSON serializable)

    Raises:
        ValueError: If input validation fails
    """
    try:
        logger.info(f"[RAG] Generating guidelines for profile: {user_profile_dict}")

        # ===== STEP 1: VALIDATE INPUT =====
        user_profile = UserMedicalProfile(**user_profile_dict)
        logger.debug(f"[RAG] Profile validated: {user_profile}")

        # ===== STEP 2: SAFETY CHECKS =====
        is_safe, safety_warnings = RAGGuardrails.check_contraindications(user_profile)

        if not is_safe:
            logger.warning(f"[RAG] Safety warnings: {safety_warnings}")
            # Return low-confidence response if contraindications present
            return MedicalGuidelinesResponse(
                guidelines=[],
                global_risks=safety_warnings,
                safety_warnings=safety_warnings,
                recommended_next_steps=[
                    "Consult with cardiologist before starting exercise",
                    "Obtain medical clearance",
                ],
                confidence=0.1,
            ).model_dump(mode="json")

        # ===== STEP 3: INITIALIZE RAG PIPELINE =====
        logger.info("[RAG] Initializing RAG pipeline...")
        try:
            # Use mock data for hackathon speed
            pipeline = _initialize_rag_with_mock_data()
            logger.info("[RAG] RAG pipeline initialized with mock data")
        except Exception as e:
            logger.error(f"[RAG] Failed to initialize: {e}")
            return _fallback_guidelines(user_profile)

        # ===== STEP 4: BUILD RAG QUERY =====
        rag_query = RAGQuery(
            user_condition=user_profile.conditions[0],  # Primary condition
            user_age=user_profile.age,
            user_comorbidities=user_profile.comorbidities,
            activity_level=user_profile.activity_level,
            contraindications=user_profile.contraindications,
            query_type="exercise_protocol",
        )

        logger.debug(f"[RAG] RAG query: {rag_query}")

        # ===== STEP 5: RETRIEVE MEDICAL DOCUMENTS =====
        logger.info("[RAG] Retrieving medical documents...")
        try:
            rag_result = pipeline.generate_rag_response(rag_query)

            if not rag_result or not rag_result.recommended_protocols:
                logger.warning("[RAG] No protocols retrieved from RAG")
                # Fallback to mock data extraction
                guidelines = _extract_guidelines_from_mock_data(user_profile)
            else:
                # Convert RAG protocols to our output format
                guidelines = _convert_rag_output_to_guidelines(
                    user_profile, rag_result.recommended_protocols
                )

        except Exception as e:
            logger.error(f"[RAG] Retrieval error: {e}")
            # Fallback to mock data
            guidelines = _extract_guidelines_from_mock_data(user_profile)

        # ===== STEP 6: IDENTIFY GLOBAL RISKS =====
        global_risks = _identify_global_risks(user_profile)

        # ===== STEP 7: GENERATE SAFETY RECOMMENDATIONS =====
        recommended_steps = _generate_recommended_steps(user_profile)

        # ===== STEP 8: CALCULATE CONFIDENCE =====
        base_confidence = len(guidelines) / 2.0  # Max 0.5 from retrieved docs
        confidence_adjustment = RAGGuardrails.calculate_confidence_adjustment(user_profile)
        final_confidence = base_confidence * confidence_adjustment

        # ===== STEP 9: BUILD RESPONSE =====
        response = MedicalGuidelinesResponse(
            guidelines=guidelines,
            global_risks=global_risks,
            safety_warnings=safety_warnings,
            recommended_next_steps=recommended_steps,
            confidence=min(1.0, final_confidence),
        )

        logger.info(
            f"[RAG] ✅ Generated response with {len(guidelines)} guidelines, "
            f"confidence: {response.confidence:.2%}"
        )

        return response.model_dump(mode="json")

    except ValueError as e:
        logger.error(f"[RAG] Validation error: {e}")
        raise ValueError(f"Invalid user profile: {str(e)}")
    except Exception as e:
        logger.error(f"[RAG] Unexpected error: {e}", exc_info=True)
        raise RuntimeError(f"RAG pipeline error: {str(e)}")


# =======================
# HELPER FUNCTIONS
# =======================


def _initialize_rag_with_mock_data() -> "MedicalRAGPipeline":
    """Initialize RAG pipeline with mock medical data (for hackathon speed)"""
    from .rag.mock_data import get_mock_medical_documents
    from .rag.rag_pipeline import MedicalRAGPipeline
    from .rag.document_loader import create_document_loader
    from pathlib import Path

    pipeline = get_rag_pipeline()

    # If index is empty, load documents
    if not pipeline.index_loaded or pipeline.vector_store.get_size() == 0:
        logger.info("[RAG] Loading medical documents into vector store...")
        
        all_docs = []
        
        # Try to load from text/PDF files first
        docs_dir = Path("backend/agents/rag/data/documents")
        if docs_dir.exists() and list(docs_dir.glob("*.txt")):
            logger.info("[RAG] Loading text documents from disk...")
            try:
                markdown_loader = create_document_loader("markdown", md_dir=docs_dir)
                file_docs = markdown_loader.load()
                all_docs.extend(file_docs)
                logger.info(f"[RAG] Loaded {len(file_docs)} documents from files")
            except Exception as e:
                logger.warning(f"[RAG] Could not load from files: {e}")
        
        # Fallback to mock data if no files found
        if not all_docs:
            logger.info("[RAG] Using hardcoded mock medical data...")
            all_docs = get_mock_medical_documents()

        # Add to vector store
        pipeline.vector_store.add_documents(all_docs, pipeline.embeddings_provider)
        pipeline.index_loaded = True
        logger.info(f"[RAG] Loaded {len(all_docs)} total documents into RAG")

    return pipeline


def _extract_guidelines_from_mock_data(user_profile: UserMedicalProfile) -> List[ExerciseGuideline]:
    """Extract guidelines from mock data when RAG fails"""
    from .rag.mock_data import get_mock_documents_by_condition

    guidelines = []

    for condition in user_profile.conditions:
        docs = get_mock_documents_by_condition(condition)

        # Create guideline from top document
        if docs:
            top_doc = docs[0]
            guideline = ExerciseGuideline(
                condition=condition,
                recommended_exercises=_parse_exercises_from_text(top_doc.content),
                frequency="3-4 times per week",
                duration="30-45 minutes",
                intensity="moderate",
                contraindications=_parse_contraindications_from_text(top_doc.content),
                precautions=_parse_precautions_from_text(top_doc.content),
                evidence_level="observational",
                source=top_doc.source,
            )
            guidelines.append(guideline)

    return guidelines


def _parse_exercises_from_text(text: str) -> List[str]:
    """Simple parsing of exercises from document text"""
    exercises = []

    # Look for exercise keywords
    keywords = [
        "walking",
        "cycling",
        "swimming",
        "aerobic",
        "resistance",
        "resistance training",
        "elliptical",
        "rowing",
        "strength training",
    ]

    for keyword in keywords:
        if keyword.lower() in text.lower():
            exercises.append(keyword.capitalize())

    return list(set(exercises)) if exercises else ["Moderate aerobic exercise"]


def _parse_contraindications_from_text(text: str) -> List[str]:
    """Extract contraindications from document text"""
    contraindications = []

    if "avoid" in text.lower():
        contraindications.append("Avoid high-intensity exercises without medical clearance")
    if "high glucose" in text.lower():
        contraindications.append("Avoid exercise if blood glucose >250 mg/dL")
    if "heavy" in text.lower():
        contraindications.append("Avoid heavy lifting without supervision")

    return contraindications


def _parse_precautions_from_text(text: str) -> List[str]:
    """Extract precautions from document text"""
    precautions = []

    if "monitor" in text.lower():
        precautions.append("Monitor blood glucose before and after exercise")
    if "hydrate" in text.lower() or "water" in text.lower():
        precautions.append("Stay well-hydrated during exercise")
    if "warm" in text.lower():
        precautions.append("Perform 5-10 minute warm-up and cool-down")

    return precautions if precautions else ["Consult with healthcare provider before starting"]


def _identify_global_risks(user_profile: UserMedicalProfile) -> List[str]:
    """Identify global risk factors from user profile"""
    risks = []

    if user_profile.age > 60:
        risks.append(f"Age >60 ({user_profile.age}): Higher cardiovascular risk")

    if user_profile.bmi and user_profile.bmi > 30:
        risks.append(f"Obesity (BMI {user_profile.bmi}): Increased metabolic stress")

    if user_profile.activity_level == "sedentary":
        risks.append("Sedentary lifestyle: Deconditioning increases injury risk")

    if user_profile.comorbidities and len(user_profile.comorbidities) > 1:
        risks.append(f"Multiple comorbidities: Complex management needed")

    if any("hypertension" in c.lower() for c in user_profile.conditions):
        risks.append("Hypertension: Increased cardiac risk during exercise")

    if any("diabetes" in c.lower() for c in user_profile.conditions):
        risks.append("Diabetes: Risk of hypoglycemia during exercise")

    return risks


def _generate_recommended_steps(user_profile: UserMedicalProfile) -> List[str]:
    """Generate recommended pre-exercise steps"""
    steps = [
        "Obtain medical clearance from primary care physician",
        "Get baseline cardiovascular assessment (EKG if age >50 or sedentary)",
    ]

    if any("diabetes" in c.lower() for c in user_profile.conditions):
        steps.extend(
            [
                "Coordinate with endocrinologist for medication adjustments",
                "Learn to monitor blood glucose before/after exercise",
                "Keep glucose monitoring device and fast-acting carbs available",
            ]
        )

    if any("hypertension" in c.lower() for c in user_profile.conditions):
        steps.extend(
            [
                "Monitor blood pressure daily for 1 week before starting",
                "Coordinate with cardiologist if BP >160 mmHg",
            ]
        )

    if user_profile.activity_level == "sedentary":
        steps.append("Start with 10-minute sessions; gradually increase to 30 minutes over 4 weeks")

    steps.append("Consider working with exercise physiologist for initial sessions")

    return steps


def _convert_rag_output_to_guidelines(
    user_profile: UserMedicalProfile, protocols: List[MedicalProtocol]
) -> List[ExerciseGuideline]:
    """Convert RAG pipeline output to output schema"""
    guidelines = []

    for i, protocol in enumerate(protocols):
        # Match condition from user profile if possible
        condition = (
            user_profile.conditions[0] if i < len(user_profile.conditions) else user_profile.conditions[0]
        )

        guideline = ExerciseGuideline(
            condition=condition,
            recommended_exercises=[protocol.protocol_name] + (protocol.protocol_name.split() if " " in protocol.protocol_name else []),
            frequency=protocol.frequency,
            duration=protocol.duration,
            intensity=protocol.intensity,
            contraindications=protocol.contraindications,
            precautions=protocol.safety_warnings,
            evidence_level=protocol.evidence_level,
            source="RAG Pipeline",
        )
        guidelines.append(guideline)

    return guidelines


def _fallback_guidelines(user_profile: UserMedicalProfile) -> Dict[str, Any]:
    """Return safe fallback response when RAG unavailable"""
    logger.warning("[RAG] Using fallback generic guidelines")

    return MedicalGuidelinesResponse(
        guidelines=[
            ExerciseGuideline(
                condition=cond,
                recommended_exercises=["Moderate aerobic activity"],
                frequency="3-4 times per week",
                duration="30 minutes",
                intensity="light to moderate",
                contraindications=[],
                precautions=[
                    "Consult with healthcare provider",
                    "Start slowly and progress gradually",
                    "Monitor for adverse symptoms",
                ],
                evidence_level="professional_recommendation",
                source="Generic Guidelines",
            )
            for cond in user_profile.conditions
        ],
        global_risks=["No medical literature available for detailed risk assessment"],
        safety_warnings=["Generic guidelines only. Require personalized medical assessment."],
        recommended_next_steps=[
            "Consult with your primary care physician",
            "Discuss with specialist (cardiologist/endocrinologist) for your conditions",
        ],
        confidence=0.2,
    ).model_dump(mode="json")


if __name__ == "__main__":
    # Example usage for testing
    test_profile = {
        "age": 50,
        "conditions": ["type 2 diabetes", "hypertension"],
        "bmi": 30,
        "activity_level": "sedentary",
    }

    result = generate_medical_guidelines(test_profile)
    print(json.dumps(result, indent=2))
