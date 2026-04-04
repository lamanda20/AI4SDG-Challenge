"""
RAG Data Models & Schemas

Defines the JSON contracts and data structures for:
- Retrieved medical documents
- RAG pipeline inputs/outputs
- Query information
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class MedicalDocument(BaseModel):
    """A medical document chunk from PubMed or medical literature"""

    id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document text chunk")
    source: str = Field(..., description="Source (PubMed, PDF, etc.)")
    pubmed_id: Optional[str] = Field(None, description="PubMed PMID if applicable")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    authors: Optional[List[str]] = Field(None, description="Document authors")
    published_date: Optional[str] = Field(None, description="Publication date")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGQuery(BaseModel):
    """Input query for RAG retrieval"""

    user_condition: str = Field(..., description="Primary medical condition (e.g., 'Type 2 Diabetes')")
    user_age: int = Field(..., ge=18, description="User age in years")
    user_comorbidities: Optional[List[str]] = Field(None, description="Additional conditions")
    activity_level: str = Field(default="moderate", description="Current activity level")
    contraindications: Optional[str] = Field(None, description="Medical contraindications")
    query_type: str = Field(default="exercise_protocol", description="Type of query")


class RAGQueryResult(BaseModel):
    """Retrieved documents from vector store"""

    query: RAGQuery
    retrieved_documents: List[MedicalDocument] = Field(..., description="Top-k retrieved documents")
    total_retrieved: int = Field(..., description="Number of documents retrieved")
    retrieval_time_ms: float = Field(..., description="Retrieval latency in milliseconds")


class MedicalProtocol(BaseModel):
    """Extracted medical protocol from RAG output"""

    protocol_name: str = Field(..., description="Name of exercise protocol")
    description: str = Field(..., description="Protocol description")
    frequency: str = Field(..., description="Recommended frequency (e.g., '3-4x per week')")
    duration: str = Field(..., description="Session duration (e.g., '30-45 minutes')")
    intensity: str = Field(..., description="Intensity level")
    contraindications: List[str] = Field(default_factory=list)
    safety_warnings: List[str] = Field(default_factory=list)
    evidence_level: str = Field(default="observational", description="Level of clinical evidence")
    citations: List[str] = Field(..., description="PubMed IDs supporting this protocol")


class RAGOutput(BaseModel):
    """Final output from RAG Medical Engine - JSON CONTRACT for other agents"""

    query: RAGQuery
    recommended_protocols: List[MedicalProtocol] = Field(..., description="Recommended exercise protocols")
    safety_considerations: str = Field(..., description="Overall safety considerations")
    contraindicated_exercises: List[str] = Field(default_factory=list)
    supporting_evidence: Dict[str, List[str]] = Field(default_factory=dict)
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendations")
    retrieved_document_count: int = Field(..., description="Number of documents used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": {
                    "user_condition": "Type 2 Diabetes",
                    "user_age": 55,
                    "activity_level": "sedentary"
                },
                "recommended_protocols": [
                    {
                        "protocol_name": "Aerobic Exercise Training",
                        "frequency": "3-4 times per week",
                        "intensity": "moderate",
                        "citations": ["PMID:12345678"]
                    }
                ]
            }
        }


class RAGEmbeddingMetadata(BaseModel):
    """Metadata for embedding tracking"""

    document_id: str
    embedding_model: str
    embedding_dimension: int
    chunk_size: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== NEW: Risk-Aware RAG Interface ====================


class RiskAssessment(BaseModel):
    """Input from ML Agent - Risk assessment of patient"""

    user_id: str = Field(..., description="Patient identifier")
    risk_level: str = Field(..., description="Risk level: low, moderate, high, critical")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score 0.0-1.0")
    risk_factors: List[str] = Field(default_factory=list, description="Primary risk factors")
    comorbidities: List[str] = Field(default_factory=list, description="Medical comorbidities")
    age: Optional[int] = Field(None, ge=18, description="Patient age in years")
    activity_level: Optional[str] = Field(default="sedentary", description="Current activity level")
    contraindications: Optional[str] = Field(None, description="Medical contraindications")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "patient_123",
                "risk_level": "high",
                "risk_score": 0.78,
                "risk_factors": ["sedentary", "obesity"],
                "comorbidities": ["type2_diabetes", "hypertension"],
                "age": 55,
                "activity_level": "sedentary",
            }
        }


class MedicalGuideline(BaseModel):
    """Exercise protocol tailored to patient risk level"""

    protocol_id: str = Field(..., description="Unique protocol identifier")
    protocol_name: str = Field(..., description="Name of exercise protocol")
    description: str = Field(..., description="Protocol description")

    # Adjustable for risk level
    frequency: str = Field(..., description="Recommended frequency (e.g., '3x per week')")
    duration: str = Field(..., description="Session duration (e.g., '20-30 minutes')")
    intensity: str = Field(..., description="Intensity level (light/moderate/vigorous)")

    # Safety focused
    safety_precautions: List[str] = Field(default_factory=list, description="Safety measures")
    contraindications: List[str] = Field(default_factory=list, description="Exercise contraindications")
    monitoring_parameters: Dict[str, str] = Field(
        default_factory=dict, description="What to monitor (e.g., heart_rate: 'below 120 bpm')"
    )

    # Evidence
    evidence_level: str = Field(
        default="observational", description="Level: randomized_controlled_trial, cohort_study, observational"
    )
    citations: List[str] = Field(default_factory=list, description="PubMed IDs supporting this protocol")

    # For Coach adaptation
    adaptability: str = Field(default="moderate", description="Can this be adapted/progressed?")
    progression_path: Optional[str] = Field(None, description="How to progress this protocol")

    # Metadata
    risk_level_applied: str = Field(..., description="Risk level this protocol was designed for")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "protocol_name": "Supervised Aerobic Walking",
                "intensity": "light",
                "frequency": "3-4 times per week",
                "duration": "20-30 minutes",
                "safety_precautions": ["Start with 5 min warm-up", "Monitor heart rate", "Stop if chest pain"],
                "monitoring_parameters": {"heart_rate": "target 50-70% of max HR", "symptoms": "check for dizziness"},
                "citations": ["PMID:12345678"],
                "risk_level_applied": "high",
            }
        }


class MedicalGuidelinesResponse(BaseModel):
    """Complete response from RAG Medical Engine"""

    status: str = Field(default="success", description="Response status")
    user_id: str = Field(..., description="Patient identifier")
    risk_level_applied: str = Field(..., description="Risk level used for recommendations")
    medical_guidelines: List[MedicalGuideline] = Field(..., description="Recommended protocols")
    safety_summary: str = Field(..., description="Overall safety summary")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendations")
    retrieved_document_count: int = Field(..., description="Number of documents used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "user_id": "patient_123",
                "risk_level_applied": "high",
                "medical_guidelines": [{}],  # MedicalGuideline example
                "safety_summary": "Conservative protocols recommended.",
                "confidence_score": 0.87,
                "retrieved_document_count": 5,
            }
        }
