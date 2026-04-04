from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


# ─────────────────────────────────────────
# BIOMETRICS
# ─────────────────────────────────────────

class BiometricsBase(BaseModel):
    # Commun à tous
    hrv:             Optional[int]   = Field(None, example=35)
    daily_steps:     Optional[int]   = Field(None, example=3200)
    mood_score:      int             = Field(..., ge=1, le=10, example=4)
    recent_feedback: str             = Field(..., example="Je suis épuisé aujourd'hui.")

    # Diabète
    hba1c:           Optional[float] = Field(None, example=7.8)

    # Hypertension
    blood_pressure:  Optional[str]   = Field(None, example="135/88")

    # Général
    bmi:             Optional[float] = Field(None, example=27.5)
    vo2_max:         Optional[float] = Field(None, example=32.0)

class BiometricsCreate(BiometricsBase):
    pass

class BiometricsResponse(BiometricsBase):
    id:         int
    user_id:    int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# USER / ADMIN / CLIENT
# ─────────────────────────────────────────

class UserBase(BaseModel):
    name:  str            = Field(..., example="Karim Benali")
    email: EmailStr       = Field(..., example="karim@email.com")
    role:  str            = Field(..., example="client")  # "admin" ou "client"

class AdminCreate(UserBase):
    password:         str  = Field(..., example="admin1234")
    can_manage_users: bool = True

class ClientCreate(UserBase):
    password:          str           = Field(..., example="pass1234")
    age:               int           = Field(..., ge=18, le=100, example=55)
    gender:            Optional[str] = Field(None, example="Male")
    chronic_condition: str           = Field(..., example="Type 2 Diabetes")
    biometrics:        BiometricsCreate

class UserResponse(BaseModel):
    id:    int
    name:  str
    email: str
    role:  str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ClientResponse(UserResponse):
    age:               Optional[int] = None
    gender:            Optional[str] = None
    chronic_condition: Optional[str] = None
    biometrics:        Optional[BiometricsResponse] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# CONTRATS INTER-AGENTS (pour l'équipe)
# ─────────────────────────────────────────

class MedicalGuidelines(BaseModel):
    """Sortie du Membre 2 — RAG Agent"""
    condition:         str
    safe_exercises:    List[str]
    contraindications: List[str]
    intensity_limit:   str
    source_references: Optional[List[str]] = []

class UserAnalysis(BaseModel):
    """Sortie du Membre 4 — ML + Sentiment Agent"""
    dropout_risk:      float = Field(..., ge=0.0, le=1.0)
    sentiment_status:  str   = Field(..., example="Burnout")
    recommended_tone:  str   = Field(..., example="Empathic CBT")
    risk_explanation:  Optional[str] = None

class ExerciseItem(BaseModel):
    """Un exercice dans le plan"""
    name:      str            = Field(..., example="Marche lente")
    duration:  str            = Field(..., example="15 min")
    intensity: str            = Field(..., example="Faible")
    notes:     Optional[str]  = None

class ExercisePlan(BaseModel):
    """Sortie du Membre 3 — LLM Coach Agent"""
    user_id:              int
    daily_goal:           str
    exercises:            List[ExerciseItem]
    motivational_message: str
    generated_at:         Optional[datetime] = None
