"""
motivator_ml.py
Agent: bridges engineered features → ML pipeline → returns risk + sentiment output.
"""

from typing import Dict, Any
from ml.pipeline import get_ml_pipeline


def run_ml_analysis(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send engineered features to the ML pipeline.
    Returns full MLModuleOutput dict.
    """
    pipeline = get_ml_pipeline()
    return pipeline.process_user_profile(features)
