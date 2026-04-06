"""
Medical Prompts Library

Centralized management of LLM prompts for the RAG pipeline.
Ensures consistency and easy maintenance of prompt engineering.
"""

SYSTEM_PROMPT_MEDICAL_ADVISOR = """You are a medical research expert specializing in exercise science and chronic disease management.
Your role is to analyze medical evidence and generate safe, evidence-based exercise recommendations.

CRITICAL RULES:
1. Only recommend exercises that are explicitly supported by the retrieved medical documents
2. Always include evidence levels and citations
3. Flag any potential safety concerns or contraindications
4. Be conservative with medical advice - if uncertain, defer to medical professionals
5. Output must be valid JSON

You have access to curated medical literature on exercise protocols for chronic diseases.
Use this to inform your recommendations while maintaining medical accuracy and safety."""

EXTRACTION_PROMPT_PROTOCOL = """Given the following medical documents, extract exercise protocols that would be appropriate for a {condition} patient.

Patient Profile:
- Age: {age}
- Condition: {condition}
- Comorbidities: {comorbidities}
- Current Activity Level: {activity_level}
- Contraindications: {contraindications}

Medical Documents:
{documents}

Please extract and structure exercise protocols in the following JSON format:
{{
  "protocols": [
    {{
      "protocol_name": "...",
      "description": "...",
      "frequency": "... times per week",
      "duration": "... minutes",
      "intensity": "light/moderate/vigorous",
      "exercises": ["exercise 1", "exercise 2", ...],
      "contraindications": [...],
      "safety_warnings": [...],
      "evidence_level": "randomized_controlled_trial/cohort_study/observational",
      "citations": ["PMID:xxx", "PMID:yyy"]
    }}
  ],
  "safety_considerations": "...",
  "contraindicated_exercises": [...],
  "confidence_score": 0.0-1.0
}}

Ensure the output is valid JSON that can be parsed."""

VALIDATION_PROMPT_SAFETY = """You are a medical safety reviewer. Given an exercise protocol recommendation, 
validate its safety for a patient with the following characteristics:

Patient:
- Age: {age}
- Primary Condition: {condition}
- Comorbidities: {comorbidities}
- Current Medications: {medications}
- Recent Vitals: {vitals}

Proposed Protocol:
{protocol}

Review and respond with:
1. Safety Assessment (Safe/Caution/Contraindicated)
2. Any additional warnings or modifications needed
3. Recommended monitoring parameters

Respond in JSON format:
{{
  "is_safe": true/false,
  "safety_level": "safe/caution/contraindicated",
  "warnings": [...],
  "modifications": [...],
  "monitoring_parameters": {...],
  "rationale": "..."
}}"""

RETRIEVAL_QUERY_EXPANSION = """Given a medical query, expand it to create multiple search queries for vector database retrieval.

Original Query:
Condition: {condition}
Context: {context}

Generate 5 alternative search queries that would help retrieve relevant medical literature:
Return as JSON:
{{
  "original_query": "...",
  "expanded_queries": [
    "query 1",
    "query 2",
    ...
  ]
}}"""

# Condition-specific prompts
CONDITION_SPECIFIC_PROMPTS = {
    "diabetes": {
        "system": "You are an expert in diabetes exercise science, specializing in type 2 diabetes management.",
        "query_hint": "Focus on aerobic exercise, resistance training, and metabolic effects on blood glucose.",
    },
    "hypertension": {
        "system": "You are an expert in exercise physiology for cardiovascular health and blood pressure management.",
        "query_hint": "Focus on aerobic exercise intensity, duration, and effects on vascular function.",
    },
    "cancer": {
        "system": "You are an expert in cancer rehabilitation and exercise oncology.",
        "query_hint": "Focus on post-treatment recovery, fatigue management, and safe exercise progression.",
    },
    "mental_health": {
        "system": "You are an expert in exercise psychology and mental health rehabilitation.",
        "query_hint": "Focus on mood improvement, anxiety reduction, and psychological benefits of exercise.",
    },
}


def get_system_prompt(condition: str = None) -> str:
    """Get system prompt, optionally condition-specific"""
    if condition and condition.lower() in CONDITION_SPECIFIC_PROMPTS:
        return CONDITION_SPECIFIC_PROMPTS[condition.lower()]["system"]
    return SYSTEM_PROMPT_MEDICAL_ADVISOR


def get_query_hint(condition: str = None) -> str:
    """Get search hint for condition"""
    if condition and condition.lower() in CONDITION_SPECIFIC_PROMPTS:
        return CONDITION_SPECIFIC_PROMPTS[condition.lower()]["query_hint"]
    return "Focus on evidence-based exercise protocols."


def format_extraction_prompt(condition: str, age: int, comorbidities: str, activity_level: str, contraindications: str, documents: str) -> str:
    """Format the protocol extraction prompt with patient data"""
    return EXTRACTION_PROMPT_PROTOCOL.format(
        condition=condition,
        age=age,
        comorbidities=comorbidities or "None",
        activity_level=activity_level,
        contraindications=contraindications or "None",
        documents=documents,
    )


def format_safety_prompt(age: int, condition: str, comorbidities: str, medications: str, vitals: str, protocol: str) -> str:
    """Format the safety validation prompt"""
    return VALIDATION_PROMPT_SAFETY.format(
        age=age,
        condition=condition,
        comorbidities=comorbidities or "None",
        medications=medications or "None",
        vitals=vitals or "Not provided",
        protocol=protocol,
    )
