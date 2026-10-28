from __future__ import annotations

import itertools
from typing import Optional

from study_room_booking.entities.booking import Booking
from study_room_booking.use_cases.booking_gateway import BookingGateway


class InMemoryBookingGateway(BookingGateway):
    def __init__(self) -> None:
        self._bookings: dict[str, Booking] = {}
        self._counter = itertools.count(1)

    def next_id(self) -> str:
        return f"B{next(self._counter):04d}"

    def add(self, booking: Booking) -> None:
        self._bookings[booking.id] = booking

    def save(self, booking: Booking) -> None:
        self._bookings[booking.id] = booking

    def get(self, booking_id: str) -> Optional[Booking]:
        return self._bookings.get(booking_id)

    def list_for_room(self, room_id: str) -> list[Booking]:
        return [b for b in self._bookings.values() if b.room_id == room_id]

    def list_active_for_student(self, student_id: str) -> list[Booking]:
        return [
            b for b in self._bookings.values() if b.student_id == student_id and b.is_active
        ]
