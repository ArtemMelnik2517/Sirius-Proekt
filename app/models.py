from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from datetime import datetime

class SpaceBase(SQLModel):
    name: str
    capacity: int
    equipment: List[str] = Field(default=[], sa_column=Column(JSON))

class Space(SpaceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reservations: List["Reservation"] = Relationship(back_populates="space")

class ReservationBase(SQLModel):
    start_at: datetime
    end_at: datetime
    user_name: str

class Reservation(ReservationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    space_id: int = Field(foreign_key="space.id")
    status: str = Field(default="active")
    space: Optional[Space] = Relationship(back_populates="reservations")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str = Field(default="user")