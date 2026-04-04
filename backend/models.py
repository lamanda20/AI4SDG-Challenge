from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id                = Column(Integer, primary_key=True, index=True)
    name              = Column(String(100), nullable=False)
    email             = Column(String(150), unique=True, nullable=False)
    hashed_password   = Column(String(255), nullable=False)
    role              = Column(String(20), nullable=False)  # "admin" ou "client"
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    # Discriminateur pour l'héritage
    __mapper_args__ = {
        "polymorphic_on": role,
        "polymorphic_identity": "user",
    }


class Admin(User):
    __mapper_args__ = {
        "polymorphic_identity": "admin",
    }
    # Champs spécifiques à l'admin
    can_manage_users  = Column(Boolean, default=True)


class Client(User):
    __mapper_args__ = {
        "polymorphic_identity": "client",
    }
    # Champs spécifiques au client (patient)
    age               = Column(Integer)
    gender            = Column(String(10))
    chronic_condition = Column(String(100))

    biometrics = relationship("Biometrics", back_populates="user", uselist=False, cascade="all, delete")
    sessions   = relationship("ExerciseSession", back_populates="user", cascade="all, delete")


class Biometrics(Base):
    __tablename__ = "biometrics"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    hba1c           = Column(Float)
    blood_pressure  = Column(String(20))
    bmi             = Column(Float)
    hrv             = Column(Integer)
    daily_steps     = Column(Integer)
    vo2_max         = Column(Float)
    mood_score      = Column(Integer)
    recent_feedback = Column(Text)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("Client", back_populates="biometrics")


class ExerciseSession(Base):
    __tablename__ = "exercise_sessions"

    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(Integer, ForeignKey("users.id"), nullable=False)
    daily_goal           = Column(Text)
    exercises_json       = Column(Text)
    motivational_message = Column(Text)
    generated_at         = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("Client", back_populates="sessions")
