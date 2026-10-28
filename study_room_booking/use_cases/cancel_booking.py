from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from study_room_booking.entities.errors import (
    BookingNotFound,
    BookingRuleViolation,
    DomainError,
)

from .booking_gateway import BookingGateway
from .clock import Clock


@dataclass(frozen=True)
class CancelBookingRequest:
    booking_id: str
    student_id: str


@dataclass(frozen=True)
class CancelBookingResponse:
    booking_id: str


class CancelBookingOutputBoundary(ABC):
    @abstractmethod
    def present_cancellation(self, response: CancelBookingResponse) -> None: ...

    @abstractmethod
    def present_error(self, message: str) -> None: ...


class CancelBooking:
    def __init__(
        self,
        bookings: BookingGateway,
        clock: Clock,
        output: CancelBookingOutputBoundary,
    ) -> None:
        self._bookings = bookings
        self._clock = clock
        self._output = output

    def execute(self, request: CancelBookingRequest) -> None:
        try:
            booking = self._bookings.get(request.booking_id)
            if booking is None:
                raise BookingNotFound(f"Booking '{request.booking_id}' does not exist.")
            if booking.student_id != request.student_id:
                raise BookingRuleViolation("You can only cancel your own bookings.")
            booking.cancel(self._clock.now())
            self._bookings.save(booking)
        except DomainError as error:
            self._output.present_error(str(error))
            return
        self._output.present_cancellation(CancelBookingResponse(booking.id))
