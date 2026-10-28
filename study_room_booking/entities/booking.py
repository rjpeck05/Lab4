from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .errors import BookingRuleViolation
from .time_slot import TimeSlot


class BookingStatus(Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass
class Booking:
    id: str
    room_id: str
    student_id: str
    slot: TimeSlot
    status: BookingStatus = BookingStatus.CONFIRMED

    @property
    def is_active(self) -> bool:
        return self.status is BookingStatus.CONFIRMED

    def conflicts_with(self, other: Booking) -> bool:
        """Two active bookings of the same room may never overlap in time."""
        return (
            self.room_id == other.room_id
            and self.is_active
            and other.is_active
            and self.slot.overlaps(other.slot)
        )

    def cancel(self, now: datetime) -> None:
        if not self.is_active:
            raise BookingRuleViolation("Booking is already cancelled.")
        if now >= self.slot.start:
            raise BookingRuleViolation("A booking that has started cannot be cancelled.")
        self.status = BookingStatus.CANCELLED
