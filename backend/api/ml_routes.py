"""
FastAPI Integration for ML Module
Routes for ML pipeline processing
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import json

from ml.contracts import UserProfile, MLModuleOutput
from ml.pipeline import get_ml_pipeline, MLPipeline

# Create router
router = APIRouter(prefix="/api/ml", tags=["ML Pipeline"])


@router.post("/analyze")
async def analyze_user_profile(user_profile: dict) -> dict:
    """
    Main ML pipeline endpoint
    Takes user profile and returns risk assessment + sentiment analysis

    Example input:
    {
        "user_id": "user_123",
        "age": 55,
        "bmi": 28.5,
        "health_conditions": [...],
        "current_biometrics": {...}
    }
    """
    try:
        pipeline = get_ml_pipeline()
        result = pipeline.process_user_profile(user_profile)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML Pipeline Error: {str(e)}")


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    pipeline = get_ml_pipeline()
    return pipeline.health_check()


@router.post("/risk-only")
async def predict_risk_only(user_profile: dict) -> dict:
    """
    Risk prediction only (without sentiment)
    """
    try:
        pipeline = get_ml_pipeline()
        risks = pipeline.risk_model.predict_all_risks(user_profile)
        return {
            "user_id": user_profile.get("user_id"),
            "timestamp": datetime.utcnow().isoformat(),
            "predictions": risks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentiment-only")
async def analyze_sentiment_only(user_id: str, feedback: Optional[str] = None) -> dict:
    """
    Sentiment analysis only
    """
    try:
        pipeline = get_ml_pipeline()
        result = pipeline.motivation_engine.analyze_and_recommend({}, feedback)
        return {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

