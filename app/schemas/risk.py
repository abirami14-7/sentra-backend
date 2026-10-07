from typing import List

from pydantic import BaseModel, Field


class RiskContext(BaseModel):
    hour: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    area_type: str = Field(
        ...,
        pattern="^(residential|commercial|isolated|transit_hub|industrial)$",
    )
    journey_type: str = Field(
        ...,
        pattern="^(walk|public_transport|cab|solo_car|shared_ride)$",
    )
    incident_density_7d: float = Field(..., ge=0, le=100)
    incident_severity_avg: float = Field(..., ge=1, le=5)
    lighting_score: float = Field(..., ge=0, le=1)
    transit_access: float = Field(..., ge=0, le=1)
    crowd_density: float = Field(..., ge=0, le=1)
    route_length_km: float = Field(..., gt=0, le=100)
    user_baseline_deviation: float = Field(0.0, ge=0, le=1)
    is_solo: bool = True
    has_live_share: bool = False


class RiskFactorOut(BaseModel):
    factor: str
    contribution: float
    direction: str


class RiskPredictionOut(BaseModel):
    risk_score: int
    risk_level: str
    confidence: int
    model_confidence: int
    evidence_score: int
    factors: List[RiskFactorOut]
    model_name: str
    model_version: str
