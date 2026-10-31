from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ProjectCreate(BaseModel):
    name: str
    type: str = "Vivienda"
    location: str | None = None
    designer: str | None = None
    iga: int = 40
    description: str | None = None
    data: dict[str, Any] = {}


class ProjectUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    location: str | None = None
    designer: str | None = None
    iga: int | None = None
    description: str | None = None
    data: dict[str, Any] | None = None


class ProjectOut(BaseModel):
    id: int
    name: str
    type: str
    location: str | None = None
    designer: str | None = None
    iga: int
    description: str | None = None
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
