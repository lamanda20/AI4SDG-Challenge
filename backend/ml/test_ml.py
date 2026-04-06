"""Unit Tests for ML Module"""

import pytest
from contracts import EXAMPLE_INPUT
from risk_model import RiskPredictionModel
from sentiment_analysis import SentimentAnalyzer
from pipeline import MLPipeline


class TestRiskModel:
    """Test XGBoost risk prediction model"""

    def test_model_initialization(self):
        model = RiskPredictionModel()
        model.train_demo_model()
        assert model.model is not None

    def test_risk_prediction(self):
        model = RiskPredictionModel()
        model.train_demo_model()
        X, _ = model.extract_features_from_profile(EXAMPLE_INPUT)
        score = model.predict_risk_score(X)
        assert 0 <= score <= 100


class TestSentimentAnalyzer:
    """Test sentiment analysis"""

    def test_positive_sentiment(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_sentiment("I'm excited about exercise!")
        assert result.score > 0.3

    def test_negative_sentiment(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_sentiment("I feel terrible today")
        assert result.score < -0.3


class TestMLPipeline:
    """Test complete ML pipeline"""

    def test_pipeline_execution(self):
        pipeline = MLPipeline()
        output = pipeline.process_user_profile(EXAMPLE_INPUT)
        assert 'user_id' in output
        assert 'risk_assessment' in output

