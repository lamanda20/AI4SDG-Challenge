from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import init_db

load_dotenv()

from api.auth import router as auth_router
from api.profile import router as profile_router
from api.checkin import router as checkin_router
from api.admin import router as admin_router
from admin_bootstrap import ensure_admin_account

app = FastAPI(title="SportRX AI — Health Coach", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(checkin_router)
app.include_router(admin_router)

@app.on_event("startup")
def startup():
    init_db()
    ensure_admin_account()

@app.get("/health")
def health():
    return {"status": "ok"}
