from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    area: str = Field(..., min_length=1, max_length=120)
    incident_type: str = Field(..., min_length=1, max_length=64)
    description: str = Field(..., min_length=1, max_length=2000)
    reporter_name: Optional[str] = Field(None, max_length=120)


class ReportOut(BaseModel):
    id: int
    reporter_name: str
    area: str
    incident_type: str
    description: str
    validations: int
    reported_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    area: str = Field(..., min_length=1, max_length=120)
    distance_km: float = Field(1.0, ge=0, le=100)
    icon_key: Optional[str] = "people_alt"
    color_hex: Optional[str] = "#6D28D9"


class GroupOut(BaseModel):
    id: int
    name: str
    area: str
    distance_km: float
    icon_key: str
    color_hex: str
    member_count: int
    joined: bool = False

    model_config = ConfigDict(from_attributes=True)
