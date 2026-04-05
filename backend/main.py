from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from api import users, auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SportRX AI",
    description="AI-powered exercise prescription for chronic disease management",
    version="1.0.0",
)

# ✅ CORS — autorise le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
 )

app.include_router(users.router)
app.include_router(auth_router.router)

@app.get("/", tags=["Health"])
def root():
    return {"status": "SportRX API is running 🚀"}
