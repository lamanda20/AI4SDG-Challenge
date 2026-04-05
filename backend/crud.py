from sqlalchemy.orm import Session
from models import Client, Admin, Biometrics, TrainingPlan, Checkin


# ── User / Client ──────────────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str):
    from models import User
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    from models import User
    return db.query(User).filter(User.id == user_id).first()


def create_admin(db: Session, name: str, email: str, hashed_password: str) -> Admin:
    admin = Admin(
        name=name,
        email=email,
        hashed_password=hashed_password,
        role="admin",
        can_manage_users=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def get_client_by_id(db: Session, user_id: int):
    return db.query(Client).filter(Client.id == user_id).first()


def create_client(db: Session, name: str, email: str, hashed_password: str, form: dict) -> Client:
    """Create Client row + Biometrics row in one transaction."""
    client = Client(
        name=name,
        email=email,
        hashed_password=hashed_password,
        role="client",
        # demographics
        age=form.get("age"),
        gender=form.get("gender"),
        height_cm=form.get("height_cm"),
        weight_kg=form.get("weight_kg"),
        chronic_condition=", ".join(form.get("diseases", [])) or None,
        diseases=form.get("diseases", []),
        medications=form.get("medications", []),
        injuries=form.get("injuries", []),
        activity_level=form.get("activity_level", "sedentary"),
        exercise_days_per_month=form.get("exercise_days_per_month", 0),
        goal_lose_weight=form.get("goal_lose_weight", False),
        goal_build_muscle=form.get("goal_build_muscle", False),
        goal_endurance=form.get("goal_endurance", False),
    )
    db.add(client)
    db.flush()   # get client.id before biometrics insert

    bio = Biometrics(
        user_id=client.id,
        hba1c=form.get("hba1c"),
        bmi=round(form["weight_kg"] / ((form["height_cm"] / 100) ** 2), 2),
        blood_pressure=_bp_string(form.get("blood_pressure_systolic"), form.get("blood_pressure_diastolic")),
        blood_pressure_systolic=form.get("blood_pressure_systolic"),
        blood_pressure_diastolic=form.get("blood_pressure_diastolic"),
        hrv=None,
        daily_steps=form.get("daily_steps"),
        vo2_max=form.get("vo2_max"),
        mood_score=None,
        recent_feedback=form.get("motivation_text"),
        heart_rate=form.get("current_heart_rate"),
        sleep_hours=form.get("sleep_hours"),
        fasting_glucose=form.get("fasting_glucose"),
    )
    db.add(bio)
    db.commit()
    db.refresh(client)
    return client


def update_biometrics(db: Session, user_id: int, updates: dict):
    bio = db.query(Biometrics).filter(Biometrics.user_id == user_id).first()
    if not bio:
        return
    for key, val in updates.items():
        if val is not None and hasattr(bio, key):
            setattr(bio, key, val)
    # Recompute blood_pressure string if both values present
    if updates.get("blood_pressure_systolic") or updates.get("blood_pressure_diastolic"):
        bio.blood_pressure = _bp_string(bio.blood_pressure_systolic, bio.blood_pressure_diastolic)
    db.commit()


# ── Training Plan ──────────────────────────────────────────────────────────────

def save_plan(db: Session, user_id: int, plan_data: dict, week_number: int = 1) -> TrainingPlan:
    plan = TrainingPlan(
        user_id=user_id,
        week_number=week_number,
        risk_level=plan_data.get("risk_level"),
        sentiment_label=plan_data.get("sentiment_label"),
        recommended_intensity=plan_data.get("recommended_intensity"),
        weekly_plan=plan_data.get("weekly_plan"),
        warnings=plan_data.get("warnings", []),
        motivational_message=plan_data.get("motivational_message"),
        medical_guidelines=plan_data.get("medical_guidelines", []),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_latest_plan(db: Session, user_id: int):
    return (
        db.query(TrainingPlan)
        .filter(TrainingPlan.user_id == user_id)
        .order_by(TrainingPlan.generated_at.desc())
        .first()
    )


def get_all_plans(db: Session, user_id: int):
    return (
        db.query(TrainingPlan)
        .filter(TrainingPlan.user_id == user_id)
        .order_by(TrainingPlan.generated_at.desc())
        .all()
    )


# ── Checkin ────────────────────────────────────────────────────────────────────

def save_checkin(db: Session, user_id: int, data: dict, new_plan_id: int = None) -> Checkin:
    checkin = Checkin(
        user_id=user_id,
        new_plan_id=new_plan_id,
        sessions_completed=data.get("sessions_completed", 0),
        avg_energy_level=data.get("avg_energy_level", 5),
        avg_pain_level=data.get("avg_pain_level", 0),
        weight_kg=data.get("weight_kg"),
        mood_text=data.get("mood_text"),
        feedback_text=data.get("feedback_text"),
        heart_rate=data.get("current_heart_rate"),
        blood_pressure_systolic=data.get("blood_pressure_systolic"),
        blood_pressure_diastolic=data.get("blood_pressure_diastolic"),
        sleep_hours=data.get("sleep_hours"),
        daily_steps=data.get("daily_steps"),
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


def get_checkin_count(db: Session, user_id: int) -> int:
    return db.query(Checkin).filter(Checkin.user_id == user_id).count()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _bp_string(systolic, diastolic) -> str | None:
    if systolic and diastolic:
        return f"{int(systolic)}/{int(diastolic)}"
    return None