import hashlib
import os

from database import SessionLocal
from crud import get_user_by_email, create_admin


def ensure_admin_account():
    admin_email = os.getenv("ADMIN_LOGIN_EMAIL", "").strip()
    if not admin_email:
        return

    admin_password = os.getenv("ADMIN_SEED_PASSWORD", "admin123")
    admin_name = os.getenv("ADMIN_SEED_NAME", "Admin")

    db = SessionLocal()
    try:
        existing_admin = get_user_by_email(db, admin_email)
        if existing_admin:
            return

        hashed_password = hashlib.sha256(admin_password.encode()).hexdigest()
        create_admin(db, admin_name, admin_email, hashed_password)
        print(f"  ✅ Admin seeded: {admin_email}")
    finally:
        db.close()
