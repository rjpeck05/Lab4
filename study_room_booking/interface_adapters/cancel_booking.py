from __future__ import annotations

from study_room_booking.use_cases.cancel_booking import (
    CancelBooking,
    CancelBookingOutputBoundary,
    CancelBookingRequest,
    CancelBookingResponse,
)

from .view_model import ViewModel


class CancelBookingPresenter(CancelBookingOutputBoundary):
    def __init__(self) -> None:
        self.view_model = ViewModel(True, ())

    def present_cancellation(self, response: CancelBookingResponse) -> None:
        self.view_model = ViewModel(True, (f"Booking {response.booking_id} cancelled.",))

    def present_error(self, message: str) -> None:
        self.view_model = ViewModel(False, (f"Error: {message}",))


class CancelBookingController:
    def __init__(self, use_case: CancelBooking, presenter: CancelBookingPresenter) -> None:
        self._use_case = use_case
        self._presenter = presenter

    def cancel(self, student_id: str, booking_id: str) -> ViewModel:
        self._use_case.execute(CancelBookingRequest(booking_id, student_id))
        return self._presenter.view_model
