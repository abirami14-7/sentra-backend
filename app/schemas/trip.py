from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TripStart(BaseModel):
    route_id: str = Field(..., min_length=1, max_length=64)
    route_name: str = Field(..., min_length=1, max_length=255)
    origin: str = Field(..., min_length=1, max_length=255)
    destination: str = Field(..., min_length=1, max_length=255)
    travel_mode: Optional[str] = Field('walking', max_length=32)
    shared_contact_ids: Optional[List[int]] = None
    notes: Optional[str] = None


class TripLocationCreate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy_m: Optional[float] = Field(None, ge=0, le=1000)
    source: str = Field("mock", max_length=32)


class TripLocationOut(BaseModel):
    id: int
    latitude: float
    longitude: float
    accuracy_m: Optional[float]
    source: str
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TripOut(BaseModel):
    id: int
    route_id: str
    route_name: str
    origin: str
    destination: str
    travel_mode: str
    shared_contact_ids: Optional[str] = None
    status: str
    privacy_state: str
    started_at: datetime
    ended_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TripWithLocations(TripOut):
    locations: List[TripLocationOut] = []
