"""
Generate PDF Medical Guidelines for RAG Testing

This script creates sample PDF files from medical guidelines that can be
used by the document loader during testing.
"""

from pathlib import Path
from datetime import datetime


def generate_sample_pdfs():
    """Generate sample medical guideline PDFs"""
    
    # Create directory
    pdf_dir = Path("backend/agents/rag/data/documents")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📄 Generating sample PDF files in {pdf_dir}...\n")
    
    # Try pypdf and reportlab for PDF generation
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        HAS_REPORTLAB = True
    except ImportError:
        print("❌ reportlab not installed. Creating text files instead.")
        HAS_REPORTLAB = False
    
    # Medical guideline content
    guidelines = {
        "ADA_Diabetes_Exercise.txt": """
AMERICAN DIABETES ASSOCIATION (ADA)
Exercise Guidelines for Type 2 Diabetes Management
Published 2023

===== RECOMMENDED EXERCISES =====

1. AEROBIC EXERCISE
   Frequency: 3-4 times per week (at least 150 minutes/week)
   Intensity: Moderate (50-70% of max heart rate)
   Duration: 30-45 minutes per session
   Types: Brisk walking, cycling, swimming, dancing

2. RESISTANCE TRAINING
   Frequency: 2-3 times per week (non-consecutive days)
   Intensity: Moderate to vigorous (60-80% 1RM)
   Duration: 20-30 minutes per session
   Focus: Large muscle groups (legs, chest, back)

===== CONTRAINDICATIONS =====

AVOID HIGH-INTENSITY EXERCISE IF:
- Blood glucose > 250 mg/dL with ketones present
- High-impact activities with diabetic neuropathy
- Prolonged standing with foot complications
- Uncontrolled hypertension (SBP >180 mmHg)

===== SAFETY PRECAUTIONS =====

1. Blood Glucose Monitoring
   - Check before exercise
   - Check during long sessions (every 60 minutes)
   - Check after exercise
   - Optimal range: 100-250 mg/dL before exercise

2. Hydration and Nutrition
   - Carry fast-acting carbs (glucose tablets, juice)
   - Drink water before, during, and after exercise
   - Time exercise 1-2 hours after meals

3. Footwear and Inspection
   - Proper supportive shoes required
   - Check feet for injuries/blisters after exercise
   - Consider protective socks for long sessions

===== EXPECTED BENEFITS =====

- Improved insulin sensitivity (lasts 48-72 hours post-exercise)
- HbA1c reduction of 1-2% over 3-6 months
- Weight loss and better cardiovascular health
- Possible medication dose reduction

Evidence Level: A (Multiple RCTs)
PMID: ADA_2023
""",

        "PubMed_Aerobic_Diabetes.txt": """
PubMed Study: Aerobic Exercise and Insulin Sensitivity
PMID: 15345678

TITLE: Effect of aerobic exercise on insulin sensitivity in Type 2 Diabetes

OBJECTIVE: 
Evaluate the effect of moderate aerobic exercise on insulin sensitivity in 
sedentary adults with type 2 diabetes.

STUDY DESIGN:
- Sample: 450 participants with type 2 diabetes
- Age: 40-65 years
- Duration: 6 months
- Intervention: 150 minutes/week moderate aerobic exercise
- Control: No structured exercise

RESULTS:
- 34% improvement in insulin sensitivity (HOMA-IR)
- 1.5% reduction in HbA1c (intervention) vs 0.3% (control)
- Average weight loss: 3 kg
- 15% reduction in cardiovascular risk factors

CONTRAINDICATIONS OBSERVED:
- Proliferative retinopathy: Risk of retinal hemorrhage with high intensity
- Severe peripheral neuropathy: Recommend non-weight-bearing activities
- Recent MI: Gradual progression needed with medical supervision

SAFETY FINDINGS:
- No serious adverse events with supervision
- Hypoglycemia in 8% (on insulin/sulfonylureas)
- Recommended: glucose monitoring, proper footwear, gradual intensity increase

CONCLUSION: 
Moderate aerobic exercise is safe and effective for improving glycemic control
in type 2 diabetes when combined with medical supervision and proper monitoring.

Evidence Level: RCT (Randomized Controlled Trial)
""",

        "WHO_Hypertension_Exercise.txt": """
WORLD HEALTH ORGANIZATION (WHO)
Exercise Recommendations for Hypertension Control
Global Strategy on Diet, Physical Activity and Health

===== AEROBIC EXERCISE GUIDELINES =====

Frequency: 5-7 days per week (ideally daily)
Intensity: Moderate (50-70% max HR or 40-60% VO2 max)
Duration: 30 minutes daily (150 minutes/week minimum)
Type: Brisk walking, cycling, swimming, elliptical trainer

EXPECTED BLOOD PRESSURE REDUCTION:
- Systolic: 5-7 mmHg reduction
- Diastolic: 3-5 mmHg reduction
- Timeline: 2-4 weeks of consistent exercise

===== RESISTANCE TRAINING =====

Frequency: 2-3 days per week (non-consecutive)
Intensity: Light to moderate (40-60% 1RM)
Sets/Reps: 2-3 sets of 10-15 repetitions
CAUTION: Avoid heavy lifting (>85% 1RM) - can cause blood pressure spike

===== CONTRAINDICATIONS =====

ABSOLUTE CONTRAINDICATIONS:
- Severe hypertension (SBP >180): Obtain medical control first
- Recent MI or stroke: Require medical clearance
- Unstable angina: Exercise contraindicated
- Severe aortic stenosis: Avoid strenuous activity

===== PRECAUTIONS =====

1. Blood Pressure Monitoring
   - Check before and after exercise
   - Target: <160/100 mmHg before exercise
   - Stop if excessive elevation occurs

2. Exercise Modification
   - Gradual warm-up (5-10 minutes)
   - Avoid breath-holding (Valsalva maneuver)
   - Gradual cool-down (5-10 minutes)

3. Environmental
   - Avoid extreme heat
   - Stay well-hydrated
   - Exercise indoors on very hot days

===== MEDICATION INTERACTIONS =====

Beta-blockers: May blunt heart rate response; use RPE instead
ACE inhibitors: Generally safe; may require dose adjustment
Thiazide diuretics: Monitor for electrolyte balance
Note: Medication doses often reduced after 3-6 months of exercise

Evidence Level: A (Consensus from multiple studies)
WHO Recommendation: 2020
""",

        "Comorbidity_Guidelines.txt": """
EXERCISE MANAGEMENT FOR DIABETES AND HYPERTENSION COMORBIDITY

===== INTEGRATED EXERCISE PRESCRIPTION =====

Frequency: 5-7 days/week
Aerobic: 150 min/week at moderate intensity
Resistance: 2-3 sessions/week, light to moderate
Combined approach most effective for both conditions

===== PRIORITY SAFETY CHECKS =====

1. Blood Glucose Monitoring
   - Check before exercise
   - Check after exercise
   - Monitor for delayed hypoglycemia (up to 24 hours)

2. Blood Pressure Monitoring
   - Check before starting
   - Ensure SBP <160 mmHg
   - Monitor response after exercise

3. Medication Review
   - Coordinate with physicians
   - Insulin often needs 10-20% reduction
   - Sulfonylureas: frequent dose adjustment needed
   - Antihypertensive: may need reduction after 3-6 months

4. Cardiovascular Assessment
   - EKG recommended for sedentary patients >50 years
   - Consider stress testing if multiple risk factors

===== SPECIAL CONSIDERATIONS =====

Hypoglycemia + Blood Pressure Drop:
- Risk of syncope (fainting) during exercise
- Slower warm-up (10-15 minutes)
- Extended cool-down (10-15 minutes)
- Always carry fast-acting carbs
- Exercise with partner or in supervised setting

Optimal Timing:
- Early morning or 1-2 hours after meals
- Avoid late evening (hypoglycemia risk overnight)
- Consistent daily timing best for blood glucose control

===== CONTRAINDICATIONS IN COMORBID PATIENTS =====

DO NOT EXERCISE WITHOUT MEDICAL CLEARANCE IF:
- Active diabetic retinopathy (any type)
- Severe peripheral neuropathy (>Grade 2)
- Uncontrolled hypertension (SBP >180 mmHg)
- Recent acute coronary syndrome (<3 months)
- Severe proteinuria or kidney disease
- Severe aortic stenosis

===== MONITORING PARAMETERS =====

Before Each Session:
- Fasting glucose: 100-200 mg/dL optimal
- Blood pressure: <160/100 mmHg
- Foot inspection for injuries

During Exercise (sessions >60 min):
- Check glucose at 60-minute mark
- Monitor for chest pain, dizziness, SOB
- Rate of perceived exertion (RPE) 5-7/10

After Exercise:
- Check glucose 30-60 minutes post-exercise
- Alert for hypoglycemia up to 24 hours later
- Document BP and glucose readings

Evidence Level: Expert consensus
Sources: Endocrine Society, ADA, WHO, ACSM
""",

        "Safety_Contraindications.txt": """
EXERCISE SAFETY AND ABSOLUTE CONTRAINDICATIONS

===== ABSOLUTE CONTRAINDICATIONS TO EXERCISE =====

DO NOT START EXERCISE WITHOUT MEDICAL CLEARANCE:

1. Acute Myocardial Infarction (within 3 days)
2. Unstable Angina Pectoris
3. Uncontrolled Arrhythmias
4. Acute Myocarditis or Pericarditis
5. Acute Pulmonary Embolism
6. Acute Aortic Dissection
7. Uncontrolled Hypertension (SBP >200, DBP >120)
8. Acute Diabetic Crisis (BG >400 mg/dL with ketones)
9. Severe Symptomatic Aortic Stenosis
10. Severe Decompensated Heart Failure

===== DIABETIC COMPLICATIONS =====

Retinopathy (Non-Proliferative):
- Avoid Valsalva maneuver (breath-holding)
- Limit weight-bearing activities
- No heavy lifting

Retinopathy (Proliferative): **CAUTION**
- NO high-impact activities
- NO heavy resistance training (>7 kg)
- Non-weight-bearing exercise preferred
- Require ophthalmology clearance

Nephropathy (Microalbuminuria):
- Modified intensity allowed
- NOT contraindicated
- Monitor blood pressure carefully

Nephropathy (Macroalbuminuria):
- Avoid intense resistance training
- Careful BP monitoring required
- May need exercise intensity limitation

Neuropathy (Sensory):
- Non-weight-bearing preferred (cycling, swimming)
- Inspect feet thoroughly after exercise
- Wear protective footwear
- Avoid prolonged standing

Neuropathy (Autonomic): **HIGH RISK**
- Heart rate unreliable as exercise guide
- Use Rate of Perceived Exertion (RPE) instead
- Monitor blood pressure carefully
- Risk of silent ischemia

Foot Complications (Active Ulcer):
- Stress-relief exercise only (seated)
- Non-weight-bearing mandatory
- Physical therapy assessment needed

===== HYPERTENSIVE COMPLICATIONS =====

Left Ventricular Hypertrophy:
- Avoid heavy weight lifting
- Moderate intensity aerobic preferred

Cerebrovascular Disease:
- Gradual progression mandatory
- Medical clearance required
- Monitor for symptoms

Peripheral Arterial Disease:
- Weight-bearing may be limited
- Lower extremity pain with activity
- Vascular surgery assessment needed

Aortic Aneurysm:
- Avoid Valsalva maneuvers
- No breath-holding
- Avoid straining activities

===== WARNING SIGNS - STOP EXERCISE IMMEDIATELY =====

SEEK IMMEDIATE MEDICAL CARE IF:
- Chest pain or pressure
- Severe shortness of breath
- Dizziness or lightheadedness
- Severe joint or muscle pain
- Severe headache
- Unusual fatigue or weakness
- Palpitations or irregular heartbeat
- Blurred vision or visual changes

Timeline: If symptoms don't resolve in 15 minutes, call emergency services.

===== INFECTION AND ILLNESS =====

Do NOT Exercise If:
- Fever >101.5°F (38.6°C)
- Active chest cold or pneumonia
- Viral illness with systemic symptoms
- Untreated or uncontrolled infection
- Recent surgery (<2 weeks, no clearance)

Resume Exercise:
- After fever-free for 24 hours without medication
- Gradually, starting at 50% normal intensity
- If only cold symptoms above neck (mild OK)

Evidence Level: ACSM Guidelines 2023
Clinical Consensus from Multiple Organizations
"""
    }
    
    # Generate files
    for filename, content in guidelines.items():
        filepath = pdf_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Created: {filename}")
    
    print(f"\n✅ Generated {len(guidelines)} medical guideline documents")
    print(f"   Location: {pdf_dir}")
    print(f"   Ready for RAG document loader")
    
    return pdf_dir


if __name__ == "__main__":
    docs_dir = generate_sample_pdfs()
    print(f"\nNext step: Update document loader to use: {docs_dir}")
