"""Composition root: the one place where concrete classes are chosen and wired."""

from study_room_booking.entities.room import Room
from study_room_booking.interface_adapters.book_room import BookRoomController, BookRoomPresenter
from study_room_booking.interface_adapters.cancel_booking import (
    CancelBookingController,
    CancelBookingPresenter,
)
from study_room_booking.interface_adapters.gateways.in_memory_bookings import InMemoryBookingGateway
from study_room_booking.interface_adapters.gateways.in_memory_rooms import InMemoryRoomGateway
from study_room_booking.interface_adapters.list_available_rooms import (
    ListAvailableRoomsController,
    ListAvailableRoomsPresenter,
)
from study_room_booking.use_cases.book_room import BookRoom
from study_room_booking.use_cases.cancel_booking import CancelBooking
from study_room_booking.use_cases.list_available_rooms import ListAvailableRooms

from .student_shell import StudentShell
from .system_clock import SystemClock

SEED_ROOMS = [
    Room("L101", "Quiet Room 1", "Main Library", 4),
    Room("L102", "Group Room A", "Main Library", 8),
    Room("S201", "Seminar Pod", "Science Building", 6),
]


def build_shell() -> StudentShell:
    rooms = InMemoryRoomGateway(SEED_ROOMS)
    bookings = InMemoryBookingGateway()
    clock = SystemClock()

    book_presenter = BookRoomPresenter()
    cancel_presenter = CancelBookingPresenter()
    list_presenter = ListAvailableRoomsPresenter()

    return StudentShell(
        book_room=BookRoomController(
            BookRoom(rooms, bookings, clock, book_presenter), book_presenter
        ),
        cancel_booking=CancelBookingController(
            CancelBooking(bookings, clock, cancel_presenter), cancel_presenter
        ),
        list_available_rooms=ListAvailableRoomsController(
            ListAvailableRooms(rooms, bookings, list_presenter), list_presenter
        ),
    )


def main() -> None:
    build_shell().cmdloop()
