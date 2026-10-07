from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.anomaly import AnomalyEvent
from app.models.risk_log import RiskPredictionLog
from app.models.trip import SafetyTrip
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary, DailyRiskPoint

router = APIRouter(prefix="/analytics", tags=["analytics"])

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@router.get("/summary", response_model=AnalyticsSummary)
def summary(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total_trips = (
        db.query(func.count(SafetyTrip.id))
        .filter(SafetyTrip.user_id == current.id)
        .scalar()
        or 0
    )
    alerts = (
        db.query(func.count(AnomalyEvent.id))
        .filter(AnomalyEvent.user_id == current.id)
        .scalar()
        or 0
    )
    avg_score = (
        db.query(func.avg(RiskPredictionLog.risk_score))
        .filter(RiskPredictionLog.user_id == current.id)
        .scalar()
    )
    avg_score_val = float(avg_score) if avg_score is not None else 0.0

    safe_pct = 100.0
    if total_trips > 0:
        safe_pct = max(
            0.0, min(100.0, ((total_trips - alerts) / total_trips) * 100.0)
        )

    today = datetime.utcnow().date()
    daily = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        start = datetime(day.year, day.month, day.day)
        end = start + timedelta(days=1)
        row = (
            db.query(
                func.avg(RiskPredictionLog.risk_score),
                func.count(RiskPredictionLog.id),
            )
            .filter(
                RiskPredictionLog.user_id == current.id,
                RiskPredictionLog.created_at >= start,
                RiskPredictionLog.created_at < end,
            )
            .first()
        )
        avg_day = float(row[0]) if row and row[0] is not None else 0.0
        count_day = int(row[1]) if row else 0
        daily.append(
            DailyRiskPoint(
                day=DAYS[day.weekday()],
                avg_score=round(avg_day, 1),
                samples=count_day,
            )
        )

    return AnalyticsSummary(
        total_trips=total_trips,
        alerts_received=alerts,
        avg_risk_score=round(avg_score_val, 1),
        safe_trips_pct=round(safe_pct, 1),
        daily=daily,
    )
