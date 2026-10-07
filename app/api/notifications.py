from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services import notification_service, trip_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/trip/{trip_id}", response_model=List[NotificationOut])
def list_for_trip(
    trip_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_by_id(db, current.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return notification_service.list_for_trip(db, current.id, trip_id)
