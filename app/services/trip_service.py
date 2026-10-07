from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.trip import SafetyTrip, TripLocation
from app.schemas.trip import TripLocationCreate, TripStart
from app.services import (
    audit_service,
    baseline_service,
    consent_service,
    privacy_state,
)


def _serialize_contact_ids(ids: Optional[List[int]]) -> Optional[str]:
    if not ids:
        return None
    return ",".join(str(int(i)) for i in ids)


def start_trip(db: Session, user_id: int, payload: TripStart) -> SafetyTrip:
    consent_service.ensure_defaults(db, user_id)

    trip = SafetyTrip(
        user_id=user_id,
        route_id=payload.route_id,
        route_name=payload.route_name,
        origin=payload.origin,
        destination=payload.destination,
        travel_mode=(payload.travel_mode or "walking"),
        shared_contact_ids=_serialize_contact_ids(payload.shared_contact_ids),
        status="TRIP_ACTIVE",
        privacy_state=privacy_state.PrivacyState.TRIP_ACTIVE.value,
        started_at=datetime.utcnow(),
        notes=payload.notes,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    audit_service.record(
        db,
        user_id=user_id,
        trip_id=trip.id,
        resource_type="TRIP",
        action="TRIP_STARTED",
        status="ALLOWED",
        privacy_state=trip.privacy_state,
        detail=(
            f"Route {trip.route_id} from {trip.origin} to {trip.destination} "
            f"via {trip.travel_mode}"
        ),
    )
    return trip


def get_active(db: Session, user_id: int) -> Optional[SafetyTrip]:
    return (
        db.query(SafetyTrip)
        .filter(
            SafetyTrip.user_id == user_id,
            SafetyTrip.status.in_(
                ["TRIP_ACTIVE", "ANOMALY_DETECTED", "EMERGENCY_ACTIVE"]
            ),
        )
        .order_by(SafetyTrip.started_at.desc())
        .first()
    )


def get_by_id(db: Session, user_id: int, trip_id: int) -> Optional[SafetyTrip]:
    return (
        db.query(SafetyTrip)
        .filter(SafetyTrip.id == trip_id, SafetyTrip.user_id == user_id)
        .first()
    )


def list_history(db: Session, user_id: int, limit: int = 50) -> List[SafetyTrip]:
    return (
        db.query(SafetyTrip)
        .filter(SafetyTrip.user_id == user_id)
        .order_by(SafetyTrip.started_at.desc())
        .limit(limit)
        .all()
    )


def add_location(
    db: Session, trip: SafetyTrip, payload: TripLocationCreate
) -> TripLocation:
    granted = consent_service.is_granted(db, trip.user_id, "GPS")
    if not granted:
        audit_service.record(
            db,
            user_id=trip.user_id,
            trip_id=trip.id,
            resource_type="GPS",
            action="WRITE_LOCATION",
            status="DENIED (no consent)",
            privacy_state=trip.privacy_state,
            detail="Location rejected because GPS consent is not granted.",
        )
        raise PermissionError("GPS consent is not granted for this user.")

    allowed = privacy_state.allowed_resources(trip.privacy_state)
    if "GPS" not in allowed:
        audit_service.record(
            db,
            user_id=trip.user_id,
            trip_id=trip.id,
            resource_type="GPS",
            action="WRITE_LOCATION",
            status=f"DENIED (state={trip.privacy_state})",
            privacy_state=trip.privacy_state,
            detail="Location rejected because the privacy state does not permit GPS.",
        )
        raise PermissionError("Privacy state does not permit GPS access.")

    loc = TripLocation(
        trip_id=trip.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_m=payload.accuracy_m,
        source=payload.source,
        recorded_at=datetime.utcnow(),
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)

    audit_service.record(
        db,
        user_id=trip.user_id,
        trip_id=trip.id,
        resource_type="GPS",
        action="WRITE_LOCATION",
        status="ALLOWED",
        privacy_state=trip.privacy_state,
        detail=f"({loc.latitude:.4f}, {loc.longitude:.4f})",
    )
    return loc


def set_state(
    db: Session, trip: SafetyTrip, target_state: str, reason: str = ""
) -> SafetyTrip:
    if not privacy_state.can_transition(trip.privacy_state, target_state):
        raise ValueError(
            f"Cannot transition from {trip.privacy_state} to {target_state}."
        )
    previous = trip.privacy_state
    trip.privacy_state = target_state
    if target_state == "RESOLVED":
        trip.status = "RESOLVED"
        trip.ended_at = datetime.utcnow()
    elif target_state == "ANOMALY_DETECTED":
        trip.status = "ANOMALY_DETECTED"
    elif target_state == "EMERGENCY_ACTIVE":
        trip.status = "EMERGENCY_ACTIVE"
    elif target_state == "TRIP_ACTIVE":
        trip.status = "TRIP_ACTIVE"
    db.commit()
    db.refresh(trip)

    audit_service.record(
        db,
        user_id=trip.user_id,
        trip_id=trip.id,
        resource_type="STATE",
        action="TRANSITION",
        status="ALLOWED",
        privacy_state=target_state,
        detail=f"{previous} -> {target_state}. {reason}".strip(),
    )
    return trip
