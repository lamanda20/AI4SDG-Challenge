# ⚡ QUICK REFERENCE - LES INPUTS

## 🎯 EN UNE PHRASE
Tu passes **1 dict UserProfile** avec 4 champs obligatoires + 7 optionnels

---

## 🔴 LES 4 OBLIGATOIRES

```
user_id: string
age: int (18-120)
bmi: float (10-60)
current_biometrics: {
  heart_rate: float
  heart_rate_variability: float
  daily_steps: int
  sleep_duration: float
  blood_pressure_systolic: float
  blood_pressure_diastolic: float
}
```

---

## 🟢 LES 7 OPTIONNELS

```
vo2_max: float (null ok)
hba1c: float (null ok)
fasting_glucose: float (null ok)
current_medications: list ([] ok)
exercise_history_days: int (0 ok)
health_conditions: list ([] ok)
user_feedback_text: string (null ok)
```

---

## 💾 COPIER-COLLER EXEMPLE

```json
{
  "user_id": "user_001",
  "age": 55,
  "bmi": 28.5,
  "vo2_max": 35.0,
  "hba1c": 7.2,
  "fasting_glucose": 120,
  "current_medications": ["Metformin"],
  "exercise_history_days": 5,
  "health_conditions": [
    {
      "condition_name": "diabetes",
      "severity": "moderate",
      "duration_years": 5
    }
  ],
  "current_biometrics": {
    "heart_rate": 72,
    "heart_rate_variability": 45,
    "daily_steps": 4200,
    "sleep_duration": 6.5,
    "blood_pressure_systolic": 135,
    "blood_pressure_diastolic": 85
  },
  "user_feedback_text": "Feeling tired"
}
```

---

## 🎯 3 CAS SIMPLES

### Cas 1: MINIMAL
```json
{
  "user_id": "u1",
  "age": 50,
  "bmi": 25,
  "health_conditions": [],
  "current_biometrics": {
    "heart_rate": 70,
    "heart_rate_variability": 50,
    "daily_steps": 5000,
    "sleep_duration": 7,
    "blood_pressure_systolic": 120,
    "blood_pressure_diastolic": 80
  }
}
```

### Cas 2: DIABETIC
```json
{
  "user_id": "u2",
  "age": 60,
  "bmi": 30,
  "hba1c": 8.5,
  "fasting_glucose": 150,
  "health_conditions": [
    {"condition_name": "diabetes", "severity": "severe", "duration_years": 10}
  ],
  "current_biometrics": {
    "heart_rate": 85,
    "heart_rate_variability": 35,
    "daily_steps": 3000,
    "sleep_duration": 6,
    "blood_pressure_systolic": 145,
    "blood_pressure_diastolic": 90
  }
}
```

### Cas 3: ATHLETE
```json
{
  "user_id": "u3",
  "age": 25,
  "bmi": 22,
  "vo2_max": 55,
  "health_conditions": [],
  "current_biometrics": {
    "heart_rate": 55,
    "heart_rate_variability": 90,
    "daily_steps": 15000,
    "sleep_duration": 8,
    "blood_pressure_systolic": 110,
    "blood_pressure_diastolic": 70
  }
}
```

---

## 🚀 UTILISATION

```python
from ml.pipeline import get_ml_pipeline

pipeline = get_ml_pipeline()
output = pipeline.process_user_profile(user_profile)
```

**C'EST TOUT! 🎉**

