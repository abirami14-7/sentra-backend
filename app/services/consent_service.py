from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.privacy import ConsentRecord

DEFAULT_CONSENTS = [
    ("GPS", "Route safety analysis during trip"),
    ("LOCATION_HISTORY", "Baseline and anomaly detection"),
    ("MICROPHONE", "Anomaly detection during active trip"),
    ("CAMERA", "Emergency verification (optional)"),
    ("EMERGENCY_CONTACTS", "Notify contacts during emergency"),
]


def ensure_defaults(db: Session, user_id: int) -> None:
    existing = {
        c.resource_type
        for c in db.query(ConsentRecord).filter(ConsentRecord.user_id == user_id).all()
    }
    changed = False
    for resource_type, purpose in DEFAULT_CONSENTS:
        if resource_type not in existing:
            db.add(
                ConsentRecord(
                    user_id=user_id,
                    resource_type=resource_type,
                    purpose=purpose,
                    granted=False,
                    updated_at=datetime.utcnow(),
                )
            )
            changed = True
    if changed:
        db.commit()


def list_all(db: Session, user_id: int) -> List[ConsentRecord]:
    return (
        db.query(ConsentRecord)
        .filter(ConsentRecord.user_id == user_id)
        .order_by(ConsentRecord.resource_type.asc())
        .all()
    )


def get_for(db: Session, user_id: int, resource_type: str) -> Optional[ConsentRecord]:
    return (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.user_id == user_id,
            ConsentRecord.resource_type == resource_type,
        )
        .first()
    )


def set_granted(
    db: Session, user_id: int, resource_type: str, granted: bool, purpose: Optional[str] = None
) -> ConsentRecord:
    record = get_for(db, user_id, resource_type)
    now = datetime.utcnow()
    if record is None:
        record = ConsentRecord(
            user_id=user_id,
            resource_type=resource_type,
            purpose=purpose or "User-configured",
            granted=granted,
            updated_at=now,
        )
        db.add(record)
    else:
        record.granted = granted
        record.updated_at = now
        if purpose:
            record.purpose = purpose
    if granted:
        record.granted_at = now
        record.revoked_at = None
    else:
        record.revoked_at = now
    db.commit()
    db.refresh(record)
    return record


def is_granted(db: Session, user_id: int, resource_type: str) -> bool:
    r = get_for(db, user_id, resource_type)
    return bool(r and r.granted)
