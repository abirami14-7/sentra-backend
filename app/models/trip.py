from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SafetyTrip(Base):
    __tablename__ = "safety_trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    route_id: Mapped[str] = mapped_column(String(64), nullable=False)
    route_name: Mapped[str] = mapped_column(String(255), nullable=False)
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    travel_mode: Mapped[str] = mapped_column(
        String(32), default="walking", nullable=False
    )
    shared_contact_ids: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default="TRIP_ACTIVE", nullable=False
    )
    privacy_state: Mapped[str] = mapped_column(
        String(32), default="TRIP_ACTIVE", nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    locations: Mapped[list["TripLocation"]] = relationship(
        "TripLocation",
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="TripLocation.recorded_at",
    )


class TripLocation(Base):
    __tablename__ = "trip_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("safety_trips.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="mock", nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    trip: Mapped[SafetyTrip] = relationship(
        "SafetyTrip", back_populates="locations"
    )
