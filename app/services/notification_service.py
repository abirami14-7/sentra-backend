from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.notification import EmergencyNotification
from app.models.trip import SafetyTrip
from app.models.user import EmergencyContact
from app.services import audit_service


def _message_for(
    trip: Optional[SafetyTrip],
    lat: Optional[float],
    lng: Optional[float],
) -> str:
    if trip is None:
        return "SENTRA alert: user triggered an emergency."
    loc = ""
    if lat is not None and lng is not None:
        loc = f" Last location: https://www.openstreetmap.org/?mlat={lat:.5f}&mlon={lng:.5f}"
    return (
        f"SENTRA alert: {trip.origin} to {trip.destination}. "
        f"User may need help.{loc}"
    )


def notify_all_contacts(
    db: Session,
    user_id: int,
    trip: SafetyTrip,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
) -> List[EmergencyNotification]:
    """Log a notification row for every emergency contact."""
    contacts = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == user_id)
        .order_by(EmergencyContact.priority.asc())
        .all()
    )

    message = _message_for(trip, lat, lng)
    out: List[EmergencyNotification] = []

    for c in contacts:
        row = EmergencyNotification(
            user_id=user_id,
            trip_id=trip.id,
            contact_id=c.id,
            contact_name=c.name,
            contact_phone=c.phone,
            channel="in_app",
            status="LOGGED",
            message=message,
            latitude=lat,
            longitude=lng,
            created_at=datetime.utcnow(),
        )
        db.add(row)
        out.append(row)

    if out:
        db.commit()
        for r in out:
            db.refresh(r)

        audit_service.record(
            db,
            user_id=user_id,
            trip_id=trip.id,
            resource_type="CONTACTS",
            action="EMERGENCY_NOTIFY",
            status=f"LOGGED ({len(out)} contacts)",
            privacy_state="EMERGENCY_ACTIVE",
            detail=message[:200],
        )

    return out


def list_for_trip(
    db: Session, user_id: int, trip_id: int
) -> List[EmergencyNotification]:
    return (
        db.query(EmergencyNotification)
        .filter(
            EmergencyNotification.user_id == user_id,
            EmergencyNotification.trip_id == trip_id,
        )
        .order_by(EmergencyNotification.created_at.asc())
        .all()
    )
