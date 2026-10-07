import hashlib
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.privacy import PrivacyAuditLog, PrivacyReceipt
from app.services import audit_service


def _hash_payload(payload: str) -> str:
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def generate_for_trip(db: Session, user_id: int, trip_id: int, trip_summary: str) -> PrivacyReceipt:
    entries: List[PrivacyAuditLog] = audit_service.list_for_trip(db, user_id, trip_id)

    accessed = sorted({e.resource_type for e in entries if e.status == "ALLOWED"})
    denied = [e for e in entries if "DENIED" in e.status]

    summary_lines = [
        f"Trip {trip_id}: {trip_summary}",
        f"Resources accessed under consent: {', '.join(accessed) if accessed else 'none'}.",
        f"Denied accesses: {len(denied)}.",
    ]
    summary = " ".join(summary_lines)

    payload = f"{user_id}|{trip_id}|{summary}|{','.join(accessed)}"
    receipt = PrivacyReceipt(
        user_id=user_id,
        trip_id=trip_id,
        summary=summary,
        resources_accessed=",".join(accessed),
        receipt_hash=_hash_payload(payload),
        generated_at=datetime.utcnow(),
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


def get_for_trip(db: Session, user_id: int, trip_id: int) -> PrivacyReceipt | None:
    return (
        db.query(PrivacyReceipt)
        .filter(
            PrivacyReceipt.user_id == user_id,
            PrivacyReceipt.trip_id == trip_id,
        )
        .order_by(PrivacyReceipt.generated_at.desc())
        .first()
    )
