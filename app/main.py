from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import Session, select, and_
from typing import List, Optional
from datetime import datetime, timezone
from .database import init_db, get_session
from . import crud, auth, schemas
from .models import User, Space, Reservation
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Sirius Arena")

@app.on_event("startup")
def on_startup():
    init_db()
    with next(get_session()) as s:
        admin = s.exec(select(User).where(User.username == "admin")).first()
        if not admin:
            from .auth import get_password_hash
            u = User(username="admin", hashed_password=get_password_hash("admin"), role="admin")
            s.add(u)
            s.commit()

@app.post("/token", response_model=schemas.Token)
def login_for_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"access_token": auth.create_access_token(data={"sub": user.username}), "token_type": "bearer"}

@app.get("/spaces", response_model=List[schemas.SpaceRead])
def list_spaces(session: Session = Depends(get_session)):
    return session.exec(select(Space)).all()

@app.post("/spaces", response_model=schemas.SpaceRead, status_code=201)
def create_space(data: schemas.SpaceCreate, session: Session = Depends(get_session), admin: User = Depends(auth.require_admin)):
    return crud.create_space(session, data.name, data.capacity, data.equipment)

@app.post("/reservations", response_model=schemas.ReservationRead, status_code=201)
def create_reservation(data: schemas.ReservationCreate, session: Session = Depends(get_session), user: User = Depends(auth.get_current_user)):
    return crud.create_reservation(session, data.space_id, data.start_at, data.end_at, user.username)

@app.post("/users/signup", status_code=201)
def signup(username: str, password: str, session: Session = Depends(get_session)):
    user = User(username=username, hashed_password=auth.get_password_hash(password), role="user")
    session.add(user); session.commit(); session.refresh(user)
    return {"username": user.username}

# Путь к статике (проверенная версия)
script_dir = os.path.dirname(__file__)
static_path = os.path.join(script_dir, "static")

if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def read_index():
    index_file = os.path.join(static_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"error": "Файл index.html не найден в папке app/static"}