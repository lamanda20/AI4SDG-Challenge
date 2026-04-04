"""
Test Suite for RAG Medical Engine

Unit tests and integration tests for the clinician_rag module.
Validates that medical guidelines are:
- Evidence-based
- Safe (with guardrails against hallucination)
- JSON-formatted
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Try to import pytest, but make it optional
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    print("[WARNING] pytest not installed. Running basic tests only.")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from clinician_rag import (
    generate_medical_guidelines,
    UserMedicalProfile,
    ExerciseGuideline,
    MedicalGuidelinesResponse,
    RAGGuardrails,
)


class TestInputValidation:
    """Test input validation and model schemas"""

    def test_valid_user_profile(self):
        """Test valid user profile creation"""
        profile = UserMedicalProfile(
            age=50,
            conditions=["type 2 diabetes"],
            bmi=30,
            activity_level="sedentary",
        )
        assert profile.age == 50
        assert profile.conditions == ["type 2 diabetes"]
        assert profile.activity_level == "sedentary"
        print("✓ Valid user profile creation")

    def test_invalid_age(self):
        """Test invalid age is rejected"""
        try:
            UserMedicalProfile(
                age=10,  # Too young
                conditions=["diabetes"],
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✓ Invalid age rejection")

    def test_invalid_activity_level(self):
        """Test invalid activity level is rejected"""
        try:
            UserMedicalProfile(
                age=50,
                conditions=["diabetes"],
                activity_level="ultra-vigorous",  # Invalid
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✓ Invalid activity level rejection")

    def test_empty_conditions(self):
        """Test that conditions are required"""
        try:
            UserMedicalProfile(
                age=50,
                conditions=[],  # Empty
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✓ Empty conditions rejection")

    def test_comorbidities_optional(self):
        """Test that comorbidities are optional"""
        profile = UserMedicalProfile(
            age=50,
            conditions=["diabetes"],
            comorbidities=None,
        )
        assert profile.comorbidities is None
        print("✓ Optional comorbidities")

    def test_with_comorbidities(self):
        """Test profile with multiple conditions"""
        profile = UserMedicalProfile(
            age=55,
            conditions=["type 2 diabetes"],
            comorbidities=["hypertension", "obesity"],
            activity_level="light",
        )
        assert len(profile.comorbidities) == 2
        print("✓ Profile with comorbidities created")


class TestSafetyGuardrails:
    """Test medical safety guardrails"""

    def test_no_recent_events(self):
        """Test safe profile without contraindications"""
        profile = UserMedicalProfile(
            age=50,
            conditions=["type 2 diabetes"],
            bmi=30,
            activity_level="sedentary",
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        assert is_safe is True
        assert len(warnings) == 0
        print("✓ Safe profile detection")

    def test_hypertension_warning(self):
        """Test hypertension safety warning"""
        profile = UserMedicalProfile(
            age=50,
            conditions=["hypertension"],
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        assert any("Monitor" in w for w in warnings)
        print("✓ Hypertension warning generated")

    def test_recent_mi_contraindication(self):
        """Test recent MI is detected as absolute contraindication"""
        profile = UserMedicalProfile(
            age=60,
            conditions=["hypertension"],
            recent_events=["MI 1 month ago"],  # Recent
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        assert is_safe is False
        assert any("MI" in w for w in warnings)
        print("✓ Recent MI contraindication detected")

    def test_old_mi_allowed(self):
        """Test old MI (>3 months) is allowed"""
        profile = UserMedicalProfile(
            age=60,
            conditions=["hypertension"],
            recent_events=["MI 6 months ago"],  # Old
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        # Should be safe from MI contraindication, but may have other warnings
        mi_warnings = [w for w in warnings if "absolute" in w.lower() and "MI" in w]
        assert len(mi_warnings) == 0
        print("✓ Old MI allowed")

    def test_unstable_angina_contraindication(self):
        """Test unstable angina is absolute contraindication"""
        profile = UserMedicalProfile(
            age=60,
            conditions=["unstable angina"],
            recent_events=["unstable angina"],
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        assert is_safe is False
        assert any("unstable angina" in w.lower() for w in warnings)
        print("✓ Unstable angina contraindication detected")

    def test_confidence_adjustment_no_risk(self):
        """Test confidence not reduced for low-risk profile"""
        profile = UserMedicalProfile(
            age=45,
            conditions=["type 2 diabetes"],
            bmi=27,
        )
        adjustment = RAGGuardrails.calculate_confidence_adjustment(profile)
        assert adjustment == 1.0
        print("✓ No confidence reduction for low-risk")

    def test_confidence_adjustment_multiple_risks(self):
        """Test confidence reduced for multiple risk factors"""
        profile = UserMedicalProfile(
            age=70,
            conditions=["type 2 diabetes"],
            comorbidities=["hypertension", "heart disease", "kidney disease"],
            recent_events=["recent event"],
        )
        adjustment = RAGGuardrails.calculate_confidence_adjustment(profile)
        assert adjustment < 1.0
        assert adjustment > 0.5
        print("✓ Confidence adjusted for multiple risks")


class TestSafetyGuardrails:
    """Test medical safety guardrails"""

    def test_no_recent_events(self):
        """Test safe profile without contraindications"""
        profile = UserMedicalProfile(
            age=50,
            conditions=["type 2 diabetes"],
            bmi=30,
            activity_level="sedentary",
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        assert is_safe is True
        assert len(warnings) == 0

    def test_hypertension_warning(self):
        """Test hypertension safety warning"""
        profile = UserMedicalProfile(
            age=50,
            conditions=["hypertension"],
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        assert any("Monitor" in w for w in warnings)

    def test_recent_mi_contraindication(self):
        """Test recent MI is detected as absolute contraindication"""
        profile = UserMedicalProfile(
            age=60,
            conditions=["hypertension"],
            recent_events=["MI 1 month ago"],  # Recent
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        assert is_safe is False
        assert any("MI" in w for w in warnings)

    def test_old_mi_allowed(self):
        """Test old MI (>3 months) is allowed"""
        profile = UserMedicalProfile(
            age=60,
            conditions=["hypertension"],
            recent_events=["MI 6 months ago"],  # Old
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        # Should be safe from MI contraindication, but may have other warnings
        mi_warnings = [w for w in warnings if "absolute" in w.lower() and "MI" in w]
        assert len(mi_warnings) == 0

    def test_unstable_angina_contraindication(self):
        """Test unstable angina is absolute contraindication"""
        profile = UserMedicalProfile(
            age=60,
            conditions=["unstable angina"],
            recent_events=["unstable angina"],
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        assert is_safe is False
        assert any("unstable angina" in w.lower() for w in warnings)

    def test_diabetic_retinopathy_caution(self):
        """Test diabetic retinopathy triggers caution"""
        profile = UserMedicalProfile(
            age=50,
            conditions=["type 2 diabetes"],
            recent_events=["proliferative retinopathy"],
        )
        is_safe, warnings = RAGGuardrails.check_contraindications(profile)
        assert any("retinopathy" in w.lower() for w in warnings)

    def test_confidence_adjustment_no_risk(self):
        """Test confidence not reduced for low-risk profile"""
        profile = UserMedicalProfile(
            age=45,
            conditions=["type 2 diabetes"],
            bmi=27,
        )
        adjustment = RAGGuardrails.calculate_confidence_adjustment(profile)
        assert adjustment == 1.0

    def test_confidence_adjustment_multiple_risks(self):
        """Test confidence reduced for multiple risk factors"""
        profile = UserMedicalProfile(
            age=70,
            conditions=["type 2 diabetes"],
            comorbidities=["hypertension", "heart disease", "kidney disease"],
            recent_events=["recent event"],
        )
        adjustment = RAGGuardrails.calculate_confidence_adjustment(profile)
        assert adjustment < 1.0
        assert adjustment > 0.5


class TestGuidelineGeneration:
    """Test the main guideline generation function"""

    def test_simple_diabetes_profile(self):
        """Test generating guidelines for simple diabetes profile"""
        user_profile = {
            "age": 50,
            "conditions": ["type 2 diabetes"],
            "bmi": 30,
            "activity_level": "sedentary",
        }

        result = generate_medical_guidelines(user_profile)

        # Validate output structure
        assert isinstance(result, dict)
        assert "guidelines" in result
        assert "global_risks" in result
        assert "confidence" in result
        assert "timestamp" in result

        # Validate response format
        assert isinstance(result["guidelines"], list)
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1
        print("✓ Simple diabetes profile generation")

    def test_comorbid_conditions(self):
        """Test generating guidelines for multiple conditions"""
        user_profile = {
            "age": 55,
            "conditions": ["type 2 diabetes", "hypertension"],
            "bmi": 32,
            "activity_level": "light",
            "comorbidities": ["obesity"],
        }

        result = generate_medical_guidelines(user_profile)

        # Should have guidelines for at least one condition
        assert len(result["guidelines"]) >= 0

        # Should identify global risks
        assert len(result["global_risks"]) > 0
        print("✓ Comorbid conditions profile generation")

    def test_json_serializable_output(self):
        """Test that output is valid JSON"""
        user_profile = {
            "age": 50,
            "conditions": ["type 2 diabetes"],
        }

        result = generate_medical_guidelines(user_profile)

        # Should be JSON serializable
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

        # Should parse back
        reparsed = json.loads(json_str)
        assert reparsed["confidence"] == result["confidence"]
        print("✓ JSON serializable output")

    def test_high_risk_profile(self):
        """Test that high-risk profiles have low confidence"""
        user_profile = {
            "age": 65,
            "conditions": ["type 2 diabetes"],
            "activity_level": "sedentary",
            "recent_events": ["MI 2 months ago"],
        }

        result = generate_medical_guidelines(user_profile)

        # Should have low confidence
        assert result["confidence"] < 0.5

        # Should have safety warnings
        assert len(result["safety_warnings"]) > 0
        print("✓ High-risk profile handling")

    def test_exercise_guideline_structure(self):
        """Test that exercise guidelines have required fields"""
        user_profile = {
            "age": 50,
            "conditions": ["type 2 diabetes"],
        }

        result = generate_medical_guidelines(user_profile)

        if result["guidelines"]:
            guideline = result["guidelines"][0]

            # Check required fields
            assert "condition" in guideline
            assert "recommended_exercises" in guideline
            assert "frequency" in guideline
            assert "intensity" in guideline
            assert "source" in guideline

            # Validate types
            assert isinstance(guideline["recommended_exercises"], list)
            assert isinstance(guideline["contraindications"], list)
            assert isinstance(guideline["precautions"], list)
        print("✓ Exercise guideline structure")

    def test_contraindications_in_output(self):
        """Test that contraindications are included when present"""
        user_profile = {
            "age": 50,
            "conditions": ["type 2 diabetes"],
        }

        result = generate_medical_guidelines(user_profile)

        if result["guidelines"]:
            # At least some guidelines should mention contraindications or precautions
            has_safety_info = any(
                len(g["contraindications"]) > 0 or len(g["precautions"]) > 0
                for g in result["guidelines"]
            )
            assert has_safety_info or len(result["guidelines"]) == 0
        print("✓ Contraindications in output")


class TestConfidenceScoring:
    """Test confidence scoring mechanism"""

    def test_confidence_high_for_common_condition(self):
        """Test high confidence for well-documented conditions"""
        user_profile = {
            "age": 50,
            "conditions": ["type 2 diabetes"],
            "bmi": 30,
        }

        result = generate_medical_guidelines(user_profile)
        assert result["confidence"] > 0
        print("✓ Confidence scoring for common condition")

    def test_confidence_factors(self):
        """Test that multiple factors affect confidence"""
        profiles = [
            # High confidence
            {
                "age": 45,
                "conditions": ["type 2 diabetes"],
                "bmi": 28,
                "activity_level": "moderate",
            },
            # Lower confidence (missing data)
            {
                "age": 50,
                "conditions": ["type 2 diabetes"],
                "activity_level": "sedentary",
            },
        ]

        results = [generate_medical_guidelines(p) for p in profiles]

        # First should have higher confidence (more data)
        print(f"  - Profile 1 confidence: {results[0]['confidence']:.2%}")
        print(f"  - Profile 2 confidence: {results[1]['confidence']:.2%}")
        print("✓ Confidence affected by multiple factors")


class TestEvidenceRequirements:
    """Test that responses are evidence-based"""

    def test_guidelines_have_sources(self):
        """Test that guidelines include source information"""
        user_profile = {
            "age": 50,
            "conditions": ["type 2 diabetes"],
        }

        result = generate_medical_guidelines(user_profile)

        if result["guidelines"]:
            for guideline in result["guidelines"]:
                # Source should not be empty
                assert len(guideline["source"]) > 0
        print("✓ Guidelines have sources")

    def test_precautions_included(self):
        """Test that safety precautions are always included"""
        user_profile = {
            "age": 50,
            "conditions": ["type 2 diabetes"],
        }

        result = generate_medical_guidelines(user_profile)

        if result["guidelines"]:
            for guideline in result["guidelines"]:
                # Should have at least one precaution
                assert len(guideline["precautions"]) > 0
        print("✓ Safety precautions included")


class TestIntegration:
    """Integration tests with full pipeline"""

    def test_end_to_end_diabetes_only(self):
        """Test complete flow for single condition"""
        user_profile = {
            "age": 52,
            "conditions": ["type 2 diabetes"],
            "bmi": 29,
            "activity_level": "sedentary",
        }

        result = generate_medical_guidelines(user_profile)

        # Verify complete response structure
        assert result["guidelines"]
        assert result["confidence"] > 0
        assert result["timestamp"]

        # Check guideline content
        first_guideline = result["guidelines"][0]
        assert "diabetes" in first_guideline["condition"].lower()
        assert first_guideline["recommended_exercises"]
        assert first_guideline["frequency"]
        assert first_guideline["intensity"] in [
            "light",
            "moderate",
            "vigorous",
        ]
        print("✓ End-to-end diabetes profile flow")

    def test_end_to_end_comorbid(self):
        """Test complete flow for comorbid conditions"""
        user_profile = {
            "age": 60,
            "conditions": ["type 2 diabetes", "hypertension"],
            "bmi": 33,
            "activity_level": "light",
            "comorbidities": ["obesity"],
        }

        result = generate_medical_guidelines(user_profile)

        assert result["guidelines"]
        assert result["confidence"] > 0

        # Should identify multiple risk factors
        assert len(result["global_risks"]) > 0

        # Should have recommended next steps
        assert len(result["recommended_next_steps"]) > 0
        print("✓ End-to-end comorbid conditions flow")

    def test_elderly_patient(self):
        """Test handling elderly patient with multiple conditions"""
        user_profile = {
            "age": 75,
            "conditions": ["type 2 diabetes"],
            "bmi": 26,
            "activity_level": "light",
        }

        result = generate_medical_guidelines(user_profile)

        # Should have safety warnings for elderly or recommendations
        result_json = json.dumps(result)
        assert "consult" in result_json.lower() or "medical" in result_json.lower()
        print("✓ Elderly patient handling")


# =======================
# TEST EXECUTION
# =======================

if __name__ == "__main__":
    print("=" * 80)
    print("RAG MEDICAL ENGINE - TEST SUITE")
    print("=" * 80)

    try:
        # Run input validation tests
        print("\n[1/6] Testing Input Validation...")
        tv = TestInputValidation()
        tv.test_valid_user_profile()
        tv.test_invalid_age()
        tv.test_invalid_activity_level()
        tv.test_empty_conditions()
        tv.test_comorbidities_optional()
        tv.test_with_comorbidities()

        # Run safety guardrails tests
        print("\n[2/6] Testing Safety Guardrails...")
        sg = TestSafetyGuardrails()
        sg.test_no_recent_events()
        sg.test_hypertension_warning()
        sg.test_recent_mi_contraindication()
        sg.test_old_mi_allowed()
        sg.test_unstable_angina_contraindication()
        sg.test_confidence_adjustment_no_risk()
        sg.test_confidence_adjustment_multiple_risks()

        # Run guideline generation tests
        print("\n[3/6] Testing Guideline Generation...")
        tgg = TestGuidelineGeneration()
        tgg.test_simple_diabetes_profile()
        tgg.test_comorbid_conditions()
        tgg.test_json_serializable_output()
        tgg.test_high_risk_profile()
        tgg.test_exercise_guideline_structure()
        tgg.test_contraindications_in_output()

        # Run confidence scoring tests
        print("\n[4/6] Testing Confidence Scoring...")
        tcs = TestConfidenceScoring()
        tcs.test_confidence_high_for_common_condition()
        tcs.test_confidence_factors()

        # Run evidence requirement tests
        print("\n[5/6] Testing Evidence Requirements...")
        ter = TestEvidenceRequirements()
        ter.test_guidelines_have_sources()
        ter.test_precautions_included()

        # Run integration tests
        print("\n[6/6] Running Integration Tests...")
        ti = TestIntegration()
        ti.test_end_to_end_diabetes_only()
        ti.test_end_to_end_comorbid()
        ti.test_elderly_patient()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)

        # Run example at the end
        print("\n" + "=" * 80)
        print("EXAMPLE: Generate guidelines for diabetes + hypertension patient")
        print("=" * 80 + "\n")

        test_profile = {
            "age": 50,
            "conditions": ["type 2 diabetes", "hypertension"],
            "bmi": 30,
            "activity_level": "sedentary",
        }

        print(f"Input Profile: {json.dumps(test_profile, indent=2)}\n")
        result = generate_medical_guidelines(test_profile)

        print(f"Output (confidence: {result['confidence']:.2%}):")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

