"""
XGBoost Predictive Model for SportRX AI
Predicts: Risk Score, Progression Risk, Adherence Risk, Injury Risk
"""

import numpy as np
from typing import Dict, Tuple, List
import warnings

warnings.filterwarnings('ignore')

# Try to import optional ML libraries
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


class RiskPredictionModel:
    """
    XGBoost model for predicting patient risk across multiple dimensions
    """

    def __init__(self, model_path: str = None):
        self.model = None
        self.feature_names = None
        self.model_path = model_path
        self.explainer = None

    def get_feature_names(self) -> List[str]:
        """Return list of expected features in order"""
        return [
            'age', 'bmi', 'vo2_max', 'hba1c', 'fasting_glucose',
            'heart_rate', 'heart_rate_variability', 'daily_steps',
            'sleep_duration', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'exercise_history_days', 'condition_duration_years', 'num_medications',
            'is_diabetic', 'is_hypertensive', 'is_depressive'
        ]

    def extract_features_from_profile(self, user_profile: Dict) -> Tuple[np.ndarray, List[str]]:
        """
        Extract features from user profile dict
        Returns: (feature_array, feature_names)
        """
        features = {}

        # Basic demographics
        features['age'] = user_profile.get('age', 50)
        features['bmi'] = user_profile.get('bmi', 25)
        features['vo2_max'] = user_profile.get('vo2_max', 35.0)

        # Clinical markers
        features['hba1c'] = user_profile.get('hba1c', 5.5)
        features['fasting_glucose'] = user_profile.get('fasting_glucose', 100)

        # Biometrics
        biometrics = user_profile.get('current_biometrics', {})
        features['heart_rate'] = biometrics.get('heart_rate', 70)
        features['heart_rate_variability'] = biometrics.get('heart_rate_variability', 50)
        features['daily_steps'] = biometrics.get('daily_steps', 5000)
        features['sleep_duration'] = biometrics.get('sleep_duration', 7)
        features['blood_pressure_systolic'] = biometrics.get('blood_pressure_systolic', 120)
        features['blood_pressure_diastolic'] = biometrics.get('blood_pressure_diastolic', 80)

        # Exercise history
        features['exercise_history_days'] = user_profile.get('exercise_history_days', 0)

        # Condition info
        conditions = user_profile.get('health_conditions', [])
        if conditions:
            features['condition_duration_years'] = conditions[0].get('duration_years', 0)
        else:
            features['condition_duration_years'] = 0

        features['num_medications'] = len(user_profile.get('current_medications', []))

        # Condition flags
        condition_names = [c.get('condition_name', '').lower() for c in conditions]
        features['is_diabetic'] = 1 if 'diabetes' in condition_names else 0
        features['is_hypertensive'] = 1 if 'hypertension' in condition_names else 0
        features['is_depressive'] = 1 if 'depression' in condition_names else 0

        # Convert to ordered array
        feature_names = self.get_feature_names()
        feature_array = np.array([features.get(name, 0) for name in feature_names]).reshape(1, -1)

        return feature_array, feature_names

    def train_demo_model(self, X_train: np.ndarray = None, y_train: np.ndarray = None):
        """
        Train XGBoost model on demo data
        If XGBoost not available, uses heuristic-based fallback
        If no data provided, uses synthetic data
        """
        if not HAS_XGBOOST:
            print("⚠️  XGBoost not installed. Using heuristic-based fallback model.")
            self.model = "heuristic"  # Use heuristic fallback
            return self

        if X_train is None or y_train is None:
            # Generate synthetic training data (100 samples)
            np.random.seed(42)
            n_samples = 100
            feature_names = self.get_feature_names()

            # Realistic synthetic data
            data = {
                'age': np.random.randint(25, 80, n_samples),
                'bmi': np.random.uniform(18, 45, n_samples),
                'vo2_max': np.random.uniform(20, 60, n_samples),
                'hba1c': np.random.uniform(4.5, 10, n_samples),
                'fasting_glucose': np.random.uniform(80, 200, n_samples),
                'heart_rate': np.random.uniform(55, 100, n_samples),
                'heart_rate_variability': np.random.uniform(20, 100, n_samples),
                'daily_steps': np.random.randint(2000, 15000, n_samples),
                'sleep_duration': np.random.uniform(4, 9, n_samples),
                'blood_pressure_systolic': np.random.uniform(110, 160, n_samples),
                'blood_pressure_diastolic': np.random.uniform(70, 105, n_samples),
                'exercise_history_days': np.random.randint(0, 31, n_samples),
                'condition_duration_years': np.random.uniform(0, 20, n_samples),
                'num_medications': np.random.randint(0, 5, n_samples),
                'is_diabetic': np.random.randint(0, 2, n_samples),
                'is_hypertensive': np.random.randint(0, 2, n_samples),
                'is_depressive': np.random.randint(0, 2, n_samples),
            }

            X_train = np.column_stack([data[name] for name in feature_names])

            # Create risk score based on features (higher values = higher risk)
            risk_score = (
                (data['hba1c'] - 5.5) * 5 +  # HbA1c contribution
                (data['blood_pressure_systolic'] - 120) * 0.3 +  # BP contribution
                (data['bmi'] - 25) * 1.5 +  # BMI contribution
                (30 - data['exercise_history_days']) * 1.0 +  # Exercise adherence
                (data['age'] - 50) * 0.2 +  # Age factor
                np.random.normal(0, 10, n_samples)  # Random noise
            )
            y_train = np.clip(risk_score, 0, 100)  # Normalize to 0-100

        self.feature_names = self.get_feature_names()

        # Train XGBoost model
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective='reg:squarederror'
        )

        self.model.fit(X_train, y_train, verbose=False)

        # Initialize SHAP explainer for interpretability
        if HAS_SHAP:
            try:
                self.explainer = shap.TreeExplainer(self.model)
            except Exception as e:
                print(f"Warning: Could not initialize SHAP explainer: {e}")
                self.explainer = None

        return self

    def predict_risk_score(self, X: np.ndarray) -> float:
        """
        Predict overall risk score (0-100)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train_demo_model() first.")

        if self.model == "heuristic":
            # Fallback heuristic-based prediction
            return self._predict_heuristic(X)

        prediction = self.model.predict(X)[0]
        return float(np.clip(prediction, 0, 100))

    def _predict_heuristic(self, X: np.ndarray) -> float:
        """
        Heuristic-based risk prediction (no ML library needed)
        """
        feature_names = self.get_feature_names()
        features = {name: X[0, i] for i, name in enumerate(feature_names)}

        # Calculate risk score from clinical markers
        risk_score = 50.0  # Base score

        # HbA1c: Major factor for diabetics
        hba1c = features['hba1c']
        if hba1c > 8.5:
            risk_score += 20
        elif hba1c > 7.5:
            risk_score += 15
        elif hba1c > 6.5:
            risk_score += 8

        # Blood pressure
        bp_sys = features['blood_pressure_systolic']
        if bp_sys > 160:
            risk_score += 15
        elif bp_sys > 140:
            risk_score += 10
        elif bp_sys > 130:
            risk_score += 5

        # BMI
        bmi = features['bmi']
        if bmi > 35:
            risk_score += 12
        elif bmi > 30:
            risk_score += 8
        elif bmi < 18.5:
            risk_score += 5

        # VO2 Max (inverse - lower is worse)
        vo2 = features['vo2_max']
        if vo2 < 20:
            risk_score += 15
        elif vo2 < 30:
            risk_score += 8

        # Exercise adherence (past 30 days)
        exercise_days = features['exercise_history_days']
        if exercise_days < 3:
            risk_score += 15
        elif exercise_days < 10:
            risk_score += 8

        # Age
        age = features['age']
        if age > 70:
            risk_score += 12
        elif age > 60:
            risk_score += 6
        elif age > 50:
            risk_score += 3

        # Medication count (indicator of complexity)
        num_meds = features['num_medications']
        if num_meds > 4:
            risk_score += 8
        elif num_meds > 2:
            risk_score += 4

        # Conditions
        if features['is_diabetic']:
            risk_score += 10
        if features['is_hypertensive']:
            risk_score += 8
        if features['is_depressive']:
            risk_score += 10

        # Sleep (poor sleep increases risk)
        sleep_duration = features['sleep_duration']
        if sleep_duration < 5:
            risk_score += 10
        elif sleep_duration < 6:
            risk_score += 5

        # Heart rate variability (low HRV = stress/risk)
        hrv = features['heart_rate_variability']
        if hrv < 25:
            risk_score += 10
        elif hrv < 40:
            risk_score += 5

        # Normalize to 0-100
        risk_score = float(np.clip(risk_score - 50 + np.random.normal(0, 5), 0, 100))
        return risk_score

    def predict_all_risks(self, user_profile: Dict) -> Dict:
        """
        Predict all risk dimensions from user profile
        Returns dictionary with risk scores and explanations
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train_demo_model() first.")

        # Extract features
        X, feature_names = self.extract_features_from_profile(user_profile)

        # Predict overall risk
        overall_risk = self.predict_risk_score(X)

        # Derive other risks based on features
        conditions = user_profile.get('health_conditions', [])
        condition_names = [c.get('condition_name', '').lower() for c in conditions]
        biometrics = user_profile.get('current_biometrics', {})

        # Progression risk: depends on clinical markers and condition severity
        hba1c = user_profile.get('hba1c', 5.5)
        if hba1c > 8.0:
            progression_risk = min(90, overall_risk * 1.3)
        elif hba1c > 7.0:
            progression_risk = min(85, overall_risk * 1.1)
        else:
            progression_risk = overall_risk * 0.8

        # Adherence risk: depends on past exercise and motivation
        exercise_days = user_profile.get('exercise_history_days', 0)
        adherence_risk = max(10, 100 - (exercise_days * 2))

        # Injury risk: depends on intensity markers and VO2 max
        vo2_max = user_profile.get('vo2_max', 35)
        hr_variability = biometrics.get('heart_rate_variability', 50)
        if vo2_max < 25 or hr_variability < 30:
            injury_risk = min(80, overall_risk * 0.9)
        else:
            injury_risk = overall_risk * 0.6

        # Generate SHAP explanation
        explanation = self._generate_shap_explanation(X, feature_names)

        return {
            'overall_risk_score': overall_risk,
            'progression_risk': float(np.clip(progression_risk, 0, 100)),
            'adherence_risk': float(np.clip(adherence_risk, 0, 100)),
            'injury_risk': float(np.clip(injury_risk, 0, 100)),
            'explanation': explanation
        }

    def _generate_shap_explanation(self, X: np.ndarray, feature_names: List[str]) -> str:
        """
        Generate human-readable explanation using SHAP
        """
        try:
            if self.explainer is None:
                return "Risk assessment completed. Model uses HbA1c, blood pressure, BMI, and exercise adherence as primary indicators."

            # Get SHAP values
            shap_values = self.explainer.shap_values(X)

            # Get feature importance
            feature_importance = list(zip(feature_names, np.abs(shap_values[0])))
            feature_importance.sort(key=lambda x: x[1], reverse=True)

            # Build explanation
            top_3 = feature_importance[:3]
            explanation = "Top risk factors: "
            explanation += ", ".join([f"{name.replace('_', ' ')} ({val:.2f})" for name, val in top_3])

            return explanation
        except Exception as e:
            return f"Model explanation: Risk score based on clinical profile. ({str(e)[:50]}...)"

    def save_model(self, path: str):
        """Save trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save. Train first.")
        joblib.dump(self.model, path)
        print(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load trained model from disk"""
        self.model = joblib.load(path)
        self.explainer = None  # Reset explainer
        return self


# Singleton instance for the application
_risk_model = None

def get_risk_model() -> RiskPredictionModel:
    """Get or create the global risk model instance"""
    global _risk_model
    if _risk_model is None:
        _risk_model = RiskPredictionModel()
        _risk_model.train_demo_model()
    return _risk_model


# For testing
if __name__ == "__main__":
    from contracts import EXAMPLE_INPUT

    model = RiskPredictionModel()
    model.train_demo_model()

    predictions = model.predict_all_risks(EXAMPLE_INPUT)
    print("Predictions:", predictions)

