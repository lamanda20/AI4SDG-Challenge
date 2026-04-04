from sqlalchemy.orm import Session
from models import User, Admin, Client, Biometrics, ExerciseSession
import schemas


# ─────────────────────────────────────────
# USER
# ─────────────────────────────────────────

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_all_users(db: Session):
    return db.query(User).all()


# ─────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────

def create_admin(db: Session, admin: schemas.AdminCreate):
    db_admin = Admin(
        name=admin.name,
        email=admin.email,
        hashed_password=admin.password,  # à hasher plus tard avec bcrypt
        role="admin",
        can_manage_users=admin.can_manage_users,
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin


# ─────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────

def create_client(db: Session, client: schemas.ClientCreate):
    db_client = Client(
        name=client.name,
        email=client.email,
        hashed_password=client.password,  # à hasher plus tard
        role="client",
        age=client.age,
        gender=client.gender,
        chronic_condition=client.chronic_condition,
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)

    db_bio = Biometrics(
        user_id=db_client.id,
        **client.biometrics.model_dump()
    )
    db.add(db_bio)
    db.commit()
    db.refresh(db_client)
    return db_client

def get_all_clients(db: Session):
    return db.query(Client).filter(Client.role == "client").all()

def get_client(db: Session, user_id: int):
    return db.query(Client).filter(Client.id == user_id).first()


# ─────────────────────────────────────────
# BIOMETRICS
# ─────────────────────────────────────────

def update_biometrics(db: Session, user_id: int, bio: schemas.BiometricsCreate):
    db_bio = db.query(Biometrics).filter(Biometrics.user_id == user_id).first()
    if not db_bio:
        return None
    for field, value in bio.model_dump(exclude_unset=True).items():
        setattr(db_bio, field, value)
    db.commit()
    db.refresh(db_bio)
    return db_bio
