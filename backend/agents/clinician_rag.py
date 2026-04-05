"""
clinician_rag.py
Agent: retrieves evidence-based medical guidelines.
- If PINECONE_API_KEY is set -> queries real vector DB
- Otherwise -> uses hardcoded stub (for dev/testing)
"""

from typing import List


def retrieve_guidelines(query: str, top_k: int = 4) -> List[str]:
    """
    Main interface: returns relevant medical guidelines for a given query.
    Automatically uses Pinecone if configured, else falls back to stub.
    """
    # Try real Pinecone RAG first
    try:
        from rag.retriever import retrieve, is_available
        if is_available():
            results = retrieve(query, top_k=top_k)
            if results:
                return results
    except Exception as e:
        print(f"[clinician_rag] Pinecone unavailable: {e}. Using stub.")

    # Fallback: hardcoded guidelines
    return _stub_guidelines(query, top_k)


def _stub_guidelines(query: str, top_k: int) -> List[str]:
    """Hardcoded guidelines used when Pinecone is not configured."""
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
