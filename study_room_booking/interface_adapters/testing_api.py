"""TestingApi: a test-only driving adapter, a peer of the controllers.

It drives each use case directly through its input boundary (``execute(request)``),
lets a test force the system into any starting state by seeding the in-memory
gateways and the clock, and returns the resulting view model and response.

It never touches the view, the console or any framework type: controllers,
input parsing and ``StudentShell`` are bypassed entirely.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Iterable, Optional, TypeVar

from study_room_booking.entities.booking import Booking, BookingStatus
from study_room_booking.entities.room import Room
from study_room_booking.entities.time_slot import TimeSlot
from study_room_booking.use_cases.book_room import (
    BookRoom,
    BookRoomRequest,
    BookRoomResponse,
)
from study_room_booking.use_cases.cancel_booking import (
    CancelBooking,
    CancelBookingRequest,
    CancelBookingResponse,
)
from study_room_booking.use_cases.classify_request import (
    ClassifyRequest,
    ClassifyRequestRequest,
    ClassifyRequestResponse,
)
from study_room_booking.use_cases.model_gateway import ModelGateway
from study_room_booking.use_cases.list_available_rooms import (
    ListAvailableRooms,
    ListAvailableRoomsRequest,
    ListAvailableRoomsResponse,
)

from .book_room import BookRoomPresenter
from .classify_request import ClassifyRequestPresenter
from .cancel_booking import CancelBookingPresenter
from .gateways.fake_clock import FakeClock
from .gateways.fake_model_adapter import FakeModelAdapter
from .gateways.in_memory_bookings import InMemoryBookingGateway
from .gateways.in_memory_rooms import InMemoryRoomGateway
from .list_available_rooms import ListAvailableRoomsPresenter
from .view_model import ViewModel

DEFAULT_NOW = datetime(2026, 11, 1, 9, 0)

R = TypeVar("R")


@dataclass(frozen=True)
class Outcome(Generic[R]):
    """What one use-case run produced.

    ``response`` is set on success, ``error`` (the raw message, without the
    presenter's "Error: " prefix) on failure. ``view_model`` is what the real
    presenter built, so tests can assert on exactly what a view would render.
    """

    response: Optional[R]
    error: Optional[str]
    view_model: ViewModel
    handoff: Optional[str] = None  # set when the system passed the user to a human

    @property
    def ok(self) -> bool:
        return self.error is None and self.handoff is None


MutableClock = FakeClock  # kept so existing imports keep working


# --- capturing output boundaries: the real presenters, plus a record of the raw result ---


class _CaptureMixin:
    captured_response = None
    captured_error: Optional[str] = None
    captured_handoff: Optional[str] = None

    def clear_capture(self) -> None:
        self.captured_response = None
        self.captured_error = None
        self.captured_handoff = None
        self.view_model = ViewModel(True, ())

    def outcome(self) -> Outcome:
        return Outcome(
            self.captured_response, self.captured_error, self.view_model, self.captured_handoff
        )


class _CapturingBookRoomPresenter(_CaptureMixin, BookRoomPresenter):
    def present_booking(self, response: BookRoomResponse) -> None:
        self.captured_response = response
        super().present_booking(response)

    def present_error(self, message: str) -> None:
        self.captured_error = message
        super().present_error(message)


class _CapturingCancelBookingPresenter(_CaptureMixin, CancelBookingPresenter):
    def present_cancellation(self, response: CancelBookingResponse) -> None:
        self.captured_response = response
        super().present_cancellation(response)

    def present_error(self, message: str) -> None:
        self.captured_error = message
        super().present_error(message)


class _CapturingListAvailableRoomsPresenter(_CaptureMixin, ListAvailableRoomsPresenter):
    def present_rooms(self, response: ListAvailableRoomsResponse) -> None:
        self.captured_response = response
        super().present_rooms(response)

    def present_error(self, message: str) -> None:
        self.captured_error = message
        super().present_error(message)


class _CapturingClassifyRequestPresenter(_CaptureMixin, ClassifyRequestPresenter):
    def present_intent(self, response: ClassifyRequestResponse) -> None:
        self.captured_response = response
        super().present_intent(response)

    def present_error(self, message: str) -> None:
        self.captured_error = message
        super().present_error(message)

    def present_handoff(self, reason: str) -> None:
        self.captured_handoff = reason
        super().present_handoff(reason)


class TestingApi:
    __test__ = False  # keep test runners from collecting this class

    def __init__(
        self,
        rooms: Iterable[Room] = (),
        now: datetime = DEFAULT_NOW,
        model: Optional[ModelGateway] = None,
    ) -> None:
        self._model = model if model is not None else FakeModelAdapter()
        self._wire(rooms, now)

    def _wire(self, rooms: Iterable[Room], now: datetime) -> None:
        self._rooms = InMemoryRoomGateway(rooms)
        self._bookings = InMemoryBookingGateway()
        self._clock = MutableClock(now)

        self._book_out = _CapturingBookRoomPresenter()
        self._cancel_out = _CapturingCancelBookingPresenter()
        self._list_out = _CapturingListAvailableRoomsPresenter()
        self._classify_out = _CapturingClassifyRequestPresenter()

        self._book_room = BookRoom(self._rooms, self._bookings, self._clock, self._book_out)
        self._cancel_booking = CancelBooking(self._bookings, self._clock, self._cancel_out)
        self._list_available_rooms = ListAvailableRooms(
            self._rooms, self._bookings, self._list_out
        )
        self._classify_request = ClassifyRequest(self._model, self._classify_out)

    # ---- forcing a starting state ----

    def reset(self, rooms: Iterable[Room] = (), now: Optional[datetime] = None) -> None:
        """Throw away all state (rooms, bookings, id counter) and start clean."""
        self._wire(rooms, now if now is not None else self._clock.now())

    def set_now(self, now: datetime) -> None:
        self._clock.set(now)

    def seed_room(self, room: Room) -> None:
        self._rooms.add(room)

    def seed_rooms(self, rooms: Iterable[Room]) -> None:
        for room in rooms:
            self.seed_room(room)

    def seed_booking(
        self,
        room_id: str,
        student_id: str,
        start: datetime,
        end: datetime,
        status: BookingStatus = BookingStatus.CONFIRMED,
    ) -> str:
        """Insert a booking directly, skipping every use-case rule. Returns its id.

        Skipping the rules is the point: it lets a test create states the use cases
        would refuse to build, such as a booking that has already started or one
        that is already cancelled. The slot must still satisfy TimeSlot's own
        invariants (opening hours, max 3 hours, same day).
        """
        booking = Booking(
            id=self._bookings.next_id(),
            room_id=room_id,
            student_id=student_id,
            slot=TimeSlot(start, end),
            status=status,
        )
        self._bookings.add(booking)
        return booking.id

    @property
    def model(self) -> ModelGateway:
        """The (fake) model gateway, so a test can switch scenarios or read prompts."""
        return self._model

    # ---- inspecting state (for assertions on side effects) ----

    def get_booking(self, booking_id: str) -> Optional[Booking]:
        return self._bookings.get(booking_id)

    # ---- driving the use cases through their input boundary ----

    def book_room(
        self, student_id: str, room_id: str, start: datetime, end: datetime, group_size: int = 1
    ) -> Outcome[BookRoomResponse]:
        self._book_out.clear_capture()
        self._book_room.execute(BookRoomRequest(student_id, room_id, start, end, group_size))
        return self._book_out.outcome()

    def cancel_booking(self, student_id: str, booking_id: str) -> Outcome[CancelBookingResponse]:
        self._cancel_out.clear_capture()
        self._cancel_booking.execute(CancelBookingRequest(booking_id, student_id))
        return self._cancel_out.outcome()

    def list_available_rooms(
        self, start: datetime, end: datetime, group_size: int = 1
    ) -> Outcome[ListAvailableRoomsResponse]:
        self._list_out.clear_capture()
        self._list_available_rooms.execute(ListAvailableRoomsRequest(start, end, group_size))
        return self._list_out.outcome()

    def classify_request(self, text: str) -> Outcome[ClassifyRequestResponse]:
        self._classify_out.clear_capture()
        self._classify_request.execute(ClassifyRequestRequest(text))
        return self._classify_out.outcome()
