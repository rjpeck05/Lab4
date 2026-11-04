"""Presenter unit tests: response in, display-ready view model out.

No controllers, shell, use cases or gateways are involved, so there is no UI to import.
"""
import unittest
from datetime import datetime

from study_room_booking.interface_adapters.book_room import BookRoomPresenter
from study_room_booking.interface_adapters.cancel_booking import CancelBookingPresenter
from study_room_booking.interface_adapters.classify_request import ClassifyRequestPresenter
from study_room_booking.interface_adapters.list_available_rooms import ListAvailableRoomsPresenter
from study_room_booking.interface_adapters.view_model import ViewModel
from study_room_booking.use_cases.book_room import BookRoomResponse
from study_room_booking.use_cases.cancel_booking import CancelBookingResponse
from study_room_booking.use_cases.classify_request import ClassifyRequestResponse, Intent
from study_room_booking.use_cases.list_available_rooms import (
    AvailableRoom,
    ListAvailableRoomsResponse,
)

START, END = datetime(2026, 11, 2, 10, 0), datetime(2026, 11, 2, 12, 0)


class BookRoomPresenterTest(unittest.TestCase):
    def test_a_confirmed_booking_is_shown_with_its_reference_room_and_times(self):
        presenter = BookRoomPresenter()
        presenter.present_booking(BookRoomResponse("B0001", "R1", "s1", START, END))

        self.assertTrue(presenter.view_model.ok)
        self.assertEqual(
            presenter.view_model.messages,
            ("Booked! Reference B0001: room R1, 2026-11-02 10:00 -> 12:00.",),
        )

    def test_a_refused_booking_is_shown_as_a_failed_view_with_the_reason(self):
        presenter = BookRoomPresenter()
        presenter.present_error("Room 1 is already booked at that time.")

        self.assertEqual(
            presenter.view_model,
            ViewModel(False, ("Error: Room 1 is already booked at that time.",)),
        )

    def test_nothing_is_shown_before_a_use_case_has_reported(self):
        self.assertEqual(BookRoomPresenter().view_model, ViewModel(True, ()))


class CancelBookingPresenterTest(unittest.TestCase):
    def test_a_cancellation_is_confirmed_by_booking_reference(self):
        presenter = CancelBookingPresenter()
        presenter.present_cancellation(CancelBookingResponse("B0007"))
        self.assertEqual(presenter.view_model, ViewModel(True, ("Booking B0007 cancelled.",)))

    def test_a_refused_cancellation_is_shown_as_a_failed_view_with_the_reason(self):
        presenter = CancelBookingPresenter()
        presenter.present_error("You can only cancel your own bookings.")
        self.assertFalse(presenter.view_model.ok)
        self.assertEqual(
            presenter.view_model.messages, ("Error: You can only cancel your own bookings.",)
        )


class ListAvailableRoomsPresenterTest(unittest.TestCase):
    def test_free_rooms_are_listed_under_the_time_window_with_building_and_capacity(self):
        presenter = ListAvailableRoomsPresenter()
        rooms = (AvailableRoom("R1", "Room 1", "Library", 4), AvailableRoom("R2", "Room 2", "Annex", 8))
        presenter.present_rooms(ListAvailableRoomsResponse(START, END, rooms))

        header, first, second = presenter.view_model.messages
        self.assertTrue(presenter.view_model.ok)
        self.assertEqual(header, "Available 2026-11-02 10:00 -> 12:00:")
        self.assertIn("R1", first)
        self.assertIn("Library, seats 4", first)
        self.assertIn("Annex, seats 8", second)

    def test_when_no_room_is_free_the_student_is_told_so_and_it_is_not_an_error(self):
        presenter = ListAvailableRoomsPresenter()
        presenter.present_rooms(ListAvailableRoomsResponse(START, END, ()))
        self.assertEqual(
            presenter.view_model, ViewModel(True, ("No rooms available for that time.",))
        )

    def test_an_invalid_request_is_shown_as_a_failed_view_with_the_reason(self):
        presenter = ListAvailableRoomsPresenter()
        presenter.present_error("End time must be after start time.")
        self.assertEqual(
            presenter.view_model, ViewModel(False, ("Error: End time must be after start time.",))
        )


class ClassifyRequestPresenterTest(unittest.TestCase):
    def test_a_recognised_intent_is_named_back_to_the_student(self):
        presenter = ClassifyRequestPresenter()
        presenter.present_intent(ClassifyRequestResponse(Intent.AVAILABLE))
        self.assertEqual(
            presenter.view_model, ViewModel(True, ("That looks like a 'available' request.",))
        )

    def test_a_handoff_tells_the_student_to_see_library_staff_and_hides_the_technical_reason(self):
        presenter = ClassifyRequestPresenter()
        presenter.present_handoff("The assistant gave an answer that could not be used.")

        view = presenter.view_model
        self.assertFalse(view.ok)
        self.assertIn("library staff", view.messages[0])
        self.assertNotIn("assistant", view.messages[0].lower())

    def test_a_rejected_message_is_shown_as_a_failed_view_with_the_reason(self):
        presenter = ClassifyRequestPresenter()
        presenter.present_error("Please type a message to classify.")
        self.assertEqual(
            presenter.view_model,
            ViewModel(False, ("Error: Please type a message to classify.",)),
        )


if __name__ == "__main__":
    unittest.main()
