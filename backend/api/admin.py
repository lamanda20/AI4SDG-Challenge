"""
api/admin.py
Admin-only backend analytics endpoints (no frontend required).
"""

from collections import Counter
from typing import Dict, List
import hashlib
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models import Admin, Checkin, Client, TrainingPlan, User
from crud import create_admin, get_user_by_email, get_user_by_id
from schemas import (
    AdminBootstrapRequest,
    AdminBootstrapResponse,
    AdminOverviewResponse,
    CountByLabel,
    DiseaseMatrixPoint,
)
from api.auth import _create_token, _verify_token

router = APIRouter(prefix="/admin", tags=["admin"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _infer_region_from_email(email: str) -> str:
    value = email.lower().strip()
    if value.endswith(".ma"):
        return "Morocco"
    if value.endswith(".fr"):
        return "France"
    if value.endswith(".dz"):
        return "Algeria"
    if value.endswith(".tn"):
        return "Tunisia"
    if value.endswith(".uk"):
        return "United Kingdom"
    if value.endswith(".us"):
        return "United States"
    return "Unknown"


def _list_diseases(client: Client) -> List[str]:
    diseases = client.diseases or []
    if isinstance(diseases, list) and diseases:
        return [str(item).strip().lower() for item in diseases if str(item).strip()]

    if client.chronic_condition:
        return [str(client.chronic_condition).strip().lower()]

    return ["none_reported"]


def _require_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user_id = _verify_token(token)
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.post("/bootstrap", response_model=AdminBootstrapResponse, status_code=201)
def bootstrap_admin(payload: AdminBootstrapRequest, db: Session = Depends(get_db)):
    expected_key = os.getenv("ADMIN_BOOTSTRAP_KEY", "sportrx-admin-bootstrap")
    if payload.bootstrap_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid bootstrap key")

    existing = get_user_by_email(db, payload.email)
    if existing:
        if existing.role != "admin":
            raise HTTPException(status_code=409, detail="Email already used by non-admin account")
        return AdminBootstrapResponse(
            admin_id=existing.id,
            email=existing.email,
            token=_create_token(existing.id),
        )

    admin = create_admin(db, payload.name, payload.email, _hash_password(payload.password))
    return AdminBootstrapResponse(admin_id=admin.id, email=admin.email, token=_create_token(admin.id))


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(_: User = Depends(_require_admin), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_clients = db.query(Client).count()
    total_admins = db.query(Admin).count()
    total_plans = db.query(TrainingPlan).count()
    total_checkins = db.query(Checkin).count()

    risk_counter = Counter(
        (plan.risk_level or "unknown").lower() for plan in db.query(TrainingPlan).all()
    )
    activity_counter = Counter(
        (client.activity_level or "unknown").lower() for client in db.query(Client).all()
    )

    return AdminOverviewResponse(
        total_users=total_users,
        total_clients=total_clients,
        total_admins=total_admins,
        total_plans=total_plans,
        total_checkins=total_checkins,
        risk_levels=[CountByLabel(label=k, count=v) for k, v in sorted(risk_counter.items())],
        activity_levels=[CountByLabel(label=k, count=v) for k, v in sorted(activity_counter.items())],
    )


@router.get("/analytics/disease-risk", response_model=List[DiseaseMatrixPoint])
def disease_risk_matrix(_: User = Depends(_require_admin), db: Session = Depends(get_db)):
    latest_plan_by_user: Dict[int, TrainingPlan] = {}
    for plan in db.query(TrainingPlan).order_by(TrainingPlan.generated_at.desc()).all():
        latest_plan_by_user.setdefault(plan.user_id, plan)

    matrix = Counter()
    for client in db.query(Client).all():
        risk = (latest_plan_by_user.get(client.id).risk_level if latest_plan_by_user.get(client.id) else "unknown")
        risk = (risk or "unknown").lower()
        for disease in _list_diseases(client):
            matrix[(disease, risk)] += 1

    return [
        DiseaseMatrixPoint(disease=disease, segment=segment, count=count)
        for (disease, segment), count in sorted(matrix.items())
    ]


@router.get("/analytics/disease-activity", response_model=List[DiseaseMatrixPoint])
def disease_activity_matrix(_: User = Depends(_require_admin), db: Session = Depends(get_db)):
    matrix = Counter()
    for client in db.query(Client).all():
        activity = (client.activity_level or "unknown").lower()
        for disease in _list_diseases(client):
            matrix[(disease, activity)] += 1

    return [
        DiseaseMatrixPoint(disease=disease, segment=segment, count=count)
        for (disease, segment), count in sorted(matrix.items())
    ]


@router.get("/analytics/disease-region", response_model=List[DiseaseMatrixPoint])
def disease_region_matrix(_: User = Depends(_require_admin), db: Session = Depends(get_db)):
    matrix = Counter()
    for client in db.query(Client).all():
        region = _infer_region_from_email(client.email)
        for disease in _list_diseases(client):
            matrix[(disease, region)] += 1

    return [
        DiseaseMatrixPoint(disease=disease, segment=segment, count=count)
        for (disease, segment), count in sorted(matrix.items())
    ]
