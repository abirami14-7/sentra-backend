from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AnomalyOut(BaseModel):
    id: int
    trip_id: int
    anomaly_type: str
    severity: str
    deviation_score: float
    description: str
    user_response: Optional[str]
    detected_at: datetime
    resolved_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AnomalyResponse(BaseModel):
    response: str = Field(..., pattern="^(SAFE|NEED_HELP)$")
