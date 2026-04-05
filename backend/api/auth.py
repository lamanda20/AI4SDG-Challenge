"""
api/auth.py
POST /auth/register  → form complet + création compte Client + génère plan initial
POST /auth/login     → JWT token
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib, os, jwt

from backend.database import get_db
from backend.schemas import RegisterRequest, LoginRequest, TokenResponse, UserFormInput
from backend.crud import get_user_by_email, create_client, save_plan
from backend.services.feature_engineering import compute_features
from backend.agents.motivator_ml import run_ml_analysis
from backend.services.vector_query import build_rag_query
from backend.agents.clinician_rag import retrieve_guidelines
from backend.agents.prescriber_llm import generate_plan

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("JWT_SECRET", "sportrx-secret-change-in-prod")
ALGORITHM  = "HS256"


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _create_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(days=7)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _verify_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, data.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    # Build form dict for DB + ML pipeline
    form = data.model_dump(exclude={"email", "password", "name"})

    # Create Client + Biometrics in DB
    client = create_client(db, data.name, data.email, _hash_password(data.password), form)

    # Generate first training plan via full pipeline
    form["user_id"] = str(client.id)
    form_obj   = UserFormInput(**form)
    features   = compute_features(form_obj)
    ml_output  = run_ml_analysis(features)
    rag_query  = build_rag_query(features, ml_output)
    guidelines = retrieve_guidelines(rag_query)
    plan_data  = generate_plan(features, ml_output, guidelines)

    save_plan(db, client.id, {
        "risk_level":             ml_output["risk_assessment"]["risk_level"],
        "sentiment_label":        ml_output["sentiment_analysis"]["sentiment_label"],
        "recommended_intensity":  ml_output["recommended_exercise_intensity"],
        "weekly_plan":            plan_data["weekly_plan"],
        "warnings":               ml_output.get("warnings", []),
        "motivational_message":   plan_data.get("motivational_message", ""),
        "medical_guidelines":     guidelines,
    }, week_number=1)

    return TokenResponse(access_token=_create_token(client.id))


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, data.email)
    if not user or user.hashed_password != _hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=_create_token(user.id))


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
def login_swagger(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 form-based login — used by Swagger UI Authorize button."""
    user = get_user_by_email(db, form.username)  # username = email in Swagger
    if not user or user.hashed_password != _hash_password(form.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=_create_token(user.id))
