from typing import List

from pydantic import BaseModel


class DailyRiskPoint(BaseModel):
    day: str
    avg_score: float
    samples: int


class AnalyticsSummary(BaseModel):
    total_trips: int
    alerts_received: int
    avg_risk_score: float
    safe_trips_pct: float
    daily: List[DailyRiskPoint]
