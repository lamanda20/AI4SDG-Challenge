"""
vector_query.py
Builds a structured query string from engineered features for RAG retrieval.
"""

from typing import Dict, Any


def build_rag_query(features: Dict[str, Any], ml_output: Dict[str, Any]) -> str:
    """
    Compose a natural-language query for the vector DB.
    Combines patient profile + ML risk output for targeted guideline retrieval.
    """
    diseases = [c["condition_name"] for c in features.get("health_conditions", [])]
    risk_level = ml_output.get("risk_assessment", {}).get("risk_level", "moderate")
    intensity = ml_output.get("recommended_exercise_intensity", "moderate")
    bmi_cat = features.get("bmi_category", "normal")
    age = features.get("age", 40)
    goals = features.get("goals", [])
    injuries = features.get("injuries", [])

    parts = [
        f"Exercise prescription for {age}-year-old patient",
        f"with {', '.join(diseases) if diseases else 'no chronic conditions'}",
        f"BMI category: {bmi_cat}",
        f"risk level: {risk_level}",
        f"recommended intensity: {intensity}",
    ]

    if goals:
        parts.append(f"goals: {', '.join(goals)}")
    if injuries:
        parts.append(f"injuries/contraindications: {', '.join(injuries)}")

    warnings = ml_output.get("warnings", [])
    if warnings:
        parts.append(f"safety concerns: {'; '.join(warnings[:2])}")

    return ". ".join(parts) + "."
