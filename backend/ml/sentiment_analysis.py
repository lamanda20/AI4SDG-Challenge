"""
Sentiment Analysis & CBT Framework for SportRX AI
Detects emotional state and recommends cognitive-behavioral interventions
"""

from typing import Dict, Optional, Tuple
import re
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    score: float  # -1 to 1
    label: str  # 'negative', 'neutral', 'positive'
    motivation_level: str  # 'low', 'medium', 'high'
    depression_risk: bool
    cbt_needed: bool
    confidence: float
    keywords: list


class SentimentAnalyzer:
    """
    Analyzes user feedback text for emotional patterns
    Uses VADER-like heuristics + CBT framework
    """

    def __init__(self):
        # Sentiment lexicon (simplified - in production use VADER or transformers)
        self.positive_words = {
            'great': 0.8, 'excited': 0.9, 'motivated': 0.85, 'energized': 0.8,
            'good': 0.6, 'better': 0.7, 'improved': 0.75, 'happy': 0.8,
            'proud': 0.75, 'accomplished': 0.8, 'strong': 0.7, 'confident': 0.75,
            'enjoying': 0.7, 'love': 0.9, 'awesome': 0.85
        }

        self.negative_words = {
            'terrible': -0.9, 'awful': -0.85, 'hate': -0.9, 'depressed': -0.9,
            'anxious': -0.75, 'worried': -0.7, 'scared': -0.8, 'afraid': -0.75,
            'tired': -0.6, 'exhausted': -0.8, 'overwhelmed': -0.85, 'confused': -0.65,
            'frustrated': -0.75, 'angry': -0.8, 'sad': -0.85, 'lonely': -0.8,
            'hopeless': -0.95, 'worthless': -0.95, 'useless': -0.9, 'fail': -0.8,
            'bad': -0.6, 'worse': -0.7, 'struggling': -0.75, 'difficult': -0.65
        }

        # CBT-relevant patterns for depression risk detection
        self.depression_patterns = [
            r'feel.*hopeless|no.*point|can.*t.*continue',
            r'never.*better|always.*fail|nothing.*works',
            r'worthless|don.*t.*deserve|better.*off.*alone',
            r'kill.*myself|end.*it.*all',  # CRITICAL
            r'constant.*pain|everything.*hurts',
            r'lose.*interest|don.*t.*care.*anymore'
        ]

        # Motivation patterns
        self.high_motivation = [
            r'will.*try|determined|can.*do.*this',
            r'ready.*for.*challenge|looking.*forward',
            r'gonna.*keep.*going|not.*giving.*up'
        ]

        self.low_motivation = [
            r'don.*t.*feel.*like|too.*tired|can.*t.*motivate',
            r'might.*skip|probably.*not.*today',
            r'what.*s.*the.*point|why.*bother'
        ]

    def analyze_sentiment(self, text: Optional[str]) -> SentimentResult:
        """
        Analyze sentiment from user feedback text
        Returns SentimentResult with detailed analysis
        """
        if not text or len(text.strip()) == 0:
            # No text = neutral
            return SentimentResult(
                score=0.0,
                label='neutral',
                motivation_level='medium',
                depression_risk=False,
                cbt_needed=False,
                confidence=0.5,
                keywords=[]
            )

        text_lower = text.lower()

        # Extract emotional keywords
        keywords = self._extract_keywords(text_lower)

        # Calculate sentiment score
        sentiment_score = self._calculate_sentiment_score(text_lower, keywords)

        # Determine sentiment label
        if sentiment_score > 0.3:
            sentiment_label = 'positive'
        elif sentiment_score < -0.3:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'

        # Assess motivation level
        motivation_level = self._assess_motivation(text_lower)

        # Check for depression risk indicators
        depression_risk = self._check_depression_risk(text_lower)

        # Determine if CBT intervention is needed
        cbt_needed = depression_risk or sentiment_score < -0.5 or motivation_level == 'low'

        # Calculate confidence (based on text length and keyword presence)
        confidence = min(0.95, 0.5 + (len(keywords) * 0.1) + (len(text) / 100) * 0.1)

        return SentimentResult(
            score=float(sentiment_score),
            label=sentiment_label,
            motivation_level=motivation_level,
            depression_risk=depression_risk,
            cbt_needed=cbt_needed,
            confidence=float(confidence),
            keywords=keywords
        )

    def _extract_keywords(self, text: str) -> list:
        """Extract emotional keywords from text"""
        keywords = []

        for word in self.positive_words.keys():
            if re.search(r'\b' + word + r'\b', text):
                keywords.append(word)

        for word in self.negative_words.keys():
            if re.search(r'\b' + word + r'\b', text):
                keywords.append(word)

        return keywords

    def _calculate_sentiment_score(self, text: str, keywords: list) -> float:
        """Calculate sentiment score from -1 to 1"""
        if not keywords:
            return 0.0

        scores = []

        # Add positive word scores
        for word in self.positive_words.keys():
            if re.search(r'\b' + word + r'\b', text):
                scores.append(self.positive_words[word])

        # Add negative word scores
        for word in self.negative_words.keys():
            if re.search(r'\b' + word + r'\b', text):
                scores.append(self.negative_words[word])

        if not scores:
            return 0.0

        # Average the scores and cap at -1 to 1
        avg_score = sum(scores) / len(scores)
        return max(-1.0, min(1.0, avg_score))

    def _assess_motivation(self, text: str) -> str:
        """Assess motivation level: 'low', 'medium', 'high'"""
        high_motivation_matches = sum(
            1 for pattern in self.high_motivation
            if re.search(pattern, text, re.IGNORECASE)
        )

        low_motivation_matches = sum(
            1 for pattern in self.low_motivation
            if re.search(pattern, text, re.IGNORECASE)
        )

        if high_motivation_matches > 0 and low_motivation_matches == 0:
            return 'high'
        elif low_motivation_matches > 0:
            return 'low'
        else:
            return 'medium'

    def _check_depression_risk(self, text: str) -> bool:
        """Check for depression risk indicators"""
        for pattern in self.depression_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def get_cbt_intervention(self, sentiment_result: SentimentResult) -> Dict:
        """
        Generate CBT-based intervention recommendations
        Based on sentiment analysis results
        """
        interventions = []
        severity = "info"

        # Critical cases (suicidal ideation)
        text_keywords = sentiment_result.keywords

        if sentiment_result.depression_risk:
            severity = "warning"
            interventions.append({
                "type": "safety_check",
                "message": "We noticed some concerning patterns. Please consider reaching out to a mental health professional.",
                "action": "Show mental health resources"
            })

        # High negative sentiment
        if sentiment_result.score < -0.6:
            severity = "warning"
            interventions.append({
                "type": "emotional_regulation",
                "message": "It sounds like you're having a tough day. Let's try a 5-minute breathing exercise before deciding on exercise intensity.",
                "action": "guided_breathing_exercise.mp3"
            })

        # Low motivation
        if sentiment_result.motivation_level == 'low':
            interventions.append({
                "type": "motivation_boost",
                "message": "Remember your progress! You've completed 12 sessions this month. Let's start with something lighter today.",
                "action": "show_achievement_summary"
            })

        # Neutral/positive but depressive markers
        if sentiment_result.cbt_needed and sentiment_result.score >= -0.3:
            interventions.append({
                "type": "cognitive_reframing",
                "message": "Challenges are opportunities to grow. How about trying a different exercise today?",
                "action": "suggest_variant_exercise"
            })

        # Positive sentiment - reinforce
        if sentiment_result.score > 0.5:
            interventions.append({
                "type": "positive_reinforcement",
                "message": "Great energy today! Let's challenge yourself a bit more if you're ready.",
                "action": "increase_intensity_option"
            })

        return {
            "severity": severity,
            "interventions": interventions,
            "primary_strategy": self._select_primary_strategy(sentiment_result)
        }

    def _select_primary_strategy(self, sentiment_result: SentimentResult) -> str:
        """Select primary CBT strategy based on sentiment"""
        if sentiment_result.depression_risk:
            return "behavioral_activation"  # Get them moving gently
        elif sentiment_result.score < -0.5:
            return "thought_challenging"  # Combat negative thoughts
        elif sentiment_result.motivation_level == 'low':
            return "goal_setting"  # Set realistic, achievable goals
        elif sentiment_result.motivation_level == 'high':
            return "progress_tracking"  # Build momentum
        else:
            return "maintenance"  # Sustain current level


class MotivationEngine:
    """
    Combines sentiment analysis with behavioral science
    to optimize user engagement without toxic positivity
    """

    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()

    def analyze_and_recommend(self, user_profile: Dict,
                            user_feedback: Optional[str] = None) -> Dict:
        """
        Complete sentiment analysis with CBT recommendations
        """
        # Analyze sentiment
        sentiment = self.sentiment_analyzer.analyze_sentiment(user_feedback)

        # Get CBT interventions
        interventions = self.sentiment_analyzer.get_cbt_intervention(sentiment)

        # Determine exercise intensity adjustment
        intensity_adjustment = self._get_intensity_adjustment(sentiment)

        # Generate motivational message
        motivational_message = self._generate_message(sentiment, interventions)

        return {
            "sentiment_analysis": {
                "score": sentiment.score,
                "sentiment_label": sentiment.label,
                "motivation_level": sentiment.motivation_level,
                "depression_risk": sentiment.depression_risk,
                "cbt_needed": sentiment.cbt_needed,
                "confidence": sentiment.confidence
            },
            "cbt_interventions": interventions,
            "intensity_adjustment": intensity_adjustment,
            "motivational_message": motivational_message,
            "recommended_cbt_framework": self._recommend_cbt_framework(sentiment)
        }

    def _get_intensity_adjustment(self, sentiment: SentimentResult) -> Dict:
        """Recommend intensity adjustment based on sentiment"""
        if sentiment.depression_risk or sentiment.score < -0.6:
            return {
                "adjustment_factor": 0.6,
                "rationale": "Lower intensity to prevent overwhelm. Focus on process, not performance."
            }
        elif sentiment.motivation_level == 'low':
            return {
                "adjustment_factor": 0.8,
                "rationale": "Moderate reduction. Start with confidence-building activities."
            }
        elif sentiment.motivation_level == 'high':
            return {
                "adjustment_factor": 1.2,
                "rationale": "Can handle higher intensity. Great energy today!"
            }
        else:
            return {
                "adjustment_factor": 1.0,
                "rationale": "Standard intensity maintained."
            }

    def _generate_message(self, sentiment: SentimentResult, interventions: Dict) -> str:
        """Generate authentic, non-toxic motivational message"""
        if sentiment.depression_risk:
            return "Today might feel challenging, and that's okay. Movement is medicine - let's start small and gentle."

        if sentiment.score < -0.6:
            return "You're going through something. I'm here to support, not push. Let's adjust today's plan."

        if sentiment.motivation_level == 'low':
            return "Motivation dips happen. You don't need to be perfect - showing up is what matters."

        if sentiment.motivation_level == 'high':
            return "Your energy is amazing! Let's channel that into today's session."

        return "You've got this. Let's make today count!"

    def _recommend_cbt_framework(self, sentiment: SentimentResult) -> str:
        """Recommend specific CBT technique"""
        if sentiment.depression_risk:
            return "Behavioral Activation: Focus on small, achievable actions"
        elif sentiment.score < -0.5:
            return "Thought Challenging: Question and reframe negative beliefs"
        elif sentiment.motivation_level == 'low':
            return "Goal Setting: Create specific, measurable, achievable goals"
        else:
            return "Positive Reinforcement: Celebrate progress and build momentum"


# Singleton instance
_motivation_engine = None

def get_motivation_engine() -> MotivationEngine:
    """Get or create global motivation engine instance"""
    global _motivation_engine
    if _motivation_engine is None:
        _motivation_engine = MotivationEngine()
    return _motivation_engine


# For testing
if __name__ == "__main__":
    engine = MotivationEngine()

    # Test cases
    test_feedback = [
        "I'm feeling terrible, hopeless, like nothing works anymore",
        "Great! Excited to exercise today!",
        "Feeling tired, might skip today",
        None
    ]

    for feedback in test_feedback:
        result = engine.analyze_and_recommend({}, feedback)
        print(f"\nFeedback: {feedback}")
        print(f"Sentiment: {result['sentiment_analysis']}")
        print(f"Message: {result['motivational_message']}")

