from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class SpaceCreate(BaseModel):
    name: str
    capacity: int
    equipment: List[str] = []

class SpaceRead(BaseModel):
    id: int
    name: str
    capacity: int
    equipment: List[str]
    class Config:
        orm_mode = True

class ReservationCreate(BaseModel):
    space_id: int
    start_at: datetime
    end_at: datetime
    user_name: str

class ReservationRead(BaseModel):
    id: int
    space_id: int
    start_at: datetime
    end_at: datetime
    user_name: str
    status: str
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"