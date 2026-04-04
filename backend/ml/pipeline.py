"""
Complete ML Pipeline Orchestrator
Integrates risk prediction, sentiment analysis, and recommendations
"""

from typing import Dict, Optional
from datetime import datetime
import json

from backend.ml.contracts import UserProfile, MLModuleOutput, RiskAssessment, SentimentAnalysis
from backend.ml.risk_model import RiskPredictionModel, get_risk_model
from backend.ml.sentiment_analysis import MotivationEngine, get_motivation_engine


class MLPipeline:
    """
    Main orchestrator for all ML operations
    """

    def __init__(self):
        self.risk_model = get_risk_model()
        self.motivation_engine = get_motivation_engine()

    def process_user_profile(self, user_profile_dict: Dict) -> Dict:
        """
        Complete ML pipeline: Risk + Sentiment + Recommendations
        Input: Raw user profile dict
        Output: Structured MLModuleOutput dict
        """

        try:
            # Validate input
            user_profile = UserProfile(**user_profile_dict)
        except Exception as e:
            return {
                "error": f"Invalid user profile: {str(e)}",
                "status": "failed"
            }

        # ============================================
        # STEP 1: Risk Prediction
        # ============================================
        risk_predictions = self.risk_model.predict_all_risks(user_profile_dict)

        overall_risk = risk_predictions['overall_risk_score']

        # Determine risk level
        if overall_risk < 30:
            risk_level = 'low'
        elif overall_risk < 60:
            risk_level = 'moderate'
        elif overall_risk < 80:
            risk_level = 'high'
        else:
            risk_level = 'critical'

        # ============================================
        # STEP 2: Sentiment Analysis & Motivation
        # ============================================
        user_feedback = user_profile_dict.get('user_feedback_text')
        motivation_analysis = self.motivation_engine.analyze_and_recommend(
            user_profile_dict,
            user_feedback
        )

        # ============================================
        # STEP 3: Determine Exercise Intensity
        # ============================================
        intensity_level, intensity_rationale = self._determine_exercise_intensity(
            overall_risk,
            motivation_analysis,
            user_profile_dict
        )

        # ============================================
        # STEP 4: Generate Safety Warnings
        # ============================================
        warnings = self._generate_safety_warnings(
            overall_risk,
            risk_predictions,
            user_profile_dict,
            motivation_analysis
        )

        # ============================================
        # STEP 5: Build Output Contract
        # ============================================
        output = MLModuleOutput(
            user_id=user_profile.user_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            risk_assessment=RiskAssessment(
                risk_score=overall_risk,
                risk_level=risk_level,
                progression_risk=risk_predictions['progression_risk'],
                adherence_risk=risk_predictions['adherence_risk'],
                injury_risk=risk_predictions['injury_risk'],
                explanation=risk_predictions['explanation']
            ),
            sentiment_analysis=SentimentAnalysis(
                sentiment_score=motivation_analysis['sentiment_analysis']['score'],
                sentiment_label=motivation_analysis['sentiment_analysis']['sentiment_label'],
                motivation_level=motivation_analysis['sentiment_analysis']['motivation_level'],
                depression_risk_indicator=motivation_analysis['sentiment_analysis']['depression_risk'],
                cbt_intervention_needed=motivation_analysis['sentiment_analysis']['cbt_needed'],
                confidence=motivation_analysis['sentiment_analysis']['confidence']
            ),
            recommended_exercise_intensity=intensity_level,
            intensity_rationale=intensity_rationale,
            warnings=warnings,
            metadata={
                "model_version": "ml_v1.0",
                "risk_factors": list(zip(
                    ['progression_risk', 'adherence_risk', 'injury_risk'],
                    [
                        risk_predictions['progression_risk'],
                        risk_predictions['adherence_risk'],
                        risk_predictions['injury_risk']
                    ]
                )),
                "sentiment_keywords": motivation_analysis['sentiment_analysis'].get('keywords', []),
                "cbt_strategy": motivation_analysis.get('recommended_cbt_framework')
            }
        )

        return json.loads(output.model_dump_json())

    def _determine_exercise_intensity(self, risk_score: float,
                                     motivation_analysis: Dict,
                                     user_profile: Dict) -> tuple:
        """
        Determine appropriate exercise intensity based on:
        - Risk score
        - Motivation level
        - Biometric data
        """

        base_intensity_map = {
            'low': 'vigorous',
            'moderate': 'moderate',
            'high': 'light',
            'critical': 'very_light'
        }

        # Start with risk-based intensity
        if risk_score < 30:
            base_intensity = 'vigorous'
            base_rationale = "Low risk profile allows vigorous exercise"
        elif risk_score < 60:
            base_intensity = 'moderate'
            base_rationale = "Moderate risk recommends moderate intensity"
        elif risk_score < 80:
            base_intensity = 'light'
            base_rationale = "High risk requires light intensity with monitoring"
        else:
            base_intensity = 'very_light'
            base_rationale = "Critical risk requires very light activity focused on safety"

        # Adjust for motivation
        motivation_level = motivation_analysis['sentiment_analysis']['motivation_level']
        adjustment_factor = motivation_analysis['intensity_adjustment']['adjustment_factor']

        # Apply adjustment
        intensity_levels = ['very_light', 'light', 'moderate', 'vigorous']
        current_idx = intensity_levels.index(base_intensity)

        if adjustment_factor < 0.8:
            # Reduce intensity
            adjusted_idx = max(0, current_idx - 1)
        elif adjustment_factor > 1.1:
            # Increase intensity
            adjusted_idx = min(len(intensity_levels) - 1, current_idx + 1)
        else:
            adjusted_idx = current_idx

        adjusted_intensity = intensity_levels[adjusted_idx]

        # Build rationale
        if adjustment_factor != 1.0:
            rationale = f"{base_rationale}. Adjusted to {adjusted_intensity} due to {motivation_level} motivation."
        else:
            rationale = base_rationale

        return adjusted_intensity, rationale

    def _generate_safety_warnings(self, risk_score: float,
                                 risk_predictions: Dict,
                                 user_profile: Dict,
                                 motivation_analysis: Dict) -> list:
        """
        Generate safety warnings based on risk factors and conditions
        """
        warnings = []

        # Critical risk warnings
        if risk_score > 80:
            warnings.append("CRITICAL: High overall risk. Medical clearance recommended before exercise.")

        # Clinical markers
        hba1c = user_profile.get('hba1c')
        if hba1c and hba1c > 8.5:
            warnings.append("HbA1c level is elevated. Monitor blood glucose before and after exercise.")

        bp_sys = user_profile.get('current_biometrics', {}).get('blood_pressure_systolic', 0)
        if bp_sys > 160:
            warnings.append("Blood pressure is elevated. Consult with physician before exercise.")

        # High progression risk
        if risk_predictions['progression_risk'] > 75:
            warnings.append("High disease progression risk detected. Conservative approach recommended.")

        # High injury risk
        if risk_predictions['injury_risk'] > 70:
            warnings.append("Injury risk is elevated. Emphasize proper form and gradual progression.")

        # Depression/mental health
        if motivation_analysis['sentiment_analysis']['depression_risk']:
            warnings.append("Depression risk detected. Consider referring to mental health support. Exercise as medicine, not as punishment.")

        # Low motivation
        if motivation_analysis['sentiment_analysis']['motivation_level'] == 'low':
            warnings.append("User motivation is low. Start with low-pressure, enjoyable activities.")

        # Adherence concerns
        if risk_predictions['adherence_risk'] > 70:
            warnings.append("High non-adherence risk. Plan motivational checkpoints throughout week.")

        # VO2 Max concern
        vo2 = user_profile.get('vo2_max')
        if vo2 and vo2 < 20:
            warnings.append("Very low VO2 max. Avoid high-intensity cardio. Focus on gradual improvement.")

        return warnings

    def health_check(self) -> Dict:
        """
        Health check endpoint for debugging
        """
        return {
            "status": "healthy",
            "risk_model": "ready" if self.risk_model.model is not None else "not_initialized",
            "motivation_engine": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }


# Global pipeline instance
_pipeline = None

def get_ml_pipeline() -> MLPipeline:
    """Get or create global ML pipeline"""
    global _pipeline
    if _pipeline is None:
        _pipeline = MLPipeline()
    return _pipeline


# For testing
if __name__ == "__main__":
    from contracts import EXAMPLE_INPUT
    import json

    pipeline = MLPipeline()
    result = pipeline.process_user_profile(EXAMPLE_INPUT)

    print("\n" + "="*80)
    print("ML PIPELINE OUTPUT")
    print("="*80)
    print(json.dumps(result, indent=2))
    print("="*80)

