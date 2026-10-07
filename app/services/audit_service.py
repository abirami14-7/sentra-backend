from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.privacy import PrivacyAuditLog


def record(
    db: Session,
    user_id: int,
    resource_type: str,
    action: str,
    status: str,
    privacy_state: str,
    trip_id: Optional[int] = None,
    detail: Optional[str] = None,
    commit: bool = True,
) -> PrivacyAuditLog:
    entry = PrivacyAuditLog(
        user_id=user_id,
        trip_id=trip_id,
        resource_type=resource_type,
        action=action,
        status=status,
        privacy_state=privacy_state,
        detail=detail,
        timestamp=datetime.utcnow(),
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    return entry


def list_for_user(db: Session, user_id: int, limit: int = 200) -> List[PrivacyAuditLog]:
    return (
        db.query(PrivacyAuditLog)
        .filter(PrivacyAuditLog.user_id == user_id)
        .order_by(desc(PrivacyAuditLog.timestamp))
        .limit(limit)
        .all()
    )


def list_for_trip(db: Session, user_id: int, trip_id: int) -> List[PrivacyAuditLog]:
    return (
        db.query(PrivacyAuditLog)
        .filter(
            PrivacyAuditLog.user_id == user_id,
            PrivacyAuditLog.trip_id == trip_id,
        )
        .order_by(PrivacyAuditLog.timestamp.asc())
        .all()
    )
