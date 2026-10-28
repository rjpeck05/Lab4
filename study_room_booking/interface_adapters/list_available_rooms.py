from __future__ import annotations

from study_room_booking.use_cases.list_available_rooms import (
    ListAvailableRooms,
    ListAvailableRoomsOutputBoundary,
    ListAvailableRoomsRequest,
    ListAvailableRoomsResponse,
)

from .input_parsing import UNREADABLE_INPUT, parse_date_time
from .view_model import ViewModel


class ListAvailableRoomsPresenter(ListAvailableRoomsOutputBoundary):
    def __init__(self) -> None:
        self.view_model = ViewModel(True, ())

    def present_rooms(self, response: ListAvailableRoomsResponse) -> None:
        if not response.rooms:
            self.view_model = ViewModel(True, ("No rooms available for that time.",))
            return
        header = f"Available {response.start:%Y-%m-%d %H:%M} -> {response.end:%H:%M}:"
        rows = tuple(
            f"  {r.room_id:<6} {r.name} ({r.building}, seats {r.capacity})" for r in response.rooms
        )
        self.view_model = ViewModel(True, (header, *rows))

    def present_error(self, message: str) -> None:
        self.view_model = ViewModel(False, (f"Error: {message}",))


class ListAvailableRoomsController:
    def __init__(self, use_case: ListAvailableRooms, presenter: ListAvailableRoomsPresenter) -> None:
        self._use_case = use_case
        self._presenter = presenter

    def find(self, start: str, end: str, group_size: str = "1") -> ViewModel:
        try:
            request = ListAvailableRoomsRequest(
                parse_date_time(start), parse_date_time(end), int(group_size)
            )
        except ValueError:
            return UNREADABLE_INPUT
        self._use_case.execute(request)
        return self._presenter.view_model
