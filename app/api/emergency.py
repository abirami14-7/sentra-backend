from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services import notification_service, trip_service

router = APIRouter(prefix="/emergency", tags=["emergency"])


class TriggerRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


@router.post("/trigger", response_model=List[NotificationOut])
def trigger(
    payload: TriggerRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_active(db, current.id)
    if trip is None:
        raise HTTPException(
            status_code=400,
            detail="No active trip. Start a trip before triggering SOS.",
        )

    lat = payload.latitude
    lng = payload.longitude
    if lat is None or lng is None:
        last = trip.locations[-1] if trip.locations else None
        if last is not None:
            lat = last.latitude
            lng = last.longitude

    try:
        trip_service.set_state(
            db, trip, "EMERGENCY_ACTIVE", reason="SOS triggered by user."
        )
    except ValueError:
        pass

    rows = notification_service.notify_all_contacts(
        db,
        user_id=current.id,
        trip=trip,
        lat=lat,
        lng=lng,
    )
    return rows
