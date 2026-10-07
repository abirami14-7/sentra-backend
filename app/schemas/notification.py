from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    id: int
    trip_id: Optional[int]
    contact_name: str
    contact_phone: str
    channel: str
    status: str
    message: str
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
