"""
SportRX AI - Main FastAPI Application

Multi-agent medical coaching platform combining exercise science and AI.
This application coordinates:
  - RAG Medical Engine (Abd elghani): Receives risk_assessment → Returns medical_guidelines
  - Coach Agent (Soufia): Receives medical_guidelines → Returns coaching_plan
  - ML Agent (Taha): Receives patient_data → Returns risk_assessment
  - Motivator Agent: Receives coaching_plan → Returns enhanced_coaching_with_motivation
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from backend.api.medical_guidelines import router as rag_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifespan manager

    Handles startup and shutdown events
    """
    logger.info("Starting SportRX AI application...")
    yield
    logger.info("Shutting down SportRX AI application...")


# Create FastAPI app
app = FastAPI(
    title="SportRX AI - Medical Exercise Coaching Platform",
    description="AI-powered chronic disease management platform combining exercise science and multi-agent AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "application": "SportRX AI",
        "version": "1.0.0",
        "description": "AI-powered chronic disease management platform",
        "endpoints": {
            "rag_medical_engine": "/api/rag/medical-guidelines (POST)",
            "health_check": "/api/rag/health (GET)",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


# Health check endpoint
@app.get("/health")
async def health():
    """Basic health check"""
    return {"status": "healthy", "service": "SportRX AI"}


# Include routers
app.include_router(rag_router)


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
