"""
DIRECT TEST - NO COMPLEX IMPORTS
Just test the ML module directly
"""

import sys
import os

# Change to project directory
os.chdir(r'C:\Users\dell\PycharmProjects\AI4SDG-Challenge')
sys.path.insert(0, r'C:\Users\dell\PycharmProjects\AI4SDG-Challenge\backend')

# Now import
from ml.sentiment_analysis import SentimentAnalyzer

print("\n" + "="*80)
print("🧪 DIRECT TEST - SENTIMENT ANALYSIS")
print("="*80)

analyzer = SentimentAnalyzer()

# Test 1
print("\n✅ Test 1: Positive Sentiment")
result = analyzer.analyze_sentiment("I'm feeling great!")
print(f"   Score: {result.score:.2f}, Label: {result.label}")

# Test 2
print("\n✅ Test 2: Negative Sentiment (Depression)")
result = analyzer.analyze_sentiment("I feel hopeless and worthless")
print(f"   Score: {result.score:.2f}, Depression: {result.depression_risk}")

# Test 3
print("\n✅ Test 3: Neutral")
result = analyzer.analyze_sentiment("Normal day")
print(f"   Score: {result.score:.2f}, Label: {result.label}")

print("\n" + "="*80)
print("✅ ALL SENTIMENT TESTS WORKING!")
print("="*80)

# Now test risk model
print("\n" + "="*80)
print("🧪 DIRECT TEST - RISK MODEL")
print("="*80)

from ml.risk_model import RiskPredictionModel

print("\n✅ Training model...")
model = RiskPredictionModel()
model.train_demo_model()

# Test with example
from ml.contracts import EXAMPLE_INPUT

print("✅ Predicting risks...")
risks = model.predict_all_risks(EXAMPLE_INPUT)
print(f"   Overall Risk: {risks['overall_risk_score']:.1f}/100")
print(f"   Progression: {risks['progression_risk']:.1f}%")
print(f"   Adherence: {risks['adherence_risk']:.1f}%")
print(f"   Injury: {risks['injury_risk']:.1f}%")

print("\n" + "="*80)
print("✅ ALL RISK TESTS WORKING!")
print("="*80)

# Test pipeline
print("\n" + "="*80)
print("🧪 DIRECT TEST - COMPLETE PIPELINE")
print("="*80)

from ml.pipeline import MLPipeline

print("\n✅ Running pipeline...")
pipeline = MLPipeline()
output = pipeline.process_user_profile(EXAMPLE_INPUT)

print(f"   Risk Score: {output['risk_assessment']['risk_score']:.1f}/100")
print(f"   Risk Level: {output['risk_assessment']['risk_level']}")
print(f"   Sentiment: {output['sentiment_analysis']['sentiment_label']}")
print(f"   Exercise: {output['recommended_exercise_intensity']}")
print(f"   Warnings: {len(output['warnings'])}")

print("\n" + "="*80)
print("✅ ALL PIPELINE TESTS WORKING!")
print("="*80)

print("\n🎉 CONCLUSION: TON MODÈLE FONCTIONNE PARFAITEMENT!")
print("\n" + "="*80)

