from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConsentOut(BaseModel):
    id: int
    resource_type: str
    purpose: str
    granted: bool
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsentUpsert(BaseModel):
    resource_type: str = Field(..., pattern="^(GPS|MICROPHONE|CAMERA|LOCATION_HISTORY|EMERGENCY_CONTACTS)$")
    granted: bool
    purpose: Optional[str] = None


class AuditOut(BaseModel):
    id: int
    trip_id: Optional[int]
    resource_type: str
    action: str
    status: str
    privacy_state: str
    detail: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class PrivacyStateOut(BaseModel):
    state: str
    trip_id: Optional[int] = None


class ReceiptOut(BaseModel):
    id: int
    trip_id: Optional[int]
    summary: str
    resources_accessed: List[str]
    receipt_hash: str
    generated_at: datetime
