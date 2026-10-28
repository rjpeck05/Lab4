import unittest
from datetime import datetime

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
from study_room_booking.use_cases.clock import Clock
from study_room_booking.use_cases.list_available_rooms import ListAvailableRooms


class FixedClock(Clock):
    def __init__(self, now):
        self._now = now

    def now(self):
        return self._now


def text(view_model):
    return " ".join(view_model.lines)


class BookingAStudyRoomTest(unittest.TestCase):
    def setUp(self):
        rooms = InMemoryRoomGateway(
            [Room("R1", "Room 1", "Library", 4), Room("R2", "Room 2", "Library", 8)]
        )
        bookings = InMemoryBookingGateway()
        clock = FixedClock(datetime(2026, 11, 1, 9, 0))
        bp, cp, lp = BookRoomPresenter(), CancelBookingPresenter(), ListAvailableRoomsPresenter()
        self.book = BookRoomController(BookRoom(rooms, bookings, clock, bp), bp).book
        self.cancel = CancelBookingController(CancelBooking(bookings, clock, cp), cp).cancel
        self.find = ListAvailableRoomsController(ListAvailableRooms(rooms, bookings, lp), lp).find

    def test_a_booked_room_disappears_from_availability_until_cancelled(self):
        self.assertTrue(self.book("s1", "R1", "2026-11-02T10:00", "2026-11-02T12:00", "3").ok)
        self.assertIn(
            "already booked", text(self.book("s2", "R1", "2026-11-02T11:00", "2026-11-02T12:30"))
        )

        free = text(self.find("2026-11-02T11:00", "2026-11-02T12:00", "2"))
        self.assertNotIn("R1", free)
        self.assertIn("R2", free)

        self.assertTrue(self.cancel("s1", "B0001").ok)
        self.assertTrue(self.book("s2", "R1", "2026-11-02T11:00", "2026-11-02T12:30").ok)

    def test_booking_rules_are_enforced(self):
        self.assertIn("at most 3 hours", text(self.book("s1", "R1", "2026-11-02T10:00", "2026-11-02T14:00")))
        self.assertIn("does not fit", text(self.book("s1", "R1", "2026-11-02T10:00", "2026-11-02T11:00", "9")))
        self.assertIn("open", text(self.book("s1", "R1", "2026-11-02T07:00", "2026-11-02T08:30")))
        self.assertIn("future", text(self.book("s1", "R1", "2026-11-01T08:30", "2026-11-01T09:00")))
        self.assertIn("Could not read", text(self.book("s1", "R1", "garbage", "2026-11-02T09:00")))

    def test_a_student_holds_at_most_two_upcoming_bookings_and_cancels_only_their_own(self):
        self.book("s1", "R1", "2026-11-02T09:00", "2026-11-02T10:00")
        self.book("s1", "R1", "2026-11-02T10:00", "2026-11-02T11:00")
        self.assertIn("at most 2", text(self.book("s1", "R2", "2026-11-02T10:00", "2026-11-02T11:00")))
        self.assertIn("own bookings", text(self.cancel("someone-else", "B0001")))


if __name__ == "__main__":
    unittest.main()
