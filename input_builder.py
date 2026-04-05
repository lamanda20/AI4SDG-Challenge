"""
INPUT BUILDER - Helper pour créer des inputs facilement
"""

import json

def create_minimal_input(user_id, age, bmi):
    """Créer un input minimaliste"""
    return {
        "user_id": user_id,
        "age": age,
        "bmi": bmi,
        "current_biometrics": {
            "heart_rate": 70,
            "heart_rate_variability": 50,
            "daily_steps": 5000,
            "sleep_duration": 7,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80
        },
        "health_conditions": []
    }


def create_diabetic_input(user_id, age, bmi, hba1c, severity="moderate"):
    """Créer un input pour un patient diabétique"""
    return {
        "user_id": user_id,
        "age": age,
        "bmi": bmi,
        "hba1c": hba1c,
        "fasting_glucose": 120,
        "current_medications": ["Metformin"],
        "exercise_history_days": 5,
        "health_conditions": [
            {
                "condition_name": "diabetes",
                "severity": severity,
                "duration_years": 5
            }
        ],
        "current_biometrics": {
            "heart_rate": 75,
            "heart_rate_variability": 45,
            "daily_steps": 4200,
            "sleep_duration": 6.5,
            "blood_pressure_systolic": 135,
            "blood_pressure_diastolic": 85
        },
        "user_feedback_text": "Feeling motivated"
    }


def create_athlete_input(user_id, age):
    """Créer un input pour un athlète sain"""
    return {
        "user_id": user_id,
        "age": age,
        "bmi": 22,
        "vo2_max": 55,
        "hba1c": 5.0,
        "fasting_glucose": 95,
        "current_medications": [],
        "exercise_history_days": 28,
        "health_conditions": [],
        "current_biometrics": {
            "heart_rate": 55,
            "heart_rate_variability": 90,
            "daily_steps": 15000,
            "sleep_duration": 8.5,
            "blood_pressure_systolic": 110,
            "blood_pressure_diastolic": 70
        },
        "user_feedback_text": "Feeling great!"
    }


def create_high_risk_input(user_id, age):
    """Créer un input pour un patient à haut risque"""
    return {
        "user_id": user_id,
        "age": age,
        "bmi": 32,
        "vo2_max": 20,
        "hba1c": 8.5,
        "fasting_glucose": 160,
        "current_medications": ["Metformin", "Lisinopril", "Atorvastatin"],
        "exercise_history_days": 2,
        "health_conditions": [
            {
                "condition_name": "diabetes",
                "severity": "severe",
                "duration_years": 15
            },
            {
                "condition_name": "hypertension",
                "severity": "moderate",
                "duration_years": 10
            }
        ],
        "current_biometrics": {
            "heart_rate": 92,
            "heart_rate_variability": 30,
            "daily_steps": 2500,
            "sleep_duration": 5.5,
            "blood_pressure_systolic": 150,
            "blood_pressure_diastolic": 95
        },
        "user_feedback_text": "Feeling hopeless and tired"
    }


# TEST
if __name__ == "__main__":
    print("\n" + "="*80)
    print("INPUT BUILDER - Examples")
    print("="*80)

    # Example 1: Minimal
    print("\n1️⃣  MINIMAL INPUT:")
    minimal = create_minimal_input("user_001", 50, 25)
    print(json.dumps(minimal, indent=2))

    # Example 2: Diabetic
    print("\n\n2️⃣  DIABETIC INPUT:")
    diabetic = create_diabetic_input("diabetic_001", 55, 28.5, 7.2)
    print(json.dumps(diabetic, indent=2))

    # Example 3: Athlete
    print("\n\n3️⃣  ATHLETE INPUT:")
    athlete = create_athlete_input("athlete_001", 28)
    print(json.dumps(athlete, indent=2))

    # Example 4: High Risk
    print("\n\n4️⃣  HIGH RISK INPUT:")
    high_risk = create_high_risk_input("high_risk_001", 70)
    print(json.dumps(high_risk, indent=2))

    print("\n" + "="*80)
    print("✅ USE THESE FUNCTIONS TO CREATE INPUTS!")
    print("="*80)

