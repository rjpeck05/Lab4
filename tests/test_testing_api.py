import unittest
from datetime import datetime

from study_room_booking.entities.booking import BookingStatus
from study_room_booking.entities.room import Room
from study_room_booking.interface_adapters.testing_api import TestingApi

ROOMS = [Room("R1", "Room 1", "Library", 4), Room("R2", "Room 2", "Library", 8)]


def at(day, hour):
    return datetime(2026, 11, day, hour, 0)


class TestingApiTest(unittest.TestCase):
    def setUp(self):
        self.api = TestingApi(ROOMS, now=at(1, 9))

    def test_book_returns_response_and_view_model(self):
        out = self.api.book_room("s1", "R1", at(2, 10), at(2, 12), 3)
        self.assertTrue(out.ok)
        self.assertEqual(out.response.booking_id, "B0001")
        self.assertTrue(out.view_model.ok)
        self.assertIn("Booked!", out.view_model.lines[0])

    def test_failure_exposes_raw_error_and_view_model(self):
        out = self.api.book_room("s1", "R1", at(2, 10), at(2, 14))
        self.assertFalse(out.ok)
        self.assertIsNone(out.response)
        self.assertEqual(out.error, "A booking may last at most 3 hours.")
        self.assertEqual(out.view_model.lines, ("Error: " + out.error,))

    def test_seeded_booking_blocks_a_conflicting_booking(self):
        self.api.seed_booking("R1", "other", at(2, 10), at(2, 12))
        out = self.api.book_room("s1", "R1", at(2, 11), at(2, 12))
        self.assertIn("already booked", out.error)

    def test_seeding_can_force_states_the_use_cases_would_refuse(self):
        self.api.seed_booking("R1", "s1", at(2, 9), at(2, 10))
        self.api.seed_booking("R2", "s1", at(2, 9), at(2, 10))
        out = self.api.book_room("s1", "R1", at(3, 9), at(3, 10))
        self.assertIn("at most 2", out.error)

    def test_clock_controls_cancellation_of_a_started_booking(self):
        booking_id = self.api.seed_booking("R1", "s1", at(2, 10), at(2, 12))
        self.api.set_now(at(2, 11))
        out = self.api.cancel_booking("s1", booking_id)
        self.assertIn("started", out.error)

    def test_cancel_changes_state_and_frees_the_room(self):
        booking_id = self.api.seed_booking("R1", "s1", at(2, 10), at(2, 12))
        self.assertTrue(self.api.cancel_booking("s1", booking_id).ok)
        self.assertIs(self.api.get_booking(booking_id).status, BookingStatus.CANCELLED)
        rooms = self.api.list_available_rooms(at(2, 10), at(2, 12)).response.rooms
        self.assertEqual([r.room_id for r in rooms], ["R1", "R2"])

    def test_seed_a_cancelled_booking(self):
        booking_id = self.api.seed_booking(
            "R1", "s1", at(2, 10), at(2, 12), status=BookingStatus.CANCELLED
        )
        self.assertIn("already cancelled", self.api.cancel_booking("s1", booking_id).error)

    def test_list_available_rooms_filters_by_group_size_and_bookings(self):
        self.api.seed_booking("R2", "s1", at(2, 10), at(2, 12))
        out = self.api.list_available_rooms(at(2, 10), at(2, 12), 2)
        self.assertEqual([r.room_id for r in out.response.rooms], ["R1"])
        self.assertIn("R1", out.view_model.lines[1])

    def test_each_run_reports_only_its_own_result(self):
        self.assertFalse(self.api.book_room("s1", "NOPE", at(2, 10), at(2, 11)).ok)
        self.assertTrue(self.api.book_room("s1", "R1", at(2, 10), at(2, 11)).ok)

    def test_seed_room_and_reset(self):
        self.api.reset(now=at(1, 9))
        self.assertIn("does not exist", self.api.book_room("s1", "R9", at(2, 10), at(2, 11)).error)
        self.api.seed_room(Room("R9", "Pod", "Science", 2))
        self.assertTrue(self.api.book_room("s1", "R9", at(2, 10), at(2, 11)).ok)
        self.api.reset()
        self.assertIn("does not exist", self.api.book_room("s1", "R9", at(2, 10), at(2, 11)).error)


if __name__ == "__main__":
    unittest.main()
