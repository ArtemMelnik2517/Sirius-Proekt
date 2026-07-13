from sqlmodel import Session, select
from datetime import datetime
from .models import Space, Reservation, User
from fastapi import HTTPException, status

def create_space(session: Session, name: str, capacity: int, equipment: list):
    space = Space(name=name, capacity=capacity, equipment=equipment)
    session.add(space)
    session.commit()
    session.refresh(space)
    return space

def get_space(session: Session, space_id: int):
    return session.get(Space, space_id)

def list_spaces(session: Session, min_capacity: int = 0, equipment: list | None = None):
    q = select(Space)
    if min_capacity:
        q = q.where(Space.capacity >= min_capacity)
    results = session.exec(q).all()
    if equipment:
        wanted = [e.lower() for e in equipment]
        def match(s):
            eqs = [x.lower() for x in (s.equipment or [])]
            return all(w in eqs for w in wanted)
        results = [s for s in results if match(s)]
    return results

def reservations_overlap(session: Session, space_id: int, start: datetime, end: datetime):
    stmt = select(Reservation).where(
        Reservation.space_id == space_id,
        Reservation.status == "active",
        Reservation.start_at < end,
        Reservation.end_at > start
    )
    return session.exec(stmt).first()

def create_reservation(session: Session, space_id: int, start: datetime, end: datetime, user_name: str):
    if end <= start:
        raise HTTPException(status_code=400, detail="end must be after start")
    if reservations_overlap(session, space_id, start, end):
        raise HTTPException(status_code=409, detail="Space already reserved for given interval")
    res = Reservation(space_id=space_id, start_at=start, end_at=end, user_name=user_name)
    session.add(res)
    session.commit()
    session.refresh(res)
    return res

def cancel_reservation(session: Session, res_id: int, requester: User):
    res = session.get(Reservation, res_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if requester.role != "admin" and requester.username != res.user_name:
        raise HTTPException(status_code=403, detail="Cannot cancel other's reservation")
    res.status = "cancelled"
    session.add(res)
    session.commit()
    return res
