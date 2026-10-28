from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from .errors import InvalidTimeSlot

OPENING_TIME = time(8, 0)
CLOSING_TIME = time(22, 0)
MAX_DURATION = timedelta(hours=3)


@dataclass(frozen=True)
class TimeSlot:
    """Value object: a bookable interval within a single day."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise InvalidTimeSlot("End time must be after start time.")
        if self.start.date() != self.end.date():
            raise InvalidTimeSlot("A booking must start and end on the same day.")
        if self.start.time() < OPENING_TIME or self.end.time() > CLOSING_TIME:
            raise InvalidTimeSlot(
                f"Rooms are open {OPENING_TIME:%H:%M}-{CLOSING_TIME:%H:%M}."
            )
        if self.end - self.start > MAX_DURATION:
            raise InvalidTimeSlot("A booking may last at most 3 hours.")

    def overlaps(self, other: TimeSlot) -> bool:
        return self.start < other.end and other.start < self.end
