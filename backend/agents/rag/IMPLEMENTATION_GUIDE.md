"""
Implementation Guide: Risk-Aware Medical Guidelines Pipeline
(For Abd Elghani - RAG Medical Engine Team Member)

This guide walks through the complete implementation of the RAG Medical Engine
following the scope: Receives: risk_assessment, Can use: risk_level for searches, Returns: medical_guidelines
"""

# =====================================================================

# PART 1: DATA FLOW & ARCHITECTURE

# =====================================================================

"""
INPUT FLOW:
ML Agent (Taha) → RiskAssessment
{
"user_id": "patient_123",
"risk_level": "high", # <-- CRITICAL: Used for search tuning
"risk_score": 0.78,
"risk_factors": ["sedentary", "obesity"],
"comorbidities": ["type2_diabetes"],
"age": 55,
"activity_level": "sedentary",
"contraindications": "recent_cardiac_event"
}

PROCESSING:
retriever.retrieve_by_risk_assessment(risk_assessment)
├─ Step 1: Adjust parameters based on risk_level
│ ├─ LOW: similarity_threshold=0.5 (lenient), intensity=light_to_vigorous
│ ├─ MODERATE: threshold=0.65, intensity=light_to_moderate
│ ├─ HIGH: threshold=0.75, intensity=light (stricter)
│ └─ CRITICAL: threshold=0.85, intensity=light (very strict)
│
├─ Step 2: Build risk-aware search queries
│ ├─ "high risk exercise protocol"
│ ├─ "obesity exercise high risk"
│ ├─ "type2_diabetes exercise safety"
│ └─ ... (8-10 total queries)
│
├─ Step 3: Retrieve base documents from vector store
│ └─ Use adjusted similarity_threshold to filter
│
├─ Step 4: Deduplicate and rank results
│ └─ Keep highest scoring versions of each protocol
│
└─ Step 5: Convert to MedicalGuideline objects
├─ Adjust frequency by risk (HIGH: 2-3x/week vs LOW: 5-7x/week)
├─ Adjust duration by risk (HIGH: 10-20 min vs LOW: 30-60 min)
├─ Set intensity from filter (HIGH: light vs LOW: moderate)
└─ Add risk-specific safety precautions

OUTPUT FLOW:
MedicalGuidelinesResponse
{
"status": "success",
"user_id": "patient_123",
"risk_level_applied": "high",
"medical_guidelines": [
{
"protocol_name": "Supervised Aerobic Walking",
"frequency": "2-3 times per week", <-- Adjusted for HIGH risk
"duration": "10-20 minutes", <-- Adjusted for HIGH risk
"intensity": "light", <-- Adjusted for HIGH risk
"safety_precautions": [...],
"monitoring_parameters": {...},
"risk_level_applied": "high"
},
...
],
"safety_summary": "Patient requires light-intensity programs with careful monitoring...",
"confidence_score": 0.87,
"retrieved_document_count": 5
}

↓
Coach Agent (Soufia) receives medical_guidelines
↓
Coach creates detailed coaching plan
"""

# =====================================================================

# PART 2: CODE STRUCTURE

# =====================================================================

"""
File Structure:
backend/
├── agents/
│ └── rag/
│ ├── schemas.py # ✅ Added: RiskAssessment, MedicalGuideline, MedicalGuidelinesResponse
│ ├── retriever.py # ✅ Added: retrieve_by_risk_assessment() method
│ ├── rag_pipeline.py # Already has: MedicalRAGPipeline class
│ ├── config.py # Already has: risk parameter defaults
│ └── **init**.py # ✅ Updated: Exports new schemas
│
├── api/
│ ├── medical_guidelines.py # ✅ Created: FastAPI endpoints
│ └── **init**.py
│
└── main.py # ✅ Created: Main FastAPI app

Key Implementation Points:

1. ✅ Schemas (backend/agents/rag/schemas.py):
   - RiskAssessment: Input contract
   - MedicalGuideline: Individual protocol
   - MedicalGuidelinesResponse: Output contract

2. ✅ Retriever Logic (backend/agents/rag/retriever.py):
   - retrieve_by_risk_assessment(): Main entry point
   - \_get_risk_parameters(): Maps risk_level → search parameters
   - \_build_risk_aware_queries(): Creates risk-adjusted searches
   - \_convert_documents_to_guidelines(): Transforms docs → protocols

3. ✅ API Endpoints (backend/api/medical_guidelines.py):
   - POST /api/rag/medical-guidelines: Main endpoint
   - GET /api/rag/health: Health check
   - POST /api/rag/reset: Pipeline reset (dev only)

4. ✅ Main App (backend/main.py):
   - FastAPI app setup
   - CORS configuration
   - Router integration
     """

# =====================================================================

# PART 3: EXAMPLE USAGE

# =====================================================================

"""
SCENARIO: Patient with HIGH risk assessment

Step 1: ML Agent (Taha) sends RiskAssessment

```
POST /api/rag/medical-guidelines
Content-Type: application/json

{
    "user_id": "patient_456",
    "risk_level": "high",
    "risk_score": 0.78,
    "risk_factors": ["sedentary", "deconditioned"],
    "comorbidities": ["type2_diabetes", "hypertension"],
    "age": 62,
    "activity_level": "sedentary",
    "contraindications": "no_chest_wall_compromise"
}
```

Step 2: RAG Medical Engine processes:
a) Identifies HIGH risk_level
b) Sets parameters:

- similarity_threshold: 0.75 (strict)
- intensity_filter: "light" (light only)
- evidence_filter: "rct_only" (randomized trials only)
  c) Builds 8 risk-aware queries:
- "high risk exercise protocol"
- "sedentary exercise high risk"
- "type2_diabetes exercise safety"
- "hypertension exercise light intensity"
- "elderly exercise program"
- "sedentary to active progression"
- "safe exercise no_chest_wall_compromise"
- "evidence based chronic disease exercise intervention"
  d) Retrieves documents matching all 8 queries
  e) Filters to top 5 most relevant (using stricter 0.75 threshold)
  f) Converts each to MedicalGuideline with:
- frequency: "2-3 times per week" (conservative)
- duration: "10-20 minutes" (short sessions)
- intensity: "light" (strict)
- safety_precautions: [multiple specific safety points]
- monitoring_parameters: [heart rate, symptoms, fatigue]

Step 3: Returns MedicalGuidelinesResponse

```
{
    "status": "success",
    "user_id": "patient_456",
    "risk_level_applied": "high",
    "medical_guidelines": [
        {
            "protocol_id": "doc_001",
            "protocol_name": "Supervised Aerobic Walking Program",
            "description": "Gentle walking program designed for sedentary adults with multiple comorbidities...",
            "frequency": "2-3 times per week",
            "duration": "10-20 minutes",
            "intensity": "light",
            "safety_precautions": [
                "Get medical clearance before starting",
                "Start with 5 minute warm-up",
                "Monitor heart rate - stay below 60% max HR",
                "Stop immediately if: chest pain, severe dyspnea, dizziness",
                "Check blood pressure before and after",
                "Keep physician informed"
            ],
            "monitoring_parameters": {
                "heart_rate": "target 50-60% of max HR",
                "symptoms": "watch for chest pain, shortness of breath",
                "fatigue": "rate perceived exertion 1-10",
                "blood_pressure": "monitor pre/post activity"
            },
            "evidence_level": "randomized_controlled_trial",
            "citations": ["PMID:12345678", "PMID:87654321"],
            "risk_level_applied": "high"
        },
        ... (more guidelines)
    ],
    "safety_summary": "Patient requires light-intensity programs with careful monitoring and frequent check-ins. AVOID: no_chest_wall_compromise. Note: Comorbidities present - type2_diabetes, hypertension. Close coordination with specialist care required.",
    "confidence_score": 0.87,
    "retrieved_document_count": 5
}
```

Step 4: Coach Agent (Soufia) receives response and creates
personalized coaching plan based on the medical guidelines

SCENARIO: Patient with LOW risk assessment

Same flow, but:

- similarity_threshold: 0.5 (lenient - more options)
- intensity_filter: "light_to_vigorous" (wider range)
- evidence_filter: "any" (all evidence levels accepted)
- frequency: "5-7 times per week"
- duration: "30-60 minutes"
- intensity: "moderate"

Result: More guidelines, more variety, less restrictive
"""

# =====================================================================

# PART 4: KEY IMPLEMENTATION DETAILS

# =====================================================================

"""
RISK-LEVEL MAPPING:

risk_level → Similarity Threshold → Intensity Filter → Evidence Level
─────────────────────────────────────────────────────────────────────
"low" → 0.50 (lenient) → light_to_vigorous → any
"moderate" → 0.65 (balanced) → light_to_moderate → cohort_or_better
"high" → 0.75 (strict) → light → rct_only
"critical" → 0.85 (very strict) → light → rct_or_meta_analysis

SIMILARITY THRESHOLD EFFECT:

- Lower (0.5): Returns more documents (more options for LOW risk)
- Higher (0.85): Returns only most relevant (safety for CRITICAL risk)
- Used in: vector_store.search()

INTENSITY FILTER:
Maps to MedicalGuideline.intensity field

- "light": Walking, stretching, tai chi, gentle aquatics
- "light_to_moderate": Adding light resistance, intervals
- "light_to_vigorous": Full range of intensities for healthy patients

EVIDENCE FILTER:
Used for document metadata filtering

- "any": Accept all studies
- "cohort_or_better": Exclude case reports, single case series
- "rct_only": Randomized controlled trials only (gold standard)
- "rct_or_meta_analysis": Best evidence available

FREQUENCY MAPPING (by risk_level):
low → "5-7 times per week"
moderate → "3-5 times per week"
high → "2-3 times per week" <-- Daily breaks for recovery
critical → "1-2 times per week" <-- Supervised sessions only

DURATION MAPPING (by risk_level):
low → "30-60 minutes" <-- Full sessions
moderate → "20-40 minutes"
high → "10-20 minutes" <-- Shorter, more frequent breaks
critical → "5-15 minutes" <-- Very short initial sessions
"""

# =====================================================================

# PART 5: TESTING THE IMPLEMENTATION

# =====================================================================

"""
QUICK TEST SCRIPT:

# Test 1: Import and verify schemas exist

from backend.agents.rag import RiskAssessment, MedicalGuideline, MedicalGuidelinesResponse

# Test 2: Create risk assessment

risk = RiskAssessment(
user_id="test_patient",
risk_level="high",
risk_score=0.75,
risk_factors=["sedentary"],
comorbidities=["diabetes"],
age=60
)

# Test 3: Get RAG pipeline and call retriever

from backend.agents.rag import get_rag_pipeline
pipeline = get_rag_pipeline()
guidelines, safety_summary = pipeline.retriever.retrieve_by_risk_assessment(risk)

# Test 4: Verify output

print(f"Retrieved {len(guidelines)} guidelines")
print(f"Risk level applied: {guidelines[0].risk_level_applied if guidelines else 'N/A'}")
print(f"Safety summary: {safety_summary}")

# Test 5: Test API endpoint

import requests
response = requests.post(
"http://localhost:8000/api/rag/medical-guidelines",
json={
"user_id": "patient_123",
"risk_level": "high",
"risk_score": 0.78,
"risk_factors": ["sedentary", "obesity"],
"comorbidities": ["type2_diabetes"],
}
)
print(response.json())
"""

# =====================================================================

# PART 6: INTEGRATION WITH COACH AGENT (SOUFIA)

# =====================================================================

"""
MODULE HANDOFF:

Abd Elghani (RAG Medical Engine)
Input: RiskAssessment from ML Agent
Output: List[MedicalGuideline]
Endpoint: /api/rag/medical-guidelines
↓
Response includes: - medical_guidelines: List of protocols - safety_summary: Overall safety text - confidence_score: How confident in recommendations
↓
Soufia (Coach Agent)
Input: MedicalGuidelinesResponse
Task: Create detailed coaching plan
Output: CoachingPlan with: - Daily exercises from medical_guidelines - Progression schedule - Behavioral coaching - Motivation messages - Check-in intervals

Example Coach integration:

```python
# In Soufia's coach agent code
from backend.agents.rag import MedicalGuidelinesResponse

async def create_coaching_plan(rag_response: MedicalGuidelinesResponse):
    # Extract safety summary
    safety_notes = rag_response.safety_summary

    # Select appropriate guidelines
    selected_protocols = select_protocols(
        rag_response.medical_guidelines,
        rag_response.risk_level_applied
    )

    # Create progression plan
    plan = build_coaching_plan(selected_protocols)

    return coaching_plan
```

"""

# =====================================================================

# PART 7: TROUBLESHOOTING

# =====================================================================

"""
ISSUE: Getting empty medical_guidelines list
CAUSE: Similarity threshold too strict, no documents retrieved
FIX:

1. Check that documents are loaded: pipeline.vector_store.get_document_count()
2. Lower similarity threshold for testing
3. Verify RAG pipeline initialized: get_rag_pipeline()

ISSUE: Guidelines have wrong intensity level
CAUSE: intensity_filter not being applied correctly
FIX:

1. Check \_get_risk_parameters() returns correct filter
2. Verify \_convert_documents_to_guidelines() applies mapping
3. Test with print statements

ISSUE: Ollama connection error
CAUSE: Ollama server not running
FIX:

1. Start Ollama: ollama serve
2. Verify with: curl http://localhost:11434/api/tags
3. Check config.ollama_base_url in config.py

ISSUE: API returns 503 Service Unavailable
CAUSE: RAG pipeline initialization failed
FIX:

1. Check logs: tail -f logs/rag.log
2. Test pipeline directly: python -c "from backend.agents.rag import get_rag_pipeline; get_rag_pipeline()"
3. Verify all dependencies installed: pip install -r requirements.txt
   """

# =====================================================================

# PART 8: PERFORMANCE CONSIDERATIONS

# =====================================================================

"""
LATENCY BREAKDOWN (typical HIGH risk query):

1. Risk parameter lookup: ~1ms
2. Query expansion (8 queries): ~5ms
3. Vector store search (8 parallel searches @ 20ms each): 160ms
4. Deduplication: ~10ms
5. Document->Guideline conversion: ~20ms
6. Safety summary generation: ~5ms
   ─────────────────────────────
   TOTAL EXPECTED: ~200ms (0.2 seconds)

OPTIMIZATION TIPS:

1. Batch similar queries with same risk_level
2. Cache frequently-accessed guidelines (e.g., diabetes + high risk)
3. Implement query timeout (60ms per vector search)
4. Use similarity_threshold appropriately (higher = faster)
5. Monitor retrieval_time_ms in response

SCALING APPROACH:

- Small: Single pipeline instance (current)
- Medium: Pipeline per worker process
- Large: Shared vector store service + distributed retrieval
  """

# =====================================================================

# PART 9: NEXT STEPS FOR ABD ELGHANI

# =====================================================================

"""
COMPLETED:
✅ 1. Created RiskAssessment schema
✅ 2. Created MedicalGuideline schema
✅ 3. Created MedicalGuidelinesResponse schema
✅ 4. Implemented retrieve_by_risk_assessment() method
✅ 5. Implemented risk parameter mapping
✅ 6. Implemented risk-aware query builder
✅ 7. Implemented document-to-guideline conversion
✅ 8. Created API endpoint /api/rag/medical-guidelines
✅ 9. Created main.py FastAPI app
✅ 10. Integrated with logger and error handling

TO DO (OPTIONAL ENHANCEMENTS):

- [ ] Add caching layer for frequently-accessed guidelines
- [ ] Implement progressive adaptation (adjust over time)
- [ ] Add contraindication validation
- [ ] Create detailed logging/metrics endpoint
- [ ] Implement A/B testing framework for guideline effectiveness
- [ ] Add feedback loop from Coach Agent (did guidelines work?)
- [ ] Create documentation API (explain why each guideline chosen)

TESTING CHECKLIST:

- [ ] Test with LOW risk assessment (should return many options)
- [ ] Test with HIGH risk (should be conservative)
- [ ] Test with CRITICAL risk (should be very restrictive)
- [ ] Test error cases (invalid risk_level, missing fields)
- [ ] Test API endpoint with curl/Postman
- [ ] Test integration point with Coach Agent
- [ ] Verify safety_summary is clinically appropriate
- [ ] Benchmark query latency

DEPLOYMENT CHECKLIST:

- [ ] Run: python -m pytest tests/ (all tests pass)
- [ ] Check logs for warnings
- [ ] Verify Ollama connectivity in target environment
- [ ] Test end-to-end: RiskAssessment → MedicalGuidelines → CoachingPlan
- [ ] Validate with clinical team
- [ ] Set appropriate timeouts for production
- [ ] Configure monitoring/alerting
      """
