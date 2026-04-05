"""
test_pipeline.py
Test chaque etape du pipeline une par une.
Usage: python test_pipeline.py
"""

import sys
import json
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def ok(msg):   print(f"  [OK]   {msg}")
def fail(msg): print(f"  [FAIL] {msg}")
def info(msg): print(f"  [>>]   {msg}")

RAW_FORM = {
    "user_id": "test_user_001",
    "age": 55,
    "gender": "male",
    "height_cm": 175,
    "weight_kg": 90,
    "diseases": ["diabetes", "hypertension"],
    "medications": ["Metformin", "Lisinopril"],
    "injuries": [],
    "activity_level": "sedentary",
    "exercise_days_per_month": 4,
    "goal_lose_weight": True,
    "goal_build_muscle": False,
    "goal_endurance": False,
    "mood": "tired but motivated",
    "motivation_text": "I want to get healthier",
    "current_heart_rate": 78,
    "daily_steps": 3500,
    "sleep_hours": 6.5,
    "blood_pressure_systolic": 140,
    "blood_pressure_diastolic": 88,
    "hba1c": 7.5,
    "fasting_glucose": 130,
    "vo2_max": 28.0,
}

results = {}

print("\n" + "="*60)
print("  SPORTRX AI - PIPELINE TEST")
print("="*60 + "\n")

# ── STEP 1 : Form Processor ────────────────────────────────────────────────────
print("[1/6] Form Processor")
try:
    from backend.services.form_processor import process_form
    form = process_form(RAW_FORM)
    ok(f"Form validated -> user_id={form.user_id}, age={form.age}, {form.weight_kg}kg/{form.height_cm}cm")
    results["form"] = form
except Exception as e:
    fail(f"form_processor: {e}")
    sys.exit(1)

# ── STEP 2 : Feature Engineering ──────────────────────────────────────────────
print("\n[2/6] Feature Engineering")
try:
    from backend.services.feature_engineering import compute_features
    features = compute_features(form)
    ok(f"BMI = {features['bmi']} ({features['bmi_category']})")
    ok(f"Max HR = {features['max_heart_rate']} bpm")
    ok(f"Target HR zone = {features['target_hr_zone']}")
    ok(f"Goals = {features['goals']}")
    results["features"] = features
except Exception as e:
    fail(f"feature_engineering: {e}")
    sys.exit(1)

# ── STEP 3 : ML Analysis ──────────────────────────────────────────────────────
print("\n[3/6] ML Analysis (Risk + Sentiment)")
try:
    from backend.agents.motivator_ml import run_ml_analysis
    ml_output = run_ml_analysis(features)
    if "error" in ml_output:
        fail(f"ML pipeline error: {ml_output['error']}")
        sys.exit(1)
    risk = ml_output["risk_assessment"]
    sentiment = ml_output["sentiment_analysis"]
    ok(f"Risk score = {risk['risk_score']:.1f}/100 -> level: {risk['risk_level']}")
    ok(f"Sentiment = {sentiment['sentiment_label']} | Motivation = {sentiment['motivation_level']}")
    ok(f"Recommended intensity = {ml_output['recommended_exercise_intensity']}")
    if ml_output.get("warnings"):
        info(f"Warnings: {ml_output['warnings'][0][:70]}")
    results["ml_output"] = ml_output
except Exception as e:
    fail(f"motivator_ml: {e}")
    sys.exit(1)

# ── STEP 4 : Vector Query ──────────────────────────────────────────────────────
print("\n[4/6] Vector Query Builder")
try:
    from backend.services.vector_query import build_rag_query
    rag_query = build_rag_query(features, ml_output)
    ok(f"RAG query built ({len(rag_query)} chars)")
    info(f"{rag_query[:100]}...")
    results["rag_query"] = rag_query
except Exception as e:
    fail(f"vector_query: {e}")
    sys.exit(1)

# ── STEP 5 : Clinician RAG ────────────────────────────────────────────────────
print("\n[5/6] Clinician RAG (Guidelines)")
try:
    from backend.agents.clinician_rag import retrieve_guidelines
    guidelines = retrieve_guidelines(rag_query)
    ok(f"{len(guidelines)} guideline(s) retrieved")
    for g in guidelines:
        info(f"{g[:80]}")
    results["guidelines"] = guidelines
except Exception as e:
    fail(f"clinician_rag: {e}")
    sys.exit(1)

# ── STEP 6 : Prescriber LLM ───────────────────────────────────────────────────
print("\n[6/6] Prescriber LLM (Training Plan)")
try:
    from backend.agents.prescriber_llm import generate_plan
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        info("GROQ_API_KEY not set -> using rule-based fallback plan")
    else:
        info("GROQ_API_KEY found -> calling Groq LLM")
    plan = generate_plan(features, ml_output, guidelines)
    ok(f"Plan generated with {len(plan['weekly_plan'])} days")
    ok(f"Message: {plan['motivational_message']}")
    for day, session in plan["weekly_plan"].items():
        info(f"{day.capitalize():10s} -> {session['activity']} ({session['duration_min']} min, {session['intensity']})")
    results["plan"] = plan
except Exception as e:
    fail(f"prescriber_llm: {e}")
    sys.exit(1)

# ── FINAL OUTPUT ───────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  FINAL OUTPUT JSON")
print("="*60)

final_output = {
    "user_id": form.user_id,
    "risk_level": ml_output["risk_assessment"]["risk_level"],
    "sentiment_label": ml_output["sentiment_analysis"]["sentiment_label"],
    "recommended_intensity": ml_output["recommended_exercise_intensity"],
    "weekly_plan": results["plan"]["weekly_plan"],
    "warnings": ml_output.get("warnings", []),
    "motivational_message": results["plan"]["motivational_message"],
    "medical_guidelines": guidelines,
}
print(json.dumps(final_output, indent=2))

print("\n" + "="*60)
print("  ALL 6 STEPS PASSING - PIPELINE READY")
print("="*60 + "\n")
