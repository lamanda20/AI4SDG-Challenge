from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional, Dict
from enum import Enum


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class ActivityLevel(str, Enum):
    sedentary   = "sedentary"
    light       = "light"
    moderate    = "moderate"
    active      = "active"
    very_active = "very_active"


# ── Auth ───────────────────────────────────────────────────────────────────────

class UserFormInput(BaseModel):
    """Internal form object used by feature_engineering."""
    user_id: str
    age: int = Field(..., ge=18, le=120)
    gender: Gender
    height_cm: float = Field(..., gt=100, lt=250)
    weight_kg: float = Field(..., gt=20, lt=300)
    diseases:    List[str] = []
    medications: List[str] = []
    injuries:    List[str] = []
    activity_level: ActivityLevel = ActivityLevel.sedentary
    exercise_days_per_month: int = Field(default=0, ge=0, le=31)
    goal_lose_weight:  bool = False
    goal_build_muscle: bool = False
    goal_endurance:    bool = False
    mood:            Optional[str] = None
    motivation_text: Optional[str] = None
    current_heart_rate:       Optional[float] = None
    daily_steps:              Optional[int]   = None
    sleep_hours:              Optional[float] = None
    blood_pressure_systolic:  Optional[float] = None
    blood_pressure_diastolic: Optional[float] = None
    hba1c:           Optional[float] = None
    fasting_glucose: Optional[float] = None
    vo2_max:         Optional[float] = None


class RegisterRequest(BaseModel):
    name:     str   = Field(..., min_length=2, max_length=100)
    email:    EmailStr
    password: str   = Field(..., min_length=6)

    # Personal
    age:       int   = Field(..., ge=18, le=120)
    gender:    Gender
    height_cm: float = Field(..., gt=100, lt=250)
    weight_kg: float = Field(..., gt=20,  lt=300)

    # Health
    diseases:    List[str] = []
    medications: List[str] = []
    injuries:    List[str] = []

    # Fitness
    activity_level:          ActivityLevel = ActivityLevel.sedentary
    exercise_days_per_month: int           = Field(default=0, ge=0, le=31)

    # Goals
    goal_lose_weight:  bool = False
    goal_build_muscle: bool = False
    goal_endurance:    bool = False

    # Mental
    mood:            Optional[str] = None
    motivation_text: Optional[str] = None

    # Biometrics (optional)
    current_heart_rate:       Optional[float] = None
    daily_steps:              Optional[int]   = None
    sleep_hours:              Optional[float] = None
    blood_pressure_systolic:  Optional[float] = None
    blood_pressure_diastolic: Optional[float] = None
    hba1c:           Optional[float] = None
    fasting_glucose: Optional[float] = None
    vo2_max:         Optional[float] = None

    @field_validator("diseases", "medications", "injuries", mode="before")
    @classmethod
    def parse_comma_string(cls, v):
        if isinstance(v, str):
            return [x.strip().lower() for x in v.split(",") if x.strip()]
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Checkin (bi-weekly) ────────────────────────────────────────────────────────

class CheckinRequest(BaseModel):
    sessions_completed: int = Field(..., ge=0, le=14, description="Sessions done in last 2 weeks")
    avg_energy_level:   int = Field(..., ge=1, le=10)
    avg_pain_level:     int = Field(default=0, ge=0, le=10)
    weight_kg:          Optional[float] = None
    mood_text:          Optional[str]   = None
    feedback_text:      Optional[str]   = None
    # Updated biometrics
    current_heart_rate:       Optional[float] = None
    blood_pressure_systolic:  Optional[float] = None
    blood_pressure_diastolic: Optional[float] = None
    sleep_hours:              Optional[float] = None
    daily_steps:              Optional[int]   = None


# ── Responses ──────────────────────────────────────────────────────────────────

class TrainingPlanResponse(BaseModel):
    id: int
    week_number: int
    risk_level: str
    sentiment_label: str
    recommended_intensity: str
    weekly_plan: Dict
    warnings: List[str]
    motivational_message: str
    medical_guidelines: List[str]
    created_at: str

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    age: int
    gender: str
    weight_kg: float
    height_cm: float
    diseases: List[str]
    activity_level: str
    latest_plan: Optional[TrainingPlanResponse] = None
    total_plans: int = 0
    total_checkins: int = 0

    class Config:
        from_attributes = True


class CheckinResponse(BaseModel):
    checkin_id: int
    week_number: int
    new_plan: TrainingPlanResponse
    progress_summary: str
