from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from study_room_booking.entities.booking import Booking


class BookingGateway(ABC):
    """Where bookings are kept, as far as the use cases are concerned."""

    @abstractmethod
    def next_id(self) -> str: ...

    @abstractmethod
    def add(self, booking: Booking) -> None: ...

    @abstractmethod
    def save(self, booking: Booking) -> None: ...

    @abstractmethod
    def get(self, booking_id: str) -> Optional[Booking]: ...

    @abstractmethod
    def list_for_room(self, room_id: str) -> list[Booking]: ...

    @abstractmethod
    def list_active_for_student(self, student_id: str) -> list[Booking]: ...
