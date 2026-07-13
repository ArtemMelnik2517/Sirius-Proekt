from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class SpaceCreate(BaseModel):
    name: str
    capacity: int
    equipment: Optional[List[str]] = []

class SpaceRead(SpaceCreate):
    id: int

class ReservationCreate(BaseModel):
    space_id: int
    start_at: datetime
    end_at: datetime
    user_name: str

class ReservationRead(ReservationCreate):
    id: int
    status: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
