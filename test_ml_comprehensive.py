"""
Final Comprehensive Test of ML Module
Run this to verify everything works end-to-end
"""

import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path.parent))

def test_section(title):
    """Print formatted test section"""
    print("\n" + "="*80)
    print(f"🧪 TEST: {title}")
    print("="*80)

def test_imports():
    """Test all imports work"""
    test_section("Module Imports")

    try:
        from backend.ml.contracts import UserProfile, MLModuleOutput, EXAMPLE_INPUT
        print("✅ contracts.py imports successful")

        from backend.ml.sentiment_analysis import SentimentAnalyzer, MotivationEngine
        print("✅ sentiment_analysis.py imports successful")

        from backend.ml.risk_model import RiskPredictionModel
        print("✅ risk_model.py imports successful")

        from backend.ml.pipeline import MLPipeline, get_ml_pipeline
        print("✅ pipeline.py imports successful")

        from backend.ml.config import MLConfig
        print("✅ config.py imports successful")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_contracts():
    """Test contract validation"""
    test_section("Contract Validation")

    try:
        from backend.ml.contracts import EXAMPLE_INPUT, UserProfile

        # Validate example input
        profile = UserProfile(**EXAMPLE_INPUT)
        print(f"✅ EXAMPLE_INPUT validates: User {profile.user_id}, Age {profile.age}")

        # Test invalid input
        try:
            invalid = UserProfile(user_id="test", age=500)  # Invalid age
            print("❌ Should have rejected invalid age")
            return False
        except Exception:
            print("✅ Invalid input correctly rejected")

        return True
    except Exception as e:
        print(f"❌ Contract validation failed: {e}")
        return False

def test_sentiment():
    """Test sentiment analysis"""
    test_section("Sentiment Analysis")

    try:
        from backend.ml.sentiment_analysis import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        # Test positive
        result = analyzer.analyze_sentiment("I'm feeling great and excited!")
        assert result.score > 0.3, "Positive sentiment not detected"
        print(f"✅ Positive: score={result.score:.2f}, label={result.label}")

        # Test negative
        result = analyzer.analyze_sentiment("I feel hopeless and worthless")
        assert result.score < -0.3, "Negative sentiment not detected"
        assert result.depression_risk, "Depression not detected"
        print(f"✅ Negative: score={result.score:.2f}, depression_risk={result.depression_risk}")

        # Test neutral
        result = analyzer.analyze_sentiment("It's a normal day")
        assert -0.3 <= result.score <= 0.3, "Neutral not detected"
        print(f"✅ Neutral: score={result.score:.2f}, label={result.label}")

        # Test empty
        result = analyzer.analyze_sentiment(None)
        assert result.score == 0.0, "Empty not handled"
        print(f"✅ Empty: score={result.score:.2f}, confidence={result.confidence:.2f}")

        return True
    except Exception as e:
        print(f"❌ Sentiment analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_motivation_engine():
    """Test motivation engine"""
    test_section("Motivation Engine")

    try:
        from backend.ml.sentiment_analysis import MotivationEngine

        engine = MotivationEngine()

        result = engine.analyze_and_recommend({}, "I'm feeling motivated today!")

        assert 'sentiment_analysis' in result, "Missing sentiment_analysis"
        assert 'cbt_interventions' in result, "Missing cbt_interventions"
        assert 'intensity_adjustment' in result, "Missing intensity_adjustment"
        assert 'motivational_message' in result, "Missing motivational_message"

        print(f"✅ Analysis complete")
        print(f"   • Sentiment: {result['sentiment_analysis']['sentiment_label']}")
        print(f"   • Intensity adjustment: {result['intensity_adjustment']['adjustment_factor']}")
        print(f"   • Message: {result['motivational_message']}")

        return True
    except Exception as e:
        print(f"❌ Motivation engine failed: {e}")
        return False

def test_risk_model():
    """Test risk prediction"""
    test_section("Risk Prediction Model")

    try:
        from backend.ml.risk_model import RiskPredictionModel
        from backend.ml.contracts import EXAMPLE_INPUT

        model = RiskPredictionModel()
        model.train_demo_model()
        print(f"✅ Model trained")

        # Feature extraction
        X, names = model.extract_features_from_profile(EXAMPLE_INPUT)
        print(f"✅ Features extracted: {len(names)} features")

        # Prediction
        score = model.predict_risk_score(X)
        assert 0 <= score <= 100, "Risk score out of bounds"
        print(f"✅ Risk score: {score:.1f}/100")

        # All risks
        predictions = model.predict_all_risks(EXAMPLE_INPUT)
        assert 'progression_risk' in predictions
        assert 'adherence_risk' in predictions
        assert 'injury_risk' in predictions
        print(f"✅ All risk predictions:")
        print(f"   • Progression: {predictions['progression_risk']:.1f}%")
        print(f"   • Adherence: {predictions['adherence_risk']:.1f}%")
        print(f"   • Injury: {predictions['injury_risk']:.1f}%")

        return True
    except Exception as e:
        print(f"❌ Risk model failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_pipeline():
    """Test complete ML pipeline"""
    test_section("Complete ML Pipeline")

    try:
        from backend.ml.pipeline import MLPipeline
        from backend.ml.contracts import EXAMPLE_INPUT
        import json

        pipeline = MLPipeline()

        # Health check
        health = pipeline.health_check()
        print(f"✅ Health check: {health['status']}")

        # Process profile
        output = pipeline.process_user_profile(EXAMPLE_INPUT)

        if "error" in output:
            print(f"❌ Pipeline error: {output['error']}")
            return False

        # Validate output structure
        assert 'user_id' in output
        assert 'risk_assessment' in output
        assert 'sentiment_analysis' in output
        assert 'recommended_exercise_intensity' in output
        assert 'warnings' in output

        print(f"✅ Pipeline executed successfully")
        print(f"   • Risk Level: {output['risk_assessment']['risk_level']}")
        print(f"   • Risk Score: {output['risk_assessment']['risk_score']:.1f}/100")
        print(f"   • Exercise Intensity: {output['recommended_exercise_intensity']}")
        print(f"   • Warnings: {len(output['warnings'])}")

        # Validate output can be serialized to JSON
        json_str = json.dumps(output)
        print(f"✅ Output is valid JSON ({len(json_str)} bytes)")

        return True
    except Exception as e:
        print(f"❌ Complete pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_profiles():
    """Test with different risk profiles"""
    test_section("Different Risk Profiles")

    try:
        from backend.ml.pipeline import MLPipeline

        pipeline = MLPipeline()

        profiles = {
            "Low-Risk": {
                "user_id": "low_risk",
                "age": 25,
                "bmi": 22,
                "vo2_max": 50,
                "hba1c": 5.0,
                "fasting_glucose": 95,
                "health_conditions": [],
                "exercise_history_days": 25,
                "current_medications": [],
                "current_biometrics": {
                    "heart_rate": 60,
                    "heart_rate_variability": 80,
                    "daily_steps": 12000,
                    "sleep_duration": 8,
                    "blood_pressure_systolic": 110,
                    "blood_pressure_diastolic": 70
                }
            },
            "High-Risk": {
                "user_id": "high_risk",
                "age": 70,
                "bmi": 32,
                "vo2_max": 20,
                "hba1c": 8.5,
                "fasting_glucose": 160,
                "health_conditions": [
                    {"condition_name": "diabetes", "severity": "severe", "duration_years": 15}
                ],
                "exercise_history_days": 2,
                "current_medications": ["Metformin", "Lisinopril"],
                "current_biometrics": {
                    "heart_rate": 92,
                    "heart_rate_variability": 30,
                    "daily_steps": 2500,
                    "sleep_duration": 5.5,
                    "blood_pressure_systolic": 150,
                    "blood_pressure_diastolic": 95
                }
            }
        }

        for profile_name, profile_data in profiles.items():
            result = pipeline.process_user_profile(profile_data)
            risk_level = result['risk_assessment']['risk_level']
            intensity = result['recommended_exercise_intensity']
            print(f"✅ {profile_name}: risk={risk_level}, intensity={intensity}")

        return True
    except Exception as e:
        print(f"❌ Profile testing failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🎬 "*40)
    print("COMPREHENSIVE ML MODULE TEST SUITE")
    print("🎬 "*40)

    tests = [
        ("Module Imports", test_imports),
        ("Contract Validation", test_contracts),
        ("Sentiment Analysis", test_sentiment),
        ("Motivation Engine", test_motivation_engine),
        ("Risk Model", test_risk_model),
        ("Complete Pipeline", test_complete_pipeline),
        ("Different Profiles", test_different_profiles),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ FATAL ERROR in {test_name}: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n🎯 Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! ML Module is ready for deployment!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

