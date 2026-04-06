from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# ══════════════════════════════════════════════════════════════════════════════
# USER (polymorphic: admin / client)
# ══════════════════════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(20), nullable=False)          # "admin" | "client"
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    __mapper_args__ = {
        "polymorphic_on":       role,
        "polymorphic_identity": "user",
    }


class Admin(User):
    __tablename__    = "admins"
    id               = Column(Integer, ForeignKey("users.id"), primary_key=True)
    can_manage_users = Column(Boolean, default=True)

    __mapper_args__ = {"polymorphic_identity": "admin"}


class Client(User):
    __tablename__ = "clients"
    id            = Column(Integer, ForeignKey("users.id"), primary_key=True)

    # Demographics
    age               = Column(Integer)
    gender            = Column(String(10))
    height_cm         = Column(Float)
    weight_kg         = Column(Float)
    chronic_condition = Column(String(100))          # legacy field kept

    # Extended health form
    diseases          = Column(JSON, default=list)   # ["diabetes","hypertension"]
    medications       = Column(JSON, default=list)
    injuries          = Column(JSON, default=list)
    activity_level    = Column(String(20), default="sedentary")
    exercise_days_per_month = Column(Integer, default=0)
    goal_lose_weight  = Column(Boolean, default=False)
    goal_build_muscle = Column(Boolean, default=False)
    goal_endurance    = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "client"}

    biometrics = relationship(
        "Biometrics", back_populates="client",
        uselist=False, cascade="all, delete"
    )
    sessions = relationship(
        "ExerciseSession", back_populates="client",
        cascade="all, delete"
    )
    plans = relationship(
        "TrainingPlan", back_populates="client",
        order_by="TrainingPlan.generated_at"
    )
    checkins = relationship(
        "Checkin", back_populates="client",
        order_by="Checkin.created_at"
    )


# ══════════════════════════════════════════════════════════════════════════════
# BIOMETRICS  (1-to-1 with Client)
# ══════════════════════════════════════════════════════════════════════════════

class Biometrics(Base):
    __tablename__ = "biometrics"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    hba1c           = Column(Float)
    blood_pressure  = Column(String(20))             # "120/80"
    bmi             = Column(Float)
    hrv             = Column(Integer)                # heart rate variability (ms)
    daily_steps     = Column(Integer)
    vo2_max         = Column(Float)
    mood_score      = Column(Integer)                # 1-10
    recent_feedback = Column(Text)
    # Extended fields used by ML pipeline
    heart_rate               = Column(Float)
    blood_pressure_systolic  = Column(Float)
    blood_pressure_diastolic = Column(Float)
    sleep_hours              = Column(Float)
    fasting_glucose          = Column(Float)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    client = relationship("Client", back_populates="biometrics")


# ══════════════════════════════════════════════════════════════════════════════
# EXERCISE SESSION  (legacy — kept for compatibility)
# ══════════════════════════════════════════════════════════════════════════════

class ExerciseSession(Base):
    __tablename__ = "exercise_sessions"

    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(Integer, ForeignKey("users.id"), nullable=False)
    daily_goal           = Column(Text)
    exercises_json       = Column(Text)              # raw JSON string
    motivational_message = Column(Text)
    generated_at         = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="sessions")


# ══════════════════════════════════════════════════════════════════════════════
# TRAINING PLAN  (AI-generated, bi-weekly)
# ══════════════════════════════════════════════════════════════════════════════

class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_number   = Column(Integer, default=1)       # 1 → 3 → 5 … (+2 each checkin)
    risk_level    = Column(String(20))               # low/moderate/high/critical
    sentiment_label      = Column(String(20))
    recommended_intensity = Column(String(20))
    weekly_plan          = Column(JSON)              # {monday:{...}, tuesday:{...}, ...}
    warnings             = Column(JSON, default=list)
    motivational_message = Column(Text)
    medical_guidelines   = Column(JSON, default=list)
    generated_at  = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="plans")


# ══════════════════════════════════════════════════════════════════════════════
# CHECKIN  (bi-weekly progress review → triggers new TrainingPlan)
# ══════════════════════════════════════════════════════════════════════════════

class Checkin(Base):
    __tablename__ = "checkins"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Progress self-report
    sessions_completed = Column(Integer, default=0)  # out of 14 (2 weeks)
    avg_energy_level   = Column(Integer, default=5)  # 1-10
    avg_pain_level     = Column(Integer, default=0)  # 0-10
    weight_kg          = Column(Float)
    mood_text          = Column(Text)
    feedback_text      = Column(Text)

    # Updated biometrics at checkin time
    heart_rate               = Column(Float)
    blood_pressure_systolic  = Column(Float)
    blood_pressure_diastolic = Column(Float)
    sleep_hours              = Column(Float)
    daily_steps              = Column(Integer)

    # FK to the new plan generated after this checkin
    new_plan_id = Column(Integer, ForeignKey("training_plans.id"), nullable=True)

    client = relationship("Client", back_populates="checkins")