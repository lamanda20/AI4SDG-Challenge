
import os
import json
from typing import Dict, Any, List

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


def _build_prompt(features: Dict, ml_output: Dict, guidelines: List[str]) -> str:
    risk = ml_output.get("risk_assessment", {})
    sentiment = ml_output.get("sentiment_analysis", {})
    warnings = ml_output.get("warnings", [])
    intensity = ml_output.get("recommended_exercise_intensity", "moderate")
    rationale = ml_output.get("intensity_rationale", "")
    cbt_strategy = ml_output.get("metadata", {}).get("cbt_strategy", "")

    guidelines_text = "\n".join(f"- {g}" for g in guidelines)
    warnings_text = "\n".join(f"- {w}" for w in warnings) if warnings else "None"

    return f"""You are a certified sports medicine physician and exercise physiologist.
Generate a safe, personalized 7-day training plan in strict JSON format.

## Patient Profile
- Age: {features.get('age')}, Gender: {features.get('gender')}, BMI: {features.get('bmi')} ({features.get('bmi_category')})
- Conditions: {[c['condition_name'] for c in features.get('health_conditions', [])]}
- Medications: {features.get('current_medications', [])}
- Injuries/Contraindications: {features.get('injuries', [])}
- Activity level: {features.get('activity_level')}
- Goals: {features.get('goals', [])}
- Target HR zone: {features.get('target_hr_zone')}

## ML Risk Assessment
- Risk score: {risk.get('risk_score')}/100 ({risk.get('risk_level')})
- Progression risk: {risk.get('progression_risk')}, Adherence risk: {risk.get('adherence_risk')}, Injury risk: {risk.get('injury_risk')}
- Recommended intensity: {intensity} — {rationale}

## Sentiment & Motivation
- Sentiment: {sentiment.get('sentiment_label')}, Motivation: {sentiment.get('motivation_level')}
- CBT strategy: {cbt_strategy}

## Safety Warnings
{warnings_text}

## Evidence-Based Guidelines
{guidelines_text}

## Output Format (strict JSON, no markdown, no explanation)
{{
  "weekly_plan": {{
    "monday":    {{"activity": "...", "duration_min": 0, "intensity": "...", "notes": "..."}},
    "tuesday":   {{"activity": "...", "duration_min": 0, "intensity": "...", "notes": "..."}},
    "wednesday": {{"activity": "...", "duration_min": 0, "intensity": "...", "notes": "..."}},
    "thursday":  {{"activity": "...", "duration_min": 0, "intensity": "...", "notes": "..."}},
    "friday":    {{"activity": "...", "duration_min": 0, "intensity": "...", "notes": "..."}},
    "saturday":  {{"activity": "...", "duration_min": 0, "intensity": "...", "notes": "..."}},
    "sunday":    {{"activity": "rest or active recovery", "duration_min": 0, "intensity": "rest", "notes": "..."}}
  }},
  "motivational_message": "..."
}}

Rules:
- Never prescribe vigorous exercise for high/critical risk without explicit medical clearance note
- Always include warm-up/cool-down in notes for cardiac patients
- Respect injuries as hard contraindications
- Keep language empathetic and non-judgmental
"""


def _fallback_plan(features: Dict, ml_output: Dict) -> Dict:
    """Rule-based plan when Groq is unavailable."""
    intensity = ml_output.get("recommended_exercise_intensity", "moderate")
    sentiment = ml_output.get("sentiment_analysis", {})

    intensity_map = {
        "very_light": {"activity": "Gentle walking",      "duration_min": 20},
        "light":      {"activity": "Brisk walking",        "duration_min": 30},
        "moderate":   {"activity": "Cycling or swimming",  "duration_min": 40},
        "vigorous":   {"activity": "Running or HIIT",      "duration_min": 45},
    }
    base = intensity_map.get(intensity, intensity_map["moderate"])
    day = {**base, "intensity": intensity, "notes": "Warm up 5 min, cool down 5 min."}
    rest = {"activity": "Rest or gentle stretching", "duration_min": 15, "intensity": "rest", "notes": "Active recovery"}

    msg_map = {
        "low":    "Every step counts. Start small, stay safe.",
        "medium": "You're doing well. Keep showing up.",
        "high":   "Great energy! Consistency is your superpower.",
    }
    return {
        "weekly_plan": {
            "monday": day, "tuesday": rest, "wednesday": day,
            "thursday": rest, "friday": day,
            "saturday": {**day, "notes": "Optional — listen to your body"},
            "sunday": rest,
        },
        "motivational_message": msg_map.get(sentiment.get("motivation_level", "medium"), "You've got this!"),
    }


def generate_plan(features: Dict[str, Any], ml_output: Dict[str, Any], guidelines: List[str]) -> Dict[str, Any]:
    """
    Generate the final training plan using Groq (free).
    Falls back to rule-based plan if GROQ_API_KEY is not set.
    """
    api_key = os.getenv("GROQ_API_KEY")

    if HAS_GROQ and api_key:
        try:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                messages=[{"role": "user", "content": _build_prompt(features, ml_output, guidelines)}],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[prescriber_llm] Groq call failed: {e}. Using fallback.")

    return _fallback_plan(features, ml_output)
