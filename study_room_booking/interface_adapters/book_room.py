from __future__ import annotations

from study_room_booking.use_cases.book_room import (
    BookRoom,
    BookRoomOutputBoundary,
    BookRoomRequest,
    BookRoomResponse,
)

from .input_parsing import UNREADABLE_INPUT, parse_date_time
from .view_model import ViewModel


class BookRoomPresenter(BookRoomOutputBoundary):
    def __init__(self) -> None:
        self.view_model = ViewModel(True, ())

    def present_booking(self, response: BookRoomResponse) -> None:
        self.view_model = ViewModel(
            True,
            (
                f"Booked! Reference {response.booking_id}: room {response.room_id}, "
                f"{response.start:%Y-%m-%d %H:%M} -> {response.end:%H:%M}.",
            ),
        )

    def present_error(self, message: str) -> None:
        self.view_model = ViewModel(False, (f"Error: {message}",))


class BookRoomController:
    def __init__(self, use_case: BookRoom, presenter: BookRoomPresenter) -> None:
        self._use_case = use_case
        self._presenter = presenter

    def book(self, student_id: str, room_id: str, start: str, end: str, group_size: str = "1") -> ViewModel:
        try:
            request = BookRoomRequest(
                student_id, room_id, parse_date_time(start), parse_date_time(end), int(group_size)
            )
        except ValueError:
            return UNREADABLE_INPUT
        self._use_case.execute(request)
        return self._presenter.view_model
