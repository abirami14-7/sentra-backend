from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RouteOut(BaseModel):
    id: int
    route_id: str
    name: str
    origin: str
    destination: str
    distance_km: float
    duration_min: int
    risk_score: int
    risk_level: str
    confidence: int
    is_safer: bool

    model_config = ConfigDict(from_attributes=True)


class RouteSearchRequest(BaseModel):
    origin_lat: Optional[float] = Field(None, ge=-90, le=90)
    origin_lng: Optional[float] = Field(None, ge=-180, le=180)
    origin_text: Optional[str] = Field(None, max_length=255)
    destination_text: str = Field(..., min_length=2, max_length=255)


class RouteSearchCandidate(BaseModel):
    route_id: str
    name: str
    distance_km: float
    duration_min: int
    risk_score: int
    risk_level: str
    confidence: int
    is_safer: bool
    polyline: List[List[float]]


class RouteSearchResponse(BaseModel):
    origin_lat: float
    origin_lng: float
    origin_name: str
    destination_lat: float
    destination_lng: float
    destination_name: str
    routes: List[RouteSearchCandidate]


class PlaceSuggestion(BaseModel):
    display_name: str
    short_name: str
    lat: float
    lng: float
