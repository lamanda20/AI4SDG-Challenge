# SportRX AI — Intelligent Health Coach

> AI-powered chronic disease management platform built for the AI4SDG Challenge.
> Combines predictive ML, RAG-based medical retrieval, and an LLM coaching agent to deliver personalized exercise prescriptions.

---

## Overview

SportRX AI helps patients with chronic conditions (diabetes, hypertension, obesity) receive safe, adaptive exercise plans backed by clinical evidence. The system analyzes biometric data, predicts health risks, retrieves relevant medical literature, and generates personalized coaching advice through a conversational AI.

**SDG Alignment:** SDG 3 — Good Health and Well-Being

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                    │
│  Login · Register · Dashboard · Exercise Plan · Profile │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────┐
│                  Backend (FastAPI)                       │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │  ML Module  │  │  RAG Module │  │   LLM Agents   │  │
│  │ Risk model  │  │ PubMed docs │  │ Clinician RAG  │  │
│  │ Sentiment   │  │ Embeddings  │  │ Motivator ML   │  │
│  │ CBT engine  │  │ Retriever   │  │ Prescriber LLM │  │
│  └─────────────┘  └─────────────┘  └────────────────┘  │
│                                                         │
│  Auth · User Profiles · Check-ins · Admin Dashboard     │
└──────────────────────────────────────────────────────────┘
                       │
               SQLite / PostgreSQL
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| ML | XGBoost, scikit-learn, NLTK, NumPy |
| RAG | Sentence Transformers, Pinecone, PyPDF2 |
| LLM | Groq API |
| Auth | JWT (PyJWT) |
| Database | SQLite (dev) / PostgreSQL (prod) |

---

## Project Structure

```
AI4SDG-Challenge/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   ├── crud.py                  # Database operations
│   ├── database.py              # DB connection
│   ├── auth.py                  # JWT authentication
│   ├── api/
│   │   ├── auth.py              # /auth endpoints
│   │   ├── profile.py           # /profile endpoints
│   │   ├── checkin.py           # /checkin endpoints
│   │   ├── admin.py             # /admin endpoints
│   │   ├── coaching.py          # /coaching endpoints
│   │   └── ml_routes.py         # /ml endpoints
│   ├── ml/
│   │   ├── pipeline.py          # ML orchestrator
│   │   ├── risk_model.py        # Risk prediction (4 dimensions)
│   │   ├── sentiment_analysis.py# Sentiment + CBT framework
│   │   └── contracts.py         # Input/output schemas
│   ├── agents/
│   │   ├── clinician_rag.py     # RAG-based clinical agent
│   │   ├── motivator_ml.py      # ML-driven motivation agent
│   │   └── prescriber_llm.py    # LLM exercise prescriber
│   └── services/
│
├── rag/
│   ├── indexer.py               # Document indexing
│   ├── retriever.py             # Semantic retrieval
│   ├── downloader.py            # PubMed/document fetcher
│   └── documents/               # Indexed medical documents
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── Register.tsx
│       │   ├── Dashboard.tsx
│       │   ├── ExercisePlan.tsx
│       │   ├── Profile.tsx
│       │   ├── OnBoarding.tsx
│       │   └── AdminDashboard.tsx
│       ├── components/
│       └── services/            # API client calls
│
├── docs/                        # Technical documentation
├── requirements.txt
└── .env                         # Environment variables (not committed)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [Groq](https://console.groq.com) API key (free)
- Optional: Pinecone API key for RAG vector store

### Backend Setup

```bash
# Clone the repo
git clone https://github.com/<your-org>/AI4SDG-Challenge.git
cd AI4SDG-Challenge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start the API server
cd backend
uvicorn main:app --reload --port 8000
```

API available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`

---

## Environment Variables

```env
# Required
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_jwt_secret

# Optional (RAG vector store)
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=sportrx-medical

# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./sportrx.db
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT token |

### User
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/PUT | `/profile` | User profile |
| POST | `/checkin` | Daily biometric check-in |

### AI / ML
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ml/analyze` | Full ML pipeline |
| POST | `/api/ml/risk-only` | Risk assessment only |
| POST | `/api/ml/sentiment-only` | Sentiment analysis only |
| GET | `/api/ml/health` | ML module health check |
| POST | `/coaching` | AI coaching session |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/users` | List all users |
| GET | `/admin/stats` | Platform statistics |

---

## ML Pipeline

The ML module processes a user profile and returns a structured risk + sentiment assessment:

**Input:** biometrics (BMI, blood pressure, HbA1c, etc.), exercise history, optional free-text feedback

**Output:**
```json
{
  "risk_assessment": {
    "risk_score": 39.1,
    "risk_level": "moderate",
    "progression_risk": 40.4,
    "adherence_risk": 90.0,
    "injury_risk": 22.0
  },
  "sentiment_analysis": {
    "sentiment_label": "neutral",
    "motivation_level": "medium",
    "depression_risk_indicator": false,
    "cbt_intervention_needed": false
  },
  "recommended_exercise_intensity": "moderate",
  "warnings": ["High non-adherence risk. Plan motivational checkpoints."]
}
```

---

## Running Tests

```bash
# Quick ML test
python direct_test.py

# Full test suite (7 tests)
python test_ml_comprehensive.py

# Setup verification
python verify_setup.py
```

---

## Team

| Member | Role |
|--------|------|
| Taha | ML module (risk model, sentiment, CBT) |
| Zineb | Backend architecture & API |
| Soufia | LLM coaching agent |

---

## License

MIT
