"""
Performance & Deployment Configuration for ML Module
"""

# ML_CONFIG.py - Central configuration for ML module

class MLConfig:
    """ML Pipeline Configuration"""

    # Model Settings
    MODEL_VERSION = "1.0"
    MODEL_TYPE = "xgboost"  # or "heuristic"

    # Risk Thresholds
    RISK_THRESHOLDS = {
        "low": (0, 30),
        "moderate": (30, 60),
        "high": (60, 80),
        "critical": (80, 100)
    }

    # Clinical Thresholds (for warnings)
    CLINICAL_THRESHOLDS = {
        "hba1c_warning": 8.0,
        "hba1c_critical": 8.5,
        "blood_pressure_warning": 140,
        "blood_pressure_critical": 160,
        "vo2_max_low": 25,
        "vo2_max_critical": 20,
        "exercise_adherence_low": 3,  # days/month
        "hrv_warning": 40,
        "hrv_critical": 25
    }

    # Exercise Intensity Levels
    INTENSITY_LEVELS = {
        "very_light": {"max_hr": "50-60%", "mets": "1.0-2.0", "example": "light walking"},
        "light": {"max_hr": "60-70%", "mets": "2.0-3.0", "example": "brisk walking"},
        "moderate": {"max_hr": "70-85%", "mets": "3.0-6.0", "example": "jogging"},
        "vigorous": {"max_hr": "85-100%", "mets": "6.0+", "example": "running"}
    }

    # Sentiment Analysis Settings
    SENTIMENT_CONFIDENCE_THRESHOLD = 0.6
    DEPRESSION_DETECTION_ENABLED = True
    CBT_INTERVENTIONS_ENABLED = True

    # Performance Settings
    RESPONSE_TIMEOUT_SECONDS = 5
    CACHE_PREDICTIONS = True
    CACHE_TTL_SECONDS = 300  # 5 minutes

    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "ml_pipeline.log"

    # Feature Engineering
    FEATURE_SCALING_METHOD = "standardize"  # or "normalize"
    HANDLE_MISSING_VALUES = "interpolate"  # or "drop", "mean"

    @classmethod
    def get_intensity_for_risk_level(cls, risk_level: str) -> str:
        """Map risk level to exercise intensity"""
        mapping = {
            "low": "vigorous",
            "moderate": "moderate",
            "high": "light",
            "critical": "very_light"
        }
        return mapping.get(risk_level, "moderate")


class PerformanceMonitoring:
    """Monitor ML module performance"""

    @staticmethod
    def log_prediction(user_id: str, risk_score: float, exec_time_ms: float):
        """Log each prediction for monitoring"""
        pass

    @staticmethod
    def track_sentiment_accuracy(feedback: str, predicted_sentiment: str, actual_sentiment: str):
        """Track sentiment analysis accuracy"""
        pass

    @staticmethod
    def get_metrics_summary() -> dict:
        """Get summary of performance metrics"""
        return {
            "total_predictions": 0,
            "avg_response_time_ms": 0,
            "sentiment_accuracy": 0.0,
            "warning_generation_rate": 0.0
        }


# For FastAPI integration
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 ML Module starting...")
    from ml.pipeline import get_ml_pipeline
    pipeline = get_ml_pipeline()
    print(f"✅ ML Pipeline initialized: {pipeline.health_check()}")

    yield

    # Shutdown
    print("🛑 ML Module shutting down...")
    # Cleanup if needed
    print("✅ ML Module stopped")

