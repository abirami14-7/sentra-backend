from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.privacy import (
    AuditOut,
    ConsentOut,
    ConsentUpsert,
    PrivacyStateOut,
    ReceiptOut,
)
from app.services import audit_service, consent_service, receipt_service, trip_service

router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.get("/consents", response_model=List[ConsentOut])
def list_consents(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    consent_service.ensure_defaults(db, current.id)
    return consent_service.list_all(db, current.id)


@router.post("/consents", response_model=ConsentOut)
def upsert_consent(
    payload: ConsentUpsert,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = consent_service.set_granted(
        db,
        user_id=current.id,
        resource_type=payload.resource_type,
        granted=payload.granted,
        purpose=payload.purpose,
    )
    audit_service.record(
        db,
        user_id=current.id,
        resource_type=payload.resource_type,
        action="CONSENT_GRANTED" if payload.granted else "CONSENT_REVOKED",
        status="RECORDED",
        privacy_state="IDLE",
        detail=payload.purpose or "",
    )
    return record


@router.get("/audit-log", response_model=List[AuditOut])
def get_audit_log(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return audit_service.list_for_user(db, current.id)


@router.get("/state", response_model=PrivacyStateOut)
def get_state(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_active(db, current.id)
    if trip is None:
        return PrivacyStateOut(state="IDLE", trip_id=None)
    return PrivacyStateOut(state=trip.privacy_state, trip_id=trip.id)


@router.get("/receipt/{trip_id}", response_model=ReceiptOut)
def get_receipt(
    trip_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_by_id(db, current.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    receipt = receipt_service.get_for_trip(db, current.id, trip_id)
    if receipt is None:
        receipt = receipt_service.generate_for_trip(
            db,
            user_id=current.id,
            trip_id=trip.id,
            trip_summary=f"{trip.origin} to {trip.destination}",
        )
    return ReceiptOut(
        id=receipt.id,
        trip_id=receipt.trip_id,
        summary=receipt.summary,
        resources_accessed=[r for r in receipt.resources_accessed.split(",") if r],
        receipt_hash=receipt.receipt_hash,
        generated_at=receipt.generated_at,
    )
