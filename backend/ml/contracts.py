"""
JSON Contracts for ML Module
Standardized input/output formats for inter-module communication
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

# ============================================
# INPUT CONTRACT: User Biometric Profile
# ============================================

class BiometricData(BaseModel):
    """User's current biometric data"""
    heart_rate: float = Field(..., description="Current heart rate (bpm)")
    heart_rate_variability: float = Field(..., description="HRV (ms)")
    daily_steps: int = Field(..., description="Daily step count")
    sleep_duration: float = Field(..., description="Sleep duration (hours)")
    blood_pressure_systolic: float = Field(..., description="Systolic BP (mmHg)")
    blood_pressure_diastolic: float = Field(..., description="Diastolic BP (mmHg)")


class HealthCondition(BaseModel):
    """User's medical conditions"""
    condition_name: str = Field(..., description="e.g., 'diabetes', 'hypertension', 'depression'")
    severity: str = Field(..., description="'mild', 'moderate', 'severe'")
    duration_years: float = Field(..., description="Years with condition")


class UserProfile(BaseModel):
    """Input contract: Complete user profile"""
    user_id: str
    age: int = Field(..., ge=18, le=120)
    bmi: float = Field(..., gt=10, lt=60)
    vo2_max: Optional[float] = Field(None, description="VO2 max (ml/kg/min)")
    hba1c: Optional[float] = Field(None, description="HbA1c level (%) - if diabetic")
    fasting_glucose: Optional[float] = Field(None, description="Fasting glucose (mg/dL)")
    current_medications: List[str] = Field(default=[], description="List of current medications")
    exercise_history_days: int = Field(default=0, description="Days of exercise in past 30 days")
    health_conditions: List[HealthCondition]
    current_biometrics: BiometricData
    user_feedback_text: Optional[str] = Field(None, description="Optional text feedback from user")


# ============================================
# OUTPUT CONTRACT: ML Predictions
# ============================================

class RiskAssessment(BaseModel):
    """Risk predictions from XGBoost model"""
    risk_score: float = Field(..., ge=0, le=100, description="Overall risk score (0-100)")
    risk_level: str = Field(..., description="'low', 'moderate', 'high', 'critical'")
    progression_risk: float = Field(..., ge=0, le=100, description="Risk of condition progression")
    adherence_risk: float = Field(..., ge=0, le=100, description="Risk of exercise non-adherence")
    injury_risk: float = Field(..., ge=0, le=100, description="Risk of exercise-related injury")
    explanation: str = Field(..., description="Human-readable explanation using SHAP")


class SentimentAnalysis(BaseModel):
    """Sentiment & emotional state analysis"""
    sentiment_score: float = Field(..., ge=-1, le=1, description="-1: very negative, 0: neutral, 1: very positive")
    sentiment_label: str = Field(..., description="'negative', 'neutral', 'positive'")
    motivation_level: str = Field(..., description="'low', 'medium', 'high'")
    depression_risk_indicator: bool = Field(..., description="Potential depression detected?")
    cbt_intervention_needed: bool = Field(..., description="Should Motivator agent intervene with CBT?")
    confidence: float = Field(..., ge=0, le=1, description="Confidence of sentiment analysis")


class MLModuleOutput(BaseModel):
    """Output contract: Complete ML analysis"""
    user_id: str
    timestamp: str
    risk_assessment: RiskAssessment
    sentiment_analysis: SentimentAnalysis
    recommended_exercise_intensity: str = Field(..., description="'very_light', 'light', 'moderate', 'vigorous'")
    intensity_rationale: str = Field(..., description="Why this intensity level?")
    warnings: List[str] = Field(default=[], description="Safety warnings for coach")
    metadata: Dict = Field(default={}, description="Additional debug info")


# ============================================
# Example usage for testing
# ============================================

EXAMPLE_INPUT = {
    "user_id": "user_123",
    "age": 55,
    "bmi": 28.5,
    "vo2_max": 35.0,
    "hba1c": 7.2,
    "fasting_glucose": 120,
    "current_medications": ["Metformin", "Lisinopril"],
    "exercise_history_days": 5,
    "health_conditions": [
        {
            "condition_name": "diabetes",
            "severity": "moderate",
            "duration_years": 5
        }
    ],
    "current_biometrics": {
        "heart_rate": 72,
        "heart_rate_variability": 45,
        "daily_steps": 4200,
        "sleep_duration": 6.5,
        "blood_pressure_systolic": 135,
        "blood_pressure_diastolic": 85
    },
    "user_feedback_text": "I'm feeling a bit tired today but motivated to exercise"
}

EXAMPLE_OUTPUT = {
    "user_id": "user_123",
    "timestamp": "2026-04-04T10:30:00Z",
    "risk_assessment": {
        "risk_score": 62,
        "risk_level": "moderate",
        "progression_risk": 65,
        "adherence_risk": 40,
        "injury_risk": 35,
        "explanation": "Moderate risk due to suboptimal HbA1c (7.2%) and elevated BP. Low exercise adherence in past 30 days (5/30). Heart rate variability indicates some stress but within acceptable range."
    },
    "sentiment_analysis": {
        "sentiment_score": 0.55,
        "sentiment_label": "positive",
        "motivation_level": "medium",
        "depression_risk_indicator": False,
        "cbt_intervention_needed": False,
        "confidence": 0.82
    },
    "recommended_exercise_intensity": "light",
    "intensity_rationale": "Light intensity recommended due to moderate risk score and elevated fatigue indicators. Start with 20-30 min walking at conversational pace.",
    "warnings": [
        "Monitor blood pressure before exercise",
        "Stay hydrated - HRV suggests mild dehydration risk",
        "Avoid intense cardio without medical clearance"
    ],
    "metadata": {
        "model_version": "xgboost_v1.0",
        "feature_importance_top_3": ["hba1c", "bp_systolic", "exercise_adherence"]
    }
}

