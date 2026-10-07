from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.anomaly import AnomalyEvent
from app.models.user import User
from app.schemas.anomaly import AnomalyOut
from app.schemas.trip import (
    TripLocationCreate,
    TripLocationOut,
    TripOut,
    TripStart,
    TripWithLocations,
)
from app.services import anomaly_service, consent_service, receipt_service, trip_service

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=TripOut, status_code=status.HTTP_201_CREATED)
def start_trip(
    payload: TripStart,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    consent_service.ensure_defaults(db, current.id)
    if trip_service.get_active(db, current.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active trip already exists for this user.",
        )
    return trip_service.start_trip(db, current.id, payload)


@router.get("/active", response_model=TripWithLocations | None)
def get_active(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_active(db, current.id)
    if trip is None:
        return None
    return trip


@router.get("/history", response_model=List[TripOut])
def get_history(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return trip_service.list_history(db, current.id)


@router.get("/{trip_id}", response_model=TripWithLocations)
def get_trip(
    trip_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_by_id(db, current.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/{trip_id}/locations", response_model=TripLocationOut, status_code=201)
def add_location(
    trip_id: int,
    payload: TripLocationCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_by_id(db, current.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    try:
        return trip_service.add_location(db, trip, payload)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{trip_id}/anomaly/check", response_model=List[AnomalyOut])
def check_anomaly(
    trip_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_by_id(db, current.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    events = anomaly_service.detect(db, trip)
    if events:
        try:
            trip_service.set_state(
                db,
                trip,
                "ANOMALY_DETECTED",
                reason=f"{len(events)} anomaly event(s) detected.",
            )
        except ValueError:
            pass
    return events


@router.post("/{trip_id}/end", response_model=TripOut)
def end_trip(
    trip_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_by_id(db, current.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trip_service.set_state(db, trip, "RESOLVED", reason="User ended trip.")
    receipt_service.generate_for_trip(
        db,
        user_id=current.id,
        trip_id=trip.id,
        trip_summary=f"{trip.origin} to {trip.destination}",
    )
    return trip
