from datetime import datetime
from statistics import median
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.trip import SafetyTrip

MIN_TRIPS_FOR_BASELINE = 3


def compute_baseline(db: Session, user_id: int) -> Dict:
    trips = (
        db.query(SafetyTrip)
        .filter(
            SafetyTrip.user_id == user_id,
            SafetyTrip.ended_at.isnot(None),
        )
        .order_by(SafetyTrip.started_at.desc())
        .limit(30)
        .all()
    )

    durations = []
    start_hours = []
    origins = []
    destinations = []

    for t in trips:
        if t.ended_at and t.started_at:
            durations.append((t.ended_at - t.started_at).total_seconds() / 60.0)
        start_hours.append(t.started_at.hour)
        origins.append(t.origin)
        destinations.append(t.destination)

    count = len(trips)
    has_enough = count >= MIN_TRIPS_FOR_BASELINE

    return {
        "trip_count": count,
        "has_enough_data": has_enough,
        "median_duration_min": median(durations) if durations else None,
        "median_start_hour": median(start_hours) if start_hours else None,
        "common_origins": list({o for o in origins})[:5],
        "common_destinations": list({d for d in destinations})[:5],
    }


def is_known_route(baseline: Dict, origin: str, destination: str) -> bool:
    if not baseline["has_enough_data"]:
        return True
    return (
        origin in baseline["common_origins"]
        and destination in baseline["common_destinations"]
    )
