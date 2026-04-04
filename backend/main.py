from fastapi import FastAPI
from fastapi import Response
from database import engine, Base
from api import users

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SportRX AI",
    description="AI-powered exercise prescription for chronic disease management",
    version="1.0.0",
)

app.include_router(users.router)

@app.get("/", tags=["Health"])
def root():
    return {"status": "SportRX API is running 🚀"}
    
