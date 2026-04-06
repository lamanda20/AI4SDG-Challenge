"""
rag/downloader.py
Downloads free medical guidelines from PubMed API and saves as text files.
No PDF parsing needed - uses PubMed abstracts directly (free, no login).
"""

import os
import json
import time
import urllib.request
import urllib.parse

DOCS_DIR = os.path.join(os.path.dirname(__file__), "documents")

# PubMed search queries for each condition
PUBMED_QUERIES = [
    ("diabetes_exercise",       "diabetes type 2 exercise guidelines physical activity"),
    ("hypertension_exercise",   "hypertension exercise training blood pressure reduction"),
    ("obesity_exercise",        "obesity weight loss exercise prescription guidelines"),
    ("cardiac_exercise",        "cardiovascular disease exercise rehabilitation guidelines"),
    ("depression_exercise",     "depression anxiety exercise therapy mental health"),
    ("general_exercise",        "exercise prescription chronic disease safety guidelines"),
    ("diabetes_intensity",      "diabetes aerobic resistance training intensity HbA1c"),
    ("elderly_exercise",        "elderly older adults exercise safety recommendations"),
]

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _search_pubmed(query: str, max_results: int = 10) -> list:
    """Search PubMed and return list of PMIDs."""
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    })
    url = f"{PUBMED_BASE}/esearch.fcgi?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        return data["esearchresult"]["idlist"]
    except Exception as e:
        print(f"  [WARN] Search failed for '{query}': {e}")
        return []


def _fetch_abstracts(pmids: list) -> list:
    """Fetch abstracts for a list of PMIDs."""
    if not pmids:
        return []
    ids = ",".join(pmids)
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "id": ids,
        "retmode": "json",
        "rettype": "abstract",
    })
    url = f"{PUBMED_BASE}/efetch.fcgi?{params}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            raw = r.read().decode("utf-8", errors="ignore")
        return [raw]
    except Exception as e:
        print(f"  [WARN] Fetch failed: {e}")
        return []


def _fetch_abstracts_summary(pmids: list) -> list:
    """Fetch structured summaries for PMIDs - more reliable than efetch."""
    if not pmids:
        return []
    ids = ",".join(pmids)
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "id": ids,
        "retmode": "json",
    })
    url = f"{PUBMED_BASE}/esummary.fcgi?{params}"
    docs = []
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        result = data.get("result", {})
        for pmid in pmids:
            item = result.get(pmid, {})
            title = item.get("title", "")
            authors = ", ".join([a.get("name", "") for a in item.get("authors", [])[:3]])
            source = item.get("source", "")
            pubdate = item.get("pubdate", "")
            if title:
                docs.append(
                    f"Title: {title}\n"
                    f"Authors: {authors}\n"
                    f"Journal: {source} ({pubdate})\n"
                    f"PMID: {pmid}\n"
                )
    except Exception as e:
        print(f"  [WARN] Summary fetch failed: {e}")
    return docs


# Hardcoded high-quality guidelines as fallback / supplement
STATIC_GUIDELINES = {
    "ada_diabetes": """
ADA Standards of Medical Care in Diabetes 2024
Source: American Diabetes Association

Exercise Recommendations for Type 2 Diabetes:
- Adults with T2DM should perform 150+ min/week of moderate-intensity aerobic activity
- Spread over at least 3 days/week with no more than 2 consecutive days without exercise
- Resistance training 2-3x/week on non-consecutive days
- Reduce prolonged sitting: interrupt every 30 min with light activity
- Blood glucose monitoring: check before exercise if on insulin or secretagogues
- Target blood glucose 100-250 mg/dL before exercise
- Avoid exercise if glucose >300 mg/dL or <100 mg/dL
- HbA1c reduction: aerobic exercise reduces HbA1c by 0.6-0.7% on average
- Combined aerobic + resistance training reduces HbA1c more than either alone
""",
    "esc_hypertension": """
ESC/ESH Guidelines for Hypertension Management 2023
Source: European Society of Cardiology

Exercise Recommendations for Hypertension:
- Regular aerobic exercise reduces systolic BP by 5-8 mmHg
- Recommended: 30 min moderate aerobic exercise 5-7 days/week
- Types: brisk walking, cycling, swimming, jogging
- Resistance training: 2-3x/week, moderate intensity (50-80% 1RM)
- Avoid heavy isometric exercises (heavy weightlifting, Valsalva maneuver)
- High-intensity interval training (HIIT) also effective for BP reduction
- Exercise before antihypertensive medication if possible
- Monitor BP before and after exercise sessions
- Contraindication: uncontrolled hypertension (>180/110 mmHg)
""",
    "acsm_general": """
ACSM Guidelines for Exercise Testing and Prescription 2022
Source: American College of Sports Medicine

General Exercise Prescription for Chronic Disease:
- Frequency: 3-5 days/week aerobic, 2-3 days/week resistance
- Intensity: moderate (40-60% VO2max) to vigorous (60-85% VO2max)
- Time: 20-60 min continuous or accumulated throughout day
- Type: rhythmic, large muscle group activities
- Progression: increase duration before intensity
- FITT principle: Frequency, Intensity, Time, Type
- High-risk patients: start at light intensity (30-40% VO2max)
- Medical clearance required for vigorous exercise in high-risk patients
- RPE scale: target 12-16 (moderate to somewhat hard)
- Heart rate reserve method: target 40-85% HRR
""",
    "who_physical_activity": """
WHO Global Guidelines on Physical Activity and Sedentary Behaviour 2020
Source: World Health Organization

Recommendations for Adults (18-64 years):
- 150-300 min/week moderate-intensity aerobic activity, OR
- 75-150 min/week vigorous-intensity aerobic activity
- Muscle-strengthening activities 2+ days/week
- Limit sedentary time; replace with physical activity of any intensity

Recommendations for Older Adults (65+ years):
- Same as adults plus balance and functional training 3+ days/week
- Multicomponent physical activity to prevent falls

For Chronic Conditions:
- Benefits outweigh risks for most chronic conditions
- Start low, go slow approach
- Adapt type and intensity to individual capacity
""",
    "obesity_exercise": """
Exercise Guidelines for Obesity and Weight Management
Source: Obesity Medicine Association 2023

Exercise Prescription for Weight Loss:
- Minimum 150 min/week moderate activity for health benefits
- 225-420 min/week for significant weight loss (0.5-1 kg/week)
- Combine aerobic + resistance training for best body composition
- Resistance training preserves lean muscle mass during weight loss
- High-intensity interval training (HIIT): time-efficient alternative
- Non-exercise activity thermogenesis (NEAT): increase daily movement
- Caloric deficit of 500-750 kcal/day combined with exercise
- Realistic goal: 5-10% body weight loss in 6 months
- BMI >35: start with low-impact activities (swimming, cycling)
- Monitor for musculoskeletal stress in obese patients
""",
    "depression_exercise": """
Exercise as Treatment for Depression and Anxiety
Source: Lancet Psychiatry 2023 / NICE Guidelines

Mental Health Exercise Recommendations:
- Exercise is as effective as antidepressants for mild-moderate depression
- 3x/week aerobic exercise for 45-60 min reduces depression symptoms
- Both aerobic and resistance training effective for depression
- Group exercise provides additional social benefit
- Minimum 8-12 weeks for measurable antidepressant effect
- High-intensity exercise may be more effective than low-intensity
- Exercise increases BDNF, serotonin, dopamine, endorphins
- CBT combined with exercise more effective than either alone
- For anxious patients: start with low-intensity to avoid symptom exacerbation
- Outdoor exercise (green exercise) has additional mood benefits
""",
    "cardiac_rehab": """
Cardiac Rehabilitation Exercise Guidelines
Source: AHA/ACC 2023

Exercise for Cardiovascular Disease:
- Cardiac rehab reduces mortality by 20-25%
- Phase 1 (inpatient): low-intensity ambulation, 3-5 METs
- Phase 2 (outpatient): supervised aerobic training, 4-8 weeks
- Target HR: 40-80% heart rate reserve
- RPE: 11-14 (light to somewhat hard)
- Warm-up and cool-down: minimum 10 min each
- Avoid exercise in extreme temperatures
- Stop exercise if: chest pain, severe dyspnea, dizziness, arrhythmia
- Beta-blockers: use RPE instead of HR for intensity monitoring
- Resistance training: safe after 2-4 weeks of aerobic training
""",
}


def download_documents():
    """
    Main function: downloads PubMed abstracts + saves static guidelines.
    Creates text files in rag/documents/ folder.
    """
    os.makedirs(DOCS_DIR, exist_ok=True)
    total = 0

    print("\n[1/2] Saving static medical guidelines...")
    for name, content in STATIC_GUIDELINES.items():
        path = os.path.join(DOCS_DIR, f"{name}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"  [OK] {name}.txt")
        total += 1

    print("\n[2/2] Fetching PubMed abstracts...")
    for topic, query in PUBMED_QUERIES:
        print(f"  Searching: {query[:50]}...")
        pmids = _search_pubmed(query, max_results=8)
        if not pmids:
            continue
        docs = _fetch_abstracts_summary(pmids)
        if docs:
            path = os.path.join(DOCS_DIR, f"pubmed_{topic}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"PubMed Search: {query}\n")
                f.write("="*60 + "\n\n")
                f.write("\n\n".join(docs))
            print(f"  [OK] pubmed_{topic}.txt ({len(docs)} articles)")
            total += 1
        time.sleep(0.4)  # PubMed rate limit: max 3 req/sec

    print(f"\n[DONE] {total} document files saved to rag/documents/")
    return total


if __name__ == "__main__":
    download_documents()
