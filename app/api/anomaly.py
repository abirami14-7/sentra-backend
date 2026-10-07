from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.anomaly import AnomalyEvent
from app.models.user import User
from app.schemas.anomaly import AnomalyOut, AnomalyResponse
from app.services import (
    anomaly_service,
    notification_service,
    trip_service,
)

router = APIRouter(prefix="/anomaly", tags=["anomaly"])


@router.get("/{anomaly_id}", response_model=AnomalyOut)
def get_anomaly(
    anomaly_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = db.get(AnomalyEvent, anomaly_id)
    if a is None or a.user_id != current.id:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return a


@router.post("/{anomaly_id}/respond", response_model=AnomalyOut)
def respond(
    anomaly_id: int,
    payload: AnomalyResponse,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = db.get(AnomalyEvent, anomaly_id)
    if a is None or a.user_id != current.id:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    trip = trip_service.get_by_id(db, current.id, a.trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    a = anomaly_service.respond(db, a, payload.response)

    if payload.response == "SAFE":
        try:
            trip_service.set_state(
                db, trip, "TRIP_ACTIVE", reason="User confirmed safe."
            )
        except ValueError:
            pass
    else:
        try:
            trip_service.set_state(
                db,
                trip,
                "EMERGENCY_ACTIVE",
                reason="User requested help.",
            )
        except ValueError:
            pass

        # Log a notification row for each emergency contact
        last_loc = trip.locations[-1] if trip.locations else None
        try:
            notification_service.notify_all_contacts(
                db,
                user_id=current.id,
                trip=trip,
                lat=last_loc.latitude if last_loc else None,
                lng=last_loc.longitude if last_loc else None,
            )
        except Exception:
            db.rollback()

    return a


@router.get("/trip/{trip_id}", response_model=list[AnomalyOut])
def list_for_trip(
    trip_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_by_id(db, current.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return anomaly_service.list_for_trip(db, trip_id)
