"""
api/profile.py
GET /profile/me     → profil client + dernier plan
GET /profile/plans  → historique complet des plans
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.crud import get_client_by_id, get_latest_plan, get_all_plans, get_checkin_count
from backend.schemas import UserProfileResponse, TrainingPlanResponse
from backend.api.auth import _verify_token

router = APIRouter(prefix="/profile", tags=["profile"])


def _get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    token   = authorization.replace("Bearer ", "").replace("bearer ", "")
    user_id = _verify_token(token)
    user    = get_client_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _plan_to_response(plan) -> TrainingPlanResponse:
    return TrainingPlanResponse(
        id=plan.id,
        week_number=plan.week_number,
        risk_level=plan.risk_level,
        sentiment_label=plan.sentiment_label,
        recommended_intensity=plan.recommended_intensity,
        weekly_plan=plan.weekly_plan,
        warnings=plan.warnings or [],
        motivational_message=plan.motivational_message or "",
        medical_guidelines=plan.medical_guidelines or [],
        created_at=plan.generated_at.isoformat(),
    )


@router.get("/me", response_model=UserProfileResponse)
def get_profile(user=Depends(_get_current_user), db: Session = Depends(get_db)):
    latest         = get_latest_plan(db, user.id)
    total_plans    = len(get_all_plans(db, user.id))
    total_checkins = get_checkin_count(db, user.id)

    return UserProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        age=user.age,
        gender=user.gender,
        weight_kg=user.weight_kg,
        height_cm=user.height_cm,
        diseases=user.diseases or [],
        activity_level=user.activity_level,
        latest_plan=_plan_to_response(latest) if latest else None,
        total_plans=total_plans,
        total_checkins=total_checkins,
    )


@router.get("/plans", response_model=list[TrainingPlanResponse])
def get_plan_history(user=Depends(_get_current_user), db: Session = Depends(get_db)):
    return [_plan_to_response(p) for p in get_all_plans(db, user.id)]
