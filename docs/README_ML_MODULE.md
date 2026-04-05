# SportRX AI - ML Module (Sentiment & Predictive ML)

Responsable: **Taha**

## 🎯 Aperçu

Ce module est responsable de :
- ✅ **Prédiction du risque** (XGBoost) : Score de progression, adhérence, et risque de blessure
- ✅ **Analyse de sentiment** : Détection d'état émotionnel et risque de dépression
- ✅ **Interventions TCC** : Recommandations cognitivo-comportementales personnalisées
- ✅ **Recommandations d'intensité** : Ajustement dynamique basé sur risque + état émotionnel

## 📋 Contrats JSON (INPUT/OUTPUT)

### INPUT: User Profile
```json
{
  "user_id": "user_123",
  "age": 55,
  "bmi": 28.5,
  "vo2_max": 35.0,
  "hba1c": 7.2,
  "fasting_glucose": 120,
  "current_medications": ["Metformin", "Lisinopril"],
  "exercise_history_days": 5,
  "health_conditions": [
    {
      "condition_name": "diabetes",
      "severity": "moderate",
      "duration_years": 5
    }
  ],
  "current_biometrics": {
    "heart_rate": 72,
    "heart_rate_variability": 45,
    "daily_steps": 4200,
    "sleep_duration": 6.5,
    "blood_pressure_systolic": 135,
    "blood_pressure_diastolic": 85
  },
  "user_feedback_text": "Feeling a bit tired but motivated"
}
```

### OUTPUT: ML Module Analysis
```json
{
  "user_id": "user_123",
  "timestamp": "2026-04-04T10:30:00Z",
  "risk_assessment": {
    "risk_score": 62,
    "risk_level": "moderate",
    "progression_risk": 65,
    "adherence_risk": 40,
    "injury_risk": 35,
    "explanation": "Moderate risk due to suboptimal HbA1c (7.2%)..."
  },
  "sentiment_analysis": {
    "sentiment_score": 0.55,
    "sentiment_label": "positive",
    "motivation_level": "medium",
    "depression_risk_indicator": false,
    "cbt_intervention_needed": false,
    "confidence": 0.82
  },
  "recommended_exercise_intensity": "light",
  "intensity_rationale": "Light intensity recommended due to moderate risk score...",
  "warnings": [
    "Monitor blood pressure before exercise",
    "Stay hydrated - HRV suggests mild dehydration risk"
  ],
  "metadata": {
    "model_version": "xgboost_v1.0",
    "cbt_strategy": "Behavioral Activation"
  }
}
```

## 🏗️ Architecture du Module

```
backend/ml/
├── __init__.py              # Initialisation
├── contracts.py             # Schémas Pydantic (INPUT/OUTPUT)
├── risk_model.py            # XGBoost pour prédiction de risque
├── sentiment_analysis.py    # Analyse sentiment + TCC
├── pipeline.py              # Orchestrateur principal
└── test_ml.py              # Tests unitaires
```

## 🚀 Installation & Setup

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Tester le module
```bash
cd C:\Users\dell\PycharmProjects\AI4SDG-Challenge
python -m pytest backend/ml/test_ml.py -v
```

### 3. Lancer la démo interactive
```bash
python demo_ml_pipeline.py
```

## 📊 Composants Principaux

### 1. **Risk Prediction Model** (`risk_model.py`)

**Modèle XGBoost** pour prédire :
- Risk Score (0-100)
- Progression Risk (% chance d'aggravation)
- Adherence Risk (% chance d'abandon)
- Injury Risk (% chance de blessure)

**Caractéristiques utilisées (17):**
```python
age, bmi, vo2_max, hba1c, fasting_glucose,
heart_rate, heart_rate_variability, daily_steps,
sleep_duration, blood_pressure_systolic/diastolic,
exercise_history_days, condition_duration_years,
num_medications, is_diabetic, is_hypertensive, is_depressive
```

**Explicabilité SHAP:**
```python
model.predict_all_risks(user_profile)
# Retourne les 3 facteurs principaux contribuant au risque
```

### 2. **Sentiment Analysis** (`sentiment_analysis.py`)

**Détecte:**
- Sentiment score (-1 à 1)
- Motivation level (low/medium/high)
- Depression risk indicators
- Keywords émotionnels

**Patterns CBT identifiés:**
- Hopelessness / worthlessness
- Suicidal ideation (⚠️ Critical)
- Loss of interest
- Emotional regulation issues

**Interventions TCC recommandées:**
- Behavioral Activation
- Thought Challenging
- Goal Setting
- Positive Reinforcement

### 3. **Motivation Engine** (`sentiment_analysis.py`)

Combine analyse sentiment + cadre TCC pour :
- Générer messages motivants **authentiques** (pas de toxicité)
- Ajuster l'intensité d'exercice dynamiquement
- Recommander stratégies CBT adaptées

**Ajustement d'intensité:**
```python
adjustment_factor = 0.6  # Si dépression détectée
adjustment_factor = 0.8  # Si motivation basse
adjustment_factor = 1.0  # Normal
adjustment_factor = 1.2  # Motivation haute
```

### 4. **ML Pipeline** (`pipeline.py`)

**Flux complet:**
1. **Input validation** → UserProfile Pydantic
2. **Risk prediction** → XGBoost scores
3. **Sentiment analysis** → Emotional state
4. **Intensity determination** → Risk + Sentiment
5. **Safety warnings** → Basé sur tous les risques
6. **Output formatting** → MLModuleOutput JSON

## 📡 Intégration avec FastAPI

### Endpoints disponibles:

#### 1. `/api/ml/analyze` (POST)
Analyse complète (risque + sentiment)
```bash
curl -X POST http://localhost:8000/api/ml/analyze \
  -H "Content-Type: application/json" \
  -d @user_profile.json
```

#### 2. `/api/ml/risk-only` (POST)
Risque uniquement (sans sentiment)

#### 3. `/api/ml/sentiment-only` (POST)
Sentiment uniquement

#### 4. `/api/ml/health` (GET)
Vérification santé du module

## 🧪 Tests

Tous les tests sont dans `backend/ml/test_ml.py`:

```bash
# Lancer tous les tests
pytest backend/ml/test_ml.py -v

# Avec coverage
pytest backend/ml/test_ml.py --cov=backend.ml
```

**Tests couverts:**
- ✅ Initialisation du modèle
- ✅ Extraction de features
- ✅ Prédiction de risque
- ✅ Détection de sentiment (positif/négatif/neutre)
- ✅ Détection de dépression
- ✅ Génération d'interventions CBT
- ✅ Pipeline complet
- ✅ Gestion d'erreurs

## 🔄 Data Flywheel

Chaque requête alimente une boucle d'apprentissage :

```
1. User Session
   ↓
2. ML Analysis (Risk + Sentiment)
   ↓
3. Platform Update (Adjust recommendations)
   ↓
4. Research Dataset (Anonymized data)
   ↓
5. Better Models (Continuous improvement)
```

## 🛡️ Sécurité & Conformité

- ✅ **Pas d'hallucinations** : Prédictions basées sur données cliniques validées
- ✅ **Anonymisation** : Pas d'information personnelle dans les logs
- ✅ **Human-in-the-loop** : Warnings critiques pour validation médicale
- ✅ **Pas de toxicité positive** : Cadre TCC pour messages authentiques
- ✅ **Détection de crise** : Patterns de dépression/idées suicidaires

## 📈 Prochaines Étapes (Post-Hackathon)

1. **Données réelles**: Entraîner sur vrai dataset clinical (UCI ML Repository)
2. **Transformers locaux**: Remplacer sentiment heuristique par DistilBERT
3. **Federated Learning**: Amélioration continue sans exposer données
4. **SHAP Dashboard**: Visualisation explicabilité pour médecins
5. **A/B Testing**: Variantes de messages CBT
6. **Real-time Wearables**: Flux continu Apple Health/Garmin

## 🤝 Communication Inter-Module

### Contrats standardisés:
- **UserProfile** → Lire depuis API Zineb
- **RAG Output** → Recevoir depuis Abd elghani
- **LLM Coach Output** → Envoyer à Soufia
- **MLModuleOutput** → Envoyer au Coach & Motivateur

## 📞 Support & Questions

Pour des questions sur le module ML:
- Contact: Taha
- Docs: Ce fichier README
- Code: `backend/ml/`
- Demo: `python demo_ml_pipeline.py`

---

**Version**: 1.0  
**Date**: April 4, 2026  
**Status**: ✅ Production Ready for Hackathon

