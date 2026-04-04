# Integration Guide: ML Module for Other Teams

## 📌 For Zineb (API Orchestrator)

### What the ML Module expects:
```python
# Call the ML pipeline with a user profile dict
from backend.ml.pipeline import get_ml_pipeline

user_profile = {
    "user_id": "user_123",
    "age": 55,
    "bmi": 28.5,
    "vo2_max": 35.0,
    "hba1c": 7.2,
    "fasting_glucose": 120,
    "current_medications": ["Metformin"],
    "exercise_history_days": 5,
    "health_conditions": [
        {"condition_name": "diabetes", "severity": "moderate", "duration_years": 5}
    ],
    "current_biometrics": {
        "heart_rate": 72,
        "heart_rate_variability": 45,
        "daily_steps": 4200,
        "sleep_duration": 6.5,
        "blood_pressure_systolic": 135,
        "blood_pressure_diastolic": 85
    },
    "user_feedback_text": "Feeling motivated but tired"  # Optional
}

# Get pipeline instance
pipeline = get_ml_pipeline()

# Process user profile
ml_output = pipeline.process_user_profile(user_profile)

# Use the output downstream
print(ml_output)
```

### ML Module Output (what you'll get back):
```json
{
  "user_id": "user_123",
  "timestamp": "2026-04-04T12:57:28Z",
  "risk_assessment": {
    "risk_score": 62.0,
    "risk_level": "moderate",
    "progression_risk": 65.0,
    "adherence_risk": 40.0,
    "injury_risk": 35.0,
    "explanation": "Moderate risk due to suboptimal HbA1c..."
  },
  "sentiment_analysis": {
    "sentiment_score": 0.55,
    "sentiment_label": "positive",
    "motivation_level": "medium",
    "depression_risk_indicator": false,
    "cbt_intervention_needed": false,
    "confidence": 0.82
  },
  "recommended_exercise_intensity": "light",
  "intensity_rationale": "Light intensity recommended...",
  "warnings": [
    "Monitor blood pressure before exercise",
    "High non-adherence risk..."
  ],
  "metadata": {
    "model_version": "ml_v1.0",
    "cbt_strategy": "Behavioral Activation"
  }
}
```

### API Endpoint (if using FastAPI):
```bash
POST /api/ml/analyze
Content-Type: application/json

{
  "user_id": "user_123",
  ...
}

# Returns: MLModuleOutput (see above)
```

### What to do with ML output:
1. **Pass to RAG Engine** (Abd elghani): Send `risk_assessment`
2. **Pass to LLM Coach** (Soufia): Send `risk_assessment` + `recommended_exercise_intensity`
3. **Store in DB**: Save full `ml_output` for audit trail
4. **Monitor**: Track `warnings` for safety alerts

---

## 📌 For Abd elghani (RAG Medical Engine)

### What you'll receive from ML Module:

```python
risk_assessment = {
    "risk_score": 62.0,  # 0-100
    "risk_level": "moderate",  # low/moderate/high/critical
    "progression_risk": 65.0,  # % chance of worsening
    "adherence_risk": 40.0,  # % chance of non-adherence
    "injury_risk": 35.0,  # % chance of exercise injury
    "explanation": "Clinical explanation"
}
```

### How to use it:
```python
# 1. Use risk_level to select appropriate PubMed search queries
if risk_assessment["risk_level"] == "critical":
    queries = [
        "safe exercise for diabetic patients with high HbA1c",
        "cardiac screening before exercise prescription",
        "hypertension management with exercise"
    ]
elif risk_assessment["risk_level"] == "high":
    queries = [
        "moderate exercise for diabetes",
        "progressive conditioning for hypertension"
    ]

# 2. Use specific risk factors for targeted searches
if risk_assessment["injury_risk"] > 70:
    queries.append("injury prevention in patients with low VO2 max")

if risk_assessment["progression_risk"] > 75:
    queries.append("disease progression markers and exercise response")

# 3. Return guidelines back to pipeline for validation
return {
    "medical_guidelines": [...],  # From PubMed
    "approved_exercises": [...],
    "contraindications": [...],
    "monitoring_parameters": [...]
}
```

### What you SHOULD NOT do:
- ❌ Don't ignore the `risk_level` - it's there for a reason
- ❌ Don't suggest high-intensity exercises for "critical" risk patients
- ❌ Don't forget contraindications (check `warnings` from ML module)

### Contract between RAG & ML:
```
ML Module → RAG Module (INPUT)
├── risk_score (guides search specificity)
├── risk_level (guides severity of recommendations)
├── progression_risk (triggers disease-progression queries)
├── injury_risk (triggers injury-prevention queries)
└── warnings (provides context for contraindications)

RAG Module → LLM Coach (OUTPUT)
├── approved_exercises []
├── contraindications []
├── monitoring_parameters []
└── evidence_level (paper citations)
```

---

## 📌 For Soufia (LLM Coach - Prescriber)

### What you'll receive from ML Module:

```python
ml_output = {
    "risk_assessment": {...},
    "sentiment_analysis": {
        "sentiment_score": 0.55,  # -1 to 1
        "sentiment_label": "positive",  # positive/neutral/negative
        "motivation_level": "medium",  # low/medium/high
        "depression_risk_indicator": false,
        "cbt_intervention_needed": false
    },
    "recommended_exercise_intensity": "light",  # very_light/light/moderate/vigorous
    "intensity_rationale": "...",
    "warnings": [...],
    "metadata": {
        "cbt_strategy": "Behavioral Activation"
    }
}
```

### How to use it in your LLM prompts:

```python
system_prompt = f"""
You are a certified exercise coach for a patient with diabetes.

# Patient Risk Profile
- Risk Level: {risk_assessment['risk_level']}
- Risk Score: {risk_assessment['risk_score']}/100
- Injury Risk: {risk_assessment['injury_risk']}%
- Adherence Risk: {risk_assessment['adherence_risk']}%

# Patient Emotional State
- Sentiment: {sentiment_analysis['sentiment_label']} (confidence: {sentiment_analysis['confidence']})
- Motivation: {sentiment_analysis['motivation_level']}
- Depression Risk: {sentiment_analysis['depression_risk_indicator']}
- CBT Strategy to use: {metadata['cbt_strategy']}

# Exercise Constraints
- MAXIMUM Intensity: {recommended_exercise_intensity}
- Rationale: {intensity_rationale}
- MUST Monitor: {warnings}

# Your Task
Generate a specific, actionable exercise plan for today that:
1. Does NOT exceed recommended intensity
2. Incorporates CBT strategy if depression risk detected
3. Addresses all warnings
4. Uses motivational language matching patient mood
5. Returns JSON plan structure
"""
```

### Critical Rules for LLM Coach:
1. **NEVER** suggest intensity > `recommended_exercise_intensity`
2. **ALWAYS** include monitoring parameters from warnings
3. **IF** `depression_risk_indicator == True` → Use gentle, supportive language
4. **IF** `motivation_level == "low"` → Start with low-pressure activities
5. **IF** `cbt_intervention_needed == True` → Integrate CBT technique from metadata

### Expected Output Format:
```json
{
  "exercise_plan": {
    "date": "2026-04-04",
    "duration_minutes": 30,
    "intensity": "light",
    "exercises": [
      {
        "name": "Brisk walking",
        "duration": 5,
        "intensity": "light",
        "hr_target": "100-110 bpm",
        "rationale": "Warm-up, aligned with risk profile"
      }
    ],
    "monitoring": [
      "Blood pressure before and after",
      "Rate of perceived exertion (6/10 max)"
    ],
    "cbt_elements": [
      "Behavioral activation: Start with one manageable activity",
      "Progress tracking: Log completion for motivation"
    ],
    "safety_notes": "Stop if chest pain or dizziness. Monitor BP given hypertension."
  }
}
```

### Questions to ask yourself:
- Is this plan respecting the risk constraints? ✅
- Would a doctor approve this for this patient? ✅
- Does it address the emotional state? ✅
- Are all warnings incorporated? ✅

---

## 📋 KEY INTEGRATION POINTS

### Data Flow:
```
Zineb (API)
    ↓ [UserProfile dict]
ML Module (Taha) [YOU ARE HERE]
    ↓ [MLModuleOutput]
    ├→ RAG (Abd elghani)
    │   ├→ [risk_assessment] 
    │   └→ Returns [medical_guidelines]
    │
    ├→ LLM Coach (Soufia)
    │   ├→ [risk_assessment]
    │   ├→ [sentiment_analysis]
    │   ├→ [recommended_exercise_intensity]
    │   └→ Returns [exercise_plan JSON]
    │
    └→ Motivator (Feedback loop)
        ├→ [sentiment_analysis]
        └→ [cbt_interventions]
```

### Contract Validation:
```python
# At the start of Jour 2 integration
from backend.ml.contracts import UserProfile, MLModuleOutput

# Validate inputs
user_profile = UserProfile(**incoming_dict)  # Will raise if invalid

# Validate outputs
ml_output = MLModuleOutput(**pipeline_result)  # Will raise if invalid

# Use with confidence - contracts guarantee structure
```

### Error Handling:
```python
try:
    ml_output = pipeline.process_user_profile(user_profile)
except ValueError as e:
    # Validation error - invalid profile
    log.error(f"Invalid profile: {e}")
    return 400, {"error": str(e)}
except Exception as e:
    # Unexpected error
    log.error(f"ML Pipeline error: {e}")
    return 500, {"error": "Internal error"}
```

---

## 🧪 Testing Your Integration

### Test with provided examples:
```python
from backend.ml.contracts import EXAMPLE_INPUT, EXAMPLE_OUTPUT
from backend.ml.pipeline import MLPipeline

pipeline = MLPipeline()
result = pipeline.process_user_profile(EXAMPLE_INPUT)

# Compare with expected output
assert result["risk_assessment"]["risk_level"] in ["low", "moderate", "high", "critical"]
assert -1 <= result["sentiment_analysis"]["sentiment_score"] <= 1
```

### Test different risk profiles:
```python
# Test with low-risk profile
# Test with high-risk profile  
# Test with depression indicators
# Test with low motivation
```

---

## 📞 SUPPORT & QUESTIONS

**ML Module Maintainer**: Taha
**Module Location**: `backend/ml/`
**Quick Test**: `python backend/ml/pipeline.py`
**Full Test**: `python demo_ml_pipeline.py`

---

**Version**: 1.0 Hackathon Edition  
**Last Updated**: April 4, 2026  
**Status**: ✅ Ready for Integration

