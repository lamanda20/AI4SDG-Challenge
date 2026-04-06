from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import crud, schemas
from database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/admin", response_model=schemas.UserResponse, status_code=201)
def create_admin(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, admin.email):
        raise HTTPException(status_code=400, detail="Email already exists.")
    return crud.create_admin(db=db, admin=admin)


@router.post("/client", response_model=schemas.ClientResponse, status_code=201)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, client.email):
        raise HTTPException(status_code=400, detail="Email already exists.")
    return crud.create_client(db=db, client=client)


@router.get("/", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    return crud.get_all_users(db=db)


@router.get("/clients", response_model=List[schemas.ClientResponse])
def list_clients(db: Session = Depends(get_db)):
    return crud.get_all_clients(db=db)


@router.get("/{user_id}", response_model=schemas.ClientResponse)
def get_client(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_client(db=db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return user


@router.put("/{user_id}/biometrics", response_model=schemas.BiometricsResponse)
def update_biometrics(user_id: int, bio: schemas.BiometricsCreate, db: Session = Depends(get_db)):
    result = crud.update_biometrics(db=db, user_id=user_id, bio=bio)
    if not result:
        raise HTTPException(status_code=404, detail="Biometrics not found.")
    return result
