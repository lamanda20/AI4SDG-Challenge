"""
feature_engineering.py
Computes derived features from validated form input.
"""

from typing import Dict, Any
from backend.schemas import UserFormInput  # noqa


def compute_features(form: UserFormInput) -> Dict[str, Any]:
    """
    Compute all derived features from form input.
    Returns a dict ready for ML pipeline + RAG query.
    """
    bmi = round(form.weight_kg / ((form.height_cm / 100) ** 2), 2)
    max_hr = 220 - form.age
    target_hr_low = round(max_hr * 0.60, 1)
    target_hr_high = round(max_hr * 0.70, 1)

    # BMI category
    if bmi < 18.5:
        bmi_category = "underweight"
    elif bmi < 25:
        bmi_category = "normal"
    elif bmi < 30:
        bmi_category = "overweight"
    else:
        bmi_category = "obese"

    # Goals list
    goals = []
    if form.goal_lose_weight:
        goals.append("weight_loss")
    if form.goal_build_muscle:
        goals.append("muscle_gain")
    if form.goal_endurance:
        goals.append("endurance")

    # Build health_conditions for ML pipeline contract
    health_conditions = [
        {"condition_name": d, "severity": "moderate", "duration_years": 1.0}
        for d in form.diseases
    ]

    # Biometrics dict (ML contract format)
    biometrics = {
        "heart_rate": form.current_heart_rate or 72.0,
        "heart_rate_variability": 45.0,
        "daily_steps": form.daily_steps or 5000,
        "sleep_duration": form.sleep_hours or 7.0,
        "blood_pressure_systolic": form.blood_pressure_systolic or 120.0,
        "blood_pressure_diastolic": form.blood_pressure_diastolic or 80.0,
    }

    # Combine user feedback text
    feedback_parts = [p for p in [form.mood, form.motivation_text] if p]
    user_feedback_text = " ".join(feedback_parts) if feedback_parts else None

    return {
        # Engineered features
        "bmi": bmi,
        "bmi_category": bmi_category,
        "max_heart_rate": max_hr,
        "target_hr_zone": {"low": target_hr_low, "high": target_hr_high},
        "goals": goals,
        # ML pipeline contract fields
        "user_id": form.user_id,
        "age": form.age,
        "vo2_max": form.vo2_max,
        "hba1c": form.hba1c,
        "fasting_glucose": form.fasting_glucose,
        "current_medications": form.medications,
        "exercise_history_days": form.exercise_days_per_month,
        "health_conditions": health_conditions,
        "current_biometrics": biometrics,
        "user_feedback_text": user_feedback_text,
        # Extra context for RAG
        "gender": form.gender.value,
        "activity_level": form.activity_level.value,
        "injuries": form.injuries,
    }
