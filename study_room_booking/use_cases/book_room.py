from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from study_room_booking.entities.booking import Booking
from study_room_booking.entities.errors import (
    BookingRuleViolation,
    DomainError,
    RoomNotFound,
)
from study_room_booking.entities.time_slot import TimeSlot

from .booking_gateway import BookingGateway
from .clock import Clock
from .room_gateway import RoomGateway

MAX_UPCOMING_BOOKINGS_PER_STUDENT = 2


@dataclass(frozen=True)
class BookRoomRequest:
    student_id: str
    room_id: str
    start: datetime
    end: datetime
    group_size: int


@dataclass(frozen=True)
class BookRoomResponse:
    booking_id: str
    room_id: str
    student_id: str
    start: datetime
    end: datetime


class BookRoomOutputBoundary(ABC):
    @abstractmethod
    def present_booking(self, response: BookRoomResponse) -> None: ...

    @abstractmethod
    def present_error(self, message: str) -> None: ...


class BookRoom:
    def __init__(
        self,
        rooms: RoomGateway,
        bookings: BookingGateway,
        clock: Clock,
        output: BookRoomOutputBoundary,
    ) -> None:
        self._rooms = rooms
        self._bookings = bookings
        self._clock = clock
        self._output = output

    def execute(self, request: BookRoomRequest) -> None:
        try:
            response = self._book(request)
        except DomainError as error:
            self._output.present_error(str(error))
            return
        self._output.present_booking(response)

    def _book(self, request: BookRoomRequest) -> BookRoomResponse:
        now = self._clock.now()

        room = self._rooms.get(request.room_id)
        if room is None:
            raise RoomNotFound(f"Room '{request.room_id}' does not exist.")
        if not room.fits(request.group_size):
            raise BookingRuleViolation(
                f"{room.name} holds {room.capacity} people; "
                f"group size {request.group_size} does not fit."
            )

        slot = TimeSlot(request.start, request.end)  # entity validates the rules
        if slot.start <= now:
            raise BookingRuleViolation("Bookings must start in the future.")

        upcoming = [
            b
            for b in self._bookings.list_active_for_student(request.student_id)
            if b.slot.end > now
        ]
        if len(upcoming) >= MAX_UPCOMING_BOOKINGS_PER_STUDENT:
            raise BookingRuleViolation(
                f"Students may hold at most {MAX_UPCOMING_BOOKINGS_PER_STUDENT} "
                "upcoming bookings."
            )

        candidate = Booking(
            id=self._bookings.next_id(),
            room_id=room.id,
            student_id=request.student_id,
            slot=slot,
        )
        if any(candidate.conflicts_with(b) for b in self._bookings.list_for_room(room.id)):
            raise BookingRuleViolation(f"{room.name} is already booked at that time.")

        self._bookings.add(candidate)
        return BookRoomResponse(
            booking_id=candidate.id,
            room_id=room.id,
            student_id=candidate.student_id,
            start=slot.start,
            end=slot.end,
        )
