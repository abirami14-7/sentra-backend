from datetime import datetime, timedelta
from math import radians, sin, cos, asin, sqrt
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.anomaly import AnomalyEvent
from app.models.trip import SafetyTrip, TripLocation
from app.services import baseline_service


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))


def detect(db: Session, trip: SafetyTrip, current_location: Optional[TripLocation] = None) -> List[AnomalyEvent]:
    events: List[AnomalyEvent] = []
    baseline = baseline_service.compute_baseline(db, trip.user_id)

    locations = (
        db.query(TripLocation)
        .filter(TripLocation.trip_id == trip.id)
        .order_by(TripLocation.recorded_at.asc())
        .all()
    )

    now = datetime.utcnow()

    if baseline["median_duration_min"] and trip.started_at:
        elapsed_min = (now - trip.started_at).total_seconds() / 60.0
        threshold = baseline["median_duration_min"] * 1.6 + 10
        if elapsed_min > threshold:
            dev = min(1.0, (elapsed_min - threshold) / max(threshold, 1))
            events.append(
                AnomalyEvent(
                    user_id=trip.user_id,
                    trip_id=trip.id,
                    anomaly_type="TIME_DEVIATION",
                    severity="MEDIUM" if dev < 0.5 else "HIGH",
                    deviation_score=round(dev, 3),
                    description=(
                        f"Trip has been active for {int(elapsed_min)} min, "
                        f"which is significantly longer than your usual "
                        f"{int(baseline['median_duration_min'])} min."
                    ),
                )
            )

    if len(locations) >= 3:
        last = locations[-1]
        window_start = last.recorded_at - timedelta(minutes=10)
        recent = [l for l in locations if l.recorded_at >= window_start]
        if len(recent) >= 3:
            spread = max(
                haversine_m(r.latitude, r.longitude, recent[0].latitude, recent[0].longitude)
                for r in recent
            )
            gap_min = (last.recorded_at - recent[0].recorded_at).total_seconds() / 60.0
            if spread < 30 and gap_min > 5:
                score = min(1.0, gap_min / 30.0)
                events.append(
                    AnomalyEvent(
                        user_id=trip.user_id,
                        trip_id=trip.id,
                        anomaly_type="PROLONGED_STOP",
                        severity="MEDIUM" if score < 0.6 else "HIGH",
                        deviation_score=round(score, 3),
                        description=(
                            f"No significant movement detected for "
                            f"{int(gap_min)} minutes."
                        ),
                    )
                )

    if current_location and locations:
        avg_lat = sum(l.latitude for l in locations) / len(locations)
        avg_lon = sum(l.longitude for l in locations) / len(locations)
        dist = haversine_m(
            current_location.latitude, current_location.longitude, avg_lat, avg_lon
        )
        if dist > 5000:
            score = min(1.0, dist / 20000.0)
            events.append(
                AnomalyEvent(
                    user_id=trip.user_id,
                    trip_id=trip.id,
                    anomaly_type="ROUTE_DEVIATION",
                    severity="MEDIUM" if score < 0.6 else "HIGH",
                    deviation_score=round(score, 3),
                    description=(
                        f"Current position is {int(dist)} m away from the average "
                        f"path of this trip."
                    ),
                )
            )

    for e in events:
        db.add(e)
    if events:
        db.commit()
        for e in events:
            db.refresh(e)

    return events


def list_for_trip(db: Session, trip_id: int) -> List[AnomalyEvent]:
    return (
        db.query(AnomalyEvent)
        .filter(AnomalyEvent.trip_id == trip_id)
        .order_by(AnomalyEvent.detected_at.desc())
        .all()
    )


def respond(db: Session, anomaly: AnomalyEvent, response: str) -> AnomalyEvent:
    anomaly.user_response = response
    anomaly.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(anomaly)
    return anomaly
