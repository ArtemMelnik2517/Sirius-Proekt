from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Optional
from datetime import datetime, timezone
from .database import init_db, get_session
from . import crud, auth, schemas
from .models import User
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI(title="Sirius.Arena Unique MVP")

@app.on_event("startup")
def on_startup():
    init_db()
    # seed admin if not exists
    with next(get_session()) as s:
        admin = s.exec(__import__("sqlmodel").select(User).where(User.username=="admin")).first()
        if not admin:
            from .auth import get_password_hash
            u = User(username="admin", hashed_password=get_password_hash("adminpass"), role="admin")
            s.add(u); s.commit()

@app.post("/token", response_model=schemas.Token)
def login_for_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(__import__("sqlmodel").sqlmodel.select(User).where(User.username==form_data.username)).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = auth.create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/signup", status_code=201)
def signup(username: str, password: str, session: Session = Depends(get_session)):
    exists = session.exec(__import__("sqlmodel").sqlmodel.select(User).where(User.username==username)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username exists")
    user = User(username=username, hashed_password=auth.get_password_hash(password), role="user")
    session.add(user); session.commit(); session.refresh(user)
    return {"username": user.username}

@app.post("/spaces", response_model=schemas.SpaceRead, status_code=201)
def create_space(data: schemas.SpaceCreate, session: Session = Depends(get_session), admin: User = Depends(auth.require_admin)):
    sp = crud.create_space(session, data.name, data.capacity, data.equipment)
    return sp

@app.get("/spaces", response_model=List[schemas.SpaceRead])
def list_spaces(min_capacity: Optional[int] = 0, equipment: Optional[str] = None, session: Session = Depends(get_session)):
    eq = [x.strip() for x in equipment.split(",")] if equipment else None
    return crud.list_spaces(session, min_capacity, eq)

@app.get("/spaces/{space_id}", response_model=schemas.SpaceRead)
def get_space(space_id: int, session: Session = Depends(get_session)):
    sp = crud.get_space(session, space_id)
    if not sp:
        raise HTTPException(status_code=404, detail="Space not found")
    return sp

@app.post("/reservations", response_model=schemas.ReservationRead, status_code=201)
def create_reservation(data: schemas.ReservationCreate, session: Session = Depends(get_session), user: User = Depends(auth.get_current_user)):
    if data.start_at.tzinfo is None or data.end_at.tzinfo is None:
        raise HTTPException(status_code=400, detail="Use timezone-aware datetimes (ISO8601 with Z)")
    if data.end_at <= data.start_at:
        raise HTTPException(status_code=400, detail="end_at must be after start_at")
    if data.end_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="end_at must be in the future")
    return crud.create_reservation(session, data.space_id, data.start_at, data.end_at, user.username)

@app.delete("/reservations/{res_id}")
def cancel_reservation(res_id: int, session: Session = Depends(get_session), user: User = Depends(auth.get_current_user)):
    res = crud.cancel_reservation(session, res_id, user)
    return {"detail": f"Reservation {res.id} cancelled"}

@app.get("/spaces/{space_id}/reservations", response_model=List[schemas.ReservationRead])
def list_reservations(space_id: int, date: Optional[str] = None, session: Session = Depends(get_session)):
    sp = crud.get_space(session, space_id)
    if not sp:
        raise HTTPException(status_code=404, detail="Space not found")
    stmt = __import__("sqlmodel").sqlmodel.select(__import__("app.models").Reservation).where(__import__("app.models").Reservation.space_id == space_id)
    if date:
        from datetime import date as date_c, datetime as dt, timezone
        try:
            d = date_c.fromisoformat(date)
        except:
            raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
        start_dt = dt.combine(d, dt.min.time()).replace(tzinfo=timezone.utc)
        end_dt = dt.combine(d, dt.max.time()).replace(tzinfo=timezone.utc)
        stmt = stmt.where(__import__("sqlmodel").sqlmodel.and_(__import__("app.models").Reservation.start_at >= start_dt, __import__("app.models").Reservation.start_at <= end_dt))
    results = session.exec(stmt).all()
    return results

@app.get("/my-reservations", response_model=List[schemas.ReservationRead])
def my_reservations(user: User = Depends(auth.get_current_user), session: Session = Depends(get_session)):
    stmt = __import__("sqlmodel").sqlmodel.select(__import__("app.models").Reservation).where(__import__("app.models").Reservation.user_name == user.username)
    return session.exec(stmt).all()

@app.get("/spaces/available", response_model=List[schemas.SpaceRead])
def spaces_available(start: datetime, end: datetime, capacity: Optional[int] = 0, session: Session = Depends(get_session)):
    if end <= start:
        raise HTTPException(status_code=400, detail="end must be after start")
    return [s for s in crud.list_spaces(session, capacity) if not crud.reservations_overlap(session, s.id, start, end)]

@app.get("/admin/stats")
def admin_stats(admin: User = Depends(auth.require_admin), session: Session = Depends(get_session)):
    total_spaces = session.exec(__import__("sqlmodel").sqlmodel.select(__import__("app.models").Space)).count()
    total_active = session.exec(__import__("sqlmodel").sqlmodel.select(__import__("app.models").Reservation).where(__import__("app.models").Reservation.status=="active")).count()
    return {"total_spaces": total_spaces, "active_reservations": total_active}
