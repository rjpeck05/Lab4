from __future__ import annotations

from datetime import datetime

from study_room_booking.use_cases.clock import Clock


class FakeClock(Clock):
    """Offline stand-in for SystemClock: time only moves when a test says so."""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now
