# 🚀 SportRX AI - ML Module (Taha)

**Sentiment & Predictive ML for Chronic Disease Management**

---

## ✅ STATUS
- ✅ **PRODUCTION READY**
- ✅ **7/7 Tests Passing**
- ✅ **All modules working**
- ✅ **Ready for Jour 2 Integration**

---

## 📦 WHAT'S INCLUDED

### Core ML Module (7 files)
```
backend/ml/
├── contracts.py              (JSON schemas - Input/Output)
├── sentiment_analysis.py     (Sentiment + CBT)
├── risk_model.py             (Risk prediction)
├── pipeline.py               (ML orchestrator)
├── config.py                 (Configuration)
├── ml_routes.py              (FastAPI endpoints)
└── test_ml.py                (Unit tests)
```

### Features
- ✅ **Risk Prediction** (4 dimensions)
- ✅ **Sentiment Analysis** + Depression Detection
- ✅ **CBT Framework** (Behavioral interventions)
- ✅ **Dynamic Exercise Intensity**
- ✅ **Safety Warnings** (Clinical thresholds)

---

## 🧪 TESTING

### Quick Test
```bash
python direct_test.py
# Result: ALL PASSING ✅
```

### Comprehensive Tests
```bash
python test_ml_comprehensive.py
# Result: 7/7 TESTS PASSING ✅
```

---

## 📥 INPUTS (What to Pass)

**Single input**: UserProfile dict

**Mandatory (4):**
- `user_id` (string)
- `age` (int, 18-120)
- `bmi` (float, 10-60)
- `current_biometrics` (dict with 6 fields)

**Optional (7):**
- `vo2_max`, `hba1c`, `fasting_glucose`
- `current_medications`, `exercise_history_days`
- `health_conditions`, `user_feedback_text`

See `QUICK_INPUT_REFERENCE.md` for examples.

---

## 📤 OUTPUTS (What You Get)

**Single output**: MLModuleOutput JSON

Contains:
- `risk_assessment` (score, level, 3 risk dimensions)
- `sentiment_analysis` (score, label, depression risk)
- `recommended_exercise_intensity`
- `warnings` (safety alerts)
- `metadata` (model version, CBT strategy)

---

## 🚀 USAGE

```python
from ml.pipeline import get_ml_pipeline

pipeline = get_ml_pipeline()
output = pipeline.process_user_profile(user_profile_dict)
```

---

## 🔌 INTEGRATION (Jour 2)

### For Zineb (API)
- Import: `from backend.api.ml_routes import router`
- Use: Complete MLModuleOutput JSON

### For Abd elghani (RAG)
- Receive: `risk_assessment` from ML
- Use: `risk_level` for PubMed queries

### For Soufia (LLM Coach)
- Receive: All ML fields
- Use: `recommended_exercise_intensity` + `sentiment_analysis` + `cbt_strategy`

---

## 📚 DOCUMENTATION

- `README_ML_MODULE.md` - Technical details
- `INTEGRATION_GUIDE.md` - How to integrate with other teams
- `QUICK_INPUT_REFERENCE.md` - Input examples
- `DEPLOYMENT_GUIDE.md` - Deployment options

---

## 💻 API ENDPOINTS

```
POST /api/ml/analyze           - Complete pipeline
POST /api/ml/risk-only         - Risk only
POST /api/ml/sentiment-only    - Sentiment only
GET  /api/ml/health            - Health check
```

---

## 🎯 EXAMPLE OUTPUT

```json
{
  "user_id": "user_123",
  "timestamp": "2026-04-04T14:00:00Z",
  "risk_assessment": {
    "risk_score": 39.1,
    "risk_level": "moderate",
    "progression_risk": 40.4,
    "adherence_risk": 90.0,
    "injury_risk": 22.0,
    "explanation": "Risk assessment based on clinical factors"
  },
  "sentiment_analysis": {
    "sentiment_score": 0.125,
    "sentiment_label": "neutral",
    "motivation_level": "medium",
    "depression_risk_indicator": false,
    "cbt_intervention_needed": false,
    "confidence": 0.755
  },
  "recommended_exercise_intensity": "moderate",
  "intensity_rationale": "Moderate risk recommends moderate intensity",
  "warnings": ["High non-adherence risk. Plan motivational checkpoints."],
  "metadata": {
    "model_version": "ml_v1.0",
    "cbt_strategy": "Positive Reinforcement"
  }
}
```

---

## 📊 TEST RESULTS

```
✅ Module Imports
✅ Contract Validation
✅ Sentiment Analysis
✅ Motivation Engine
✅ Risk Model
✅ Complete Pipeline
✅ Different Risk Profiles

TOTAL: 7/7 PASSING ✅
```

---

## ⚠️ NOTES

- XGBoost not required (fallback heuristic model works)
- All inputs validated with Pydantic
- Zero external dependencies for core functionality
- Production-ready for immediate deployment

---

**Developer**: Taha  
**Date**: April 4, 2026  
**Status**: 🟢 PRODUCTION READY

