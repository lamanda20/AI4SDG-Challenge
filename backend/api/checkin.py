"""
api/checkin.py
POST /checkin  → bilan bi-mensuel → LLM régénère un nouveau plan

Logique:
- Client rapporte: sessions faites, énergie, douleur, poids, humeur
- Système fusionne les nouvelles biométriques avec le profil existant
- Re-run pipeline complet → nouveau plan pour les 2 prochaines semaines
- week_number += 2 à chaque checkin
"""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import CheckinRequest, CheckinResponse, UserFormInput
from backend.crud import save_plan, save_checkin, get_checkin_count, update_biometrics
from backend.api.profile import _get_current_user, _plan_to_response
from backend.services.feature_engineering import compute_features
from backend.agents.motivator_ml import run_ml_analysis
from backend.services.vector_query import build_rag_query
from backend.agents.clinician_rag import retrieve_guidelines
from backend.agents.prescriber_llm import generate_plan

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("", response_model=CheckinResponse)
def submit_checkin(
    data: CheckinRequest,
    user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    bio = user.biometrics  # 1-to-1 relationship

    # Merge checkin biometrics with stored values
    form_dict = {
        "user_id":                str(user.id),
        "age":                    user.age,
        "gender":                 user.gender,
        "height_cm":              user.height_cm,
        "weight_kg":              data.weight_kg or user.weight_kg,
        "diseases":               user.diseases or [],
        "medications":            user.medications or [],
        "injuries":               user.injuries or [],
        "activity_level":         user.activity_level,
        "exercise_days_per_month": data.sessions_completed,
        "goal_lose_weight":       user.goal_lose_weight,
        "goal_build_muscle":      user.goal_build_muscle,
        "goal_endurance":         user.goal_endurance,
        "current_heart_rate":     data.current_heart_rate  or (bio.heart_rate if bio else None),
        "daily_steps":            data.daily_steps         or (bio.daily_steps if bio else None),
        "sleep_hours":            data.sleep_hours         or (bio.sleep_hours if bio else None),
        "blood_pressure_systolic":  data.blood_pressure_systolic  or (bio.blood_pressure_systolic if bio else None),
        "blood_pressure_diastolic": data.blood_pressure_diastolic or (bio.blood_pressure_diastolic if bio else None),
        "hba1c":          bio.hba1c if bio else None,
        "fasting_glucose": bio.fasting_glucose if bio else None,
        "vo2_max":         bio.vo2_max if bio else None,
        "mood":            data.mood_text,
        "motivation_text": data.feedback_text,
    }

    # Persist updated biometrics
    update_biometrics(db, user.id, {
        "heart_rate":               data.current_heart_rate,
        "daily_steps":              data.daily_steps,
        "sleep_hours":              data.sleep_hours,
        "blood_pressure_systolic":  data.blood_pressure_systolic,
        "blood_pressure_diastolic": data.blood_pressure_diastolic,
        "weight_kg":                data.weight_kg,
        "mood_score":               data.avg_energy_level,
        "recent_feedback":          data.feedback_text,
    })
    if data.weight_kg:
        user.weight_kg = data.weight_kg
        db.commit()

    # Re-run full AI pipeline
    form_obj   = UserFormInput(**form_dict)
    features   = compute_features(form_obj)

    # Enrich feedback with energy signal for sentiment analysis
    energy_note = ""
    if data.avg_energy_level <= 3:
        energy_note = f"Very low energy ({data.avg_energy_level}/10). "
    elif data.avg_energy_level >= 8:
        energy_note = f"High energy ({data.avg_energy_level}/10). "
    if energy_note:
        features["user_feedback_text"] = energy_note + (data.mood_text or "")

    ml_output  = run_ml_analysis(features)
    rag_query  = build_rag_query(features, ml_output)
    guidelines = retrieve_guidelines(rag_query)
    plan_data  = generate_plan(features, ml_output, guidelines)

    checkin_count = get_checkin_count(db, user.id)
    week_number   = 1 + ((checkin_count + 1) * 2)   # 3, 5, 7 …

    new_plan = save_plan(db, user.id, {
        "risk_level":            ml_output["risk_assessment"]["risk_level"],
        "sentiment_label":       ml_output["sentiment_analysis"]["sentiment_label"],
        "recommended_intensity": ml_output["recommended_exercise_intensity"],
        "weekly_plan":           plan_data["weekly_plan"],
        "warnings":              ml_output.get("warnings", []),
        "motivational_message":  plan_data.get("motivational_message", ""),
        "medical_guidelines":    guidelines,
    }, week_number=week_number)

    save_checkin(db, user.id, data.model_dump(), new_plan_id=new_plan.id)

    adherence = round((data.sessions_completed / 14) * 100)
    summary = (
        f"Adherence: {adherence}% ({data.sessions_completed}/14 sessions). "
        f"Energy: {data.avg_energy_level}/10. Pain: {data.avg_pain_level}/10. "
        f"New risk level: {ml_output['risk_assessment']['risk_level']}."
    )

    return CheckinResponse(
        checkin_id=new_plan.id,
        week_number=week_number,
        new_plan=_plan_to_response(new_plan),
        progress_summary=summary,
    )
