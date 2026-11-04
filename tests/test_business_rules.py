"""Business rules, proven through TestingApi only.

No controllers, shell or view are touched, and every gateway is a fake: in-memory rooms
and bookings, a FakeClock, and a FakeModelAdapter. Nothing here can reach the network.
"""
import unittest
from datetime import datetime

from study_room_booking.entities.booking import BookingStatus
from study_room_booking.entities.room import Room
from study_room_booking.interface_adapters.gateways.fake_model_adapter import (
    DEFAULT_SCRIPTS,
    FakeModelAdapter,
    Scenario,
)
from study_room_booking.interface_adapters.testing_api import TestingApi
from study_room_booking.use_cases.classify_request import Intent
from study_room_booking.use_cases.model_gateway import ModelGateway

ROOMS = [Room("R1", "Room 1", "Library", 4), Room("R2", "Room 2", "Library", 8)]


def at(day, hour, minute=0):
    return datetime(2026, 11, day, hour, minute)


NOW = at(1, 9)


class BookRoomRulesTest(unittest.TestCase):
    def setUp(self):
        self.api = TestingApi(ROOMS, now=NOW)

    def test_a_student_can_book_a_free_room_that_fits_their_group(self):
        out = self.api.book_room("s1", "R1", at(2, 10), at(2, 12), group_size=3)

        self.assertTrue(out.ok)
        self.assertEqual(out.response.room_id, "R1")
        self.assertEqual((out.response.start, out.response.end), (at(2, 10), at(2, 12)))
        self.assertEqual(self.api.get_booking(out.response.booking_id).student_id, "s1")

    def test_a_booking_that_ends_when_another_begins_does_not_conflict(self):
        self.api.seed_booking("R1", "other", at(2, 10), at(2, 11))

        out = self.api.book_room("s1", "R1", at(2, 11), at(2, 12))

        self.assertTrue(out.ok)

    def test_a_room_cannot_be_double_booked_for_overlapping_times(self):
        self.api.seed_booking("R1", "other", at(2, 10), at(2, 12))

        out = self.api.book_room("s1", "R1", at(2, 11), at(2, 13))

        self.assertFalse(out.ok)
        self.assertIn("already booked", out.error)

    def test_a_booking_may_not_exceed_three_hours(self):
        out = self.api.book_room("s1", "R1", at(2, 10), at(2, 14))
        self.assertIn("at most 3 hours", out.error)

    def test_a_group_larger_than_the_room_capacity_is_refused(self):
        out = self.api.book_room("s1", "R1", at(2, 10), at(2, 11), group_size=5)
        self.assertIn("does not fit", out.error)

    def test_bookings_must_start_in_the_future(self):
        out = self.api.book_room("s1", "R1", at(1, 8, 30), at(1, 9, 30))
        self.assertIn("future", out.error)

    def test_a_student_may_hold_at_most_two_upcoming_bookings(self):
        self.api.seed_booking("R1", "s1", at(2, 9), at(2, 10))
        self.api.seed_booking("R2", "s1", at(2, 9), at(2, 10))

        out = self.api.book_room("s1", "R1", at(3, 9), at(3, 10))

        self.assertIn("at most 2", out.error)

    def test_an_unknown_room_cannot_be_booked(self):
        out = self.api.book_room("s1", "NOPE", at(2, 10), at(2, 11))
        self.assertIn("does not exist", out.error)


class CancelBookingRulesTest(unittest.TestCase):
    def setUp(self):
        self.api = TestingApi(ROOMS, now=NOW)

    def test_a_student_can_cancel_their_own_future_booking_and_the_room_is_freed(self):
        booking_id = self.api.seed_booking("R1", "s1", at(2, 10), at(2, 12))

        out = self.api.cancel_booking("s1", booking_id)

        self.assertTrue(out.ok)
        self.assertIs(self.api.get_booking(booking_id).status, BookingStatus.CANCELLED)
        self.assertTrue(self.api.book_room("s2", "R1", at(2, 10), at(2, 12)).ok)

    def test_a_booking_that_has_already_started_cannot_be_cancelled(self):
        booking_id = self.api.seed_booking("R1", "s1", at(2, 10), at(2, 12))
        self.api.set_now(at(2, 10))  # exactly at the start time

        out = self.api.cancel_booking("s1", booking_id)

        self.assertIn("started", out.error)
        self.assertIs(self.api.get_booking(booking_id).status, BookingStatus.CONFIRMED)

    def test_a_student_cannot_cancel_someone_elses_booking(self):
        booking_id = self.api.seed_booking("R1", "s1", at(2, 10), at(2, 12))
        out = self.api.cancel_booking("intruder", booking_id)
        self.assertIn("own bookings", out.error)

    def test_a_booking_cannot_be_cancelled_twice(self):
        booking_id = self.api.seed_booking(
            "R1", "s1", at(2, 10), at(2, 12), status=BookingStatus.CANCELLED
        )
        self.assertIn("already cancelled", self.api.cancel_booking("s1", booking_id).error)

    def test_cancelling_an_unknown_booking_is_reported(self):
        self.assertIn("does not exist", self.api.cancel_booking("s1", "B9999").error)


class ListAvailableRoomsRulesTest(unittest.TestCase):
    def setUp(self):
        self.api = TestingApi(ROOMS, now=NOW)

    def ids(self, out):
        return [r.room_id for r in out.response.rooms]

    def test_only_free_rooms_that_fit_the_group_are_offered(self):
        self.api.seed_booking("R1", "other", at(2, 10), at(2, 12))

        both_free = self.api.list_available_rooms(at(2, 14), at(2, 15), group_size=2)
        r1_taken = self.api.list_available_rooms(at(2, 11), at(2, 12), group_size=2)
        too_big_for_r1 = self.api.list_available_rooms(at(2, 14), at(2, 15), group_size=6)

        self.assertEqual(self.ids(both_free), ["R1", "R2"])
        self.assertEqual(self.ids(r1_taken), ["R2"])
        self.assertEqual(self.ids(too_big_for_r1), ["R2"])

    def test_a_cancelled_booking_no_longer_blocks_a_room(self):
        self.api.seed_booking("R1", "s1", at(2, 10), at(2, 12), status=BookingStatus.CANCELLED)

        out = self.api.list_available_rooms(at(2, 10), at(2, 12))

        self.assertEqual(self.ids(out), ["R1", "R2"])

    def test_an_invalid_time_window_is_rejected(self):
        out = self.api.list_available_rooms(at(2, 12), at(2, 10))
        self.assertIn("after start", out.error)


def model_saying(label):
    """A FakeModelAdapter whose good answer is `label`; malformed/off-topic stay default."""
    return FakeModelAdapter(Scenario.GOOD, {**DEFAULT_SCRIPTS, Scenario.GOOD: label})


class UnavailableModel(ModelGateway):
    def complete(self, prompt):
        raise ConnectionError("model is down")


class ClassifyRequestRulesTest(unittest.TestCase):
    def test_a_clear_message_is_routed_to_the_matching_command(self):
        api = TestingApi(ROOMS, now=NOW, model=model_saying(" Book\n"))  # sloppy casing/spacing

        out = api.classify_request("I need a room tomorrow at 2")

        self.assertTrue(out.ok)
        self.assertIs(out.response.intent, Intent.BOOK)
        self.assertIn("book", out.view_model.lines[0])

    def test_the_students_message_is_what_is_sent_to_the_assistant(self):
        api = TestingApi(ROOMS, now=NOW, model=model_saying("cancel"))
        api.classify_request("please drop my reservation")
        self.assertIn("please drop my reservation", api.model.prompts[0])

    def test_a_blank_message_is_rejected_without_calling_the_assistant(self):
        api = TestingApi(ROOMS, now=NOW, model=model_saying("book"))

        out = api.classify_request("   ")

        self.assertFalse(out.ok)
        self.assertIsNone(out.handoff)
        self.assertEqual(api.model.prompts, [])

    def test_an_unusable_assistant_answer_hands_the_student_to_library_staff(self):
        for scenario in (Scenario.MALFORMED, Scenario.OFF_TOPIC):
            with self.subTest(scenario=scenario.name):
                api = TestingApi(ROOMS, now=NOW, model=FakeModelAdapter(scenario))

                out = api.classify_request("I need a room tomorrow at 2")

                self.assertFalse(out.ok)
                self.assertIsNone(out.response)  # nothing is acted on
                self.assertIsNotNone(out.handoff)  # the off-ramp fired
                self.assertIn("library staff", out.view_model.lines[0])
                self.assertEqual(api.bookings_for_room("R1"), [])  # no side effects

    def test_an_unavailable_assistant_hands_the_student_to_library_staff(self):
        api = TestingApi(ROOMS, now=NOW, model=UnavailableModel())

        out = api.classify_request("I need a room")

        self.assertIsNotNone(out.handoff)
        self.assertIn("library staff", out.view_model.lines[0])


if __name__ == "__main__":
    unittest.main()
