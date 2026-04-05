"""
clinician_rag.py
Agent: retrieves evidence-based medical guidelines from vector DB.
Stub implementation - replace _query_vector_db() with your actual vector store client.
"""

from typing import List


def _query_vector_db(query: str, top_k: int = 3) -> List[str]:
    """
    Stub: returns hardcoded guidelines keyed on keywords in the query.
    In production: embed query -> similarity search -> return top_k chunks.
    """
    guidelines = []
    q = query.lower()

    if "diabetes" in q:
        guidelines.append(
            "ADA 2024: Adults with T2DM should accumulate 150+ min/week moderate-intensity "
            "aerobic activity. Monitor blood glucose before/after exercise."
        )
    if "hypertension" in q:
        guidelines.append(
            "ESC 2023: Hypertensive patients benefit from 30 min moderate aerobic exercise "
            "5 days/week. Avoid Valsalva maneuver during resistance training."
        )
    if "obese" in q or "weight_loss" in q:
        guidelines.append(
            "WHO 2022: For weight management, 300 min/week moderate aerobic activity "
            "combined with resistance training 2x/week is recommended."
        )
    if "high" in q and "risk" in q:
        guidelines.append(
            "ACSM 2023: High-risk patients require medical clearance before vigorous exercise. "
            "Start with light intensity and progress gradually over 4-6 weeks."
        )
    if "muscle_gain" in q:
        guidelines.append(
            "NSCA 2022: Resistance training 2-3x/week targeting major muscle groups. "
            "8-12 reps at 60-80% 1RM for hypertrophy."
        )
    if "endurance" in q:
        guidelines.append(
            "ACSM 2023: Endurance training should follow progressive overload principle. "
            "Increase weekly volume by no more than 10% per week."
        )

    if not guidelines:
        guidelines.append(
            "ACSM General: Adults should perform 150-300 min/week moderate aerobic activity "
            "plus muscle-strengthening activities 2+ days/week."
        )

    return guidelines[:top_k]


def retrieve_guidelines(query: str) -> List[str]:
    """
    Public interface: given a RAG query string, return relevant medical guidelines.
    """
    return _query_vector_db(query)
