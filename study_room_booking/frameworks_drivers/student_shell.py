from __future__ import annotations

import cmd

from study_room_booking.interface_adapters.book_room import BookRoomController
from study_room_booking.interface_adapters.cancel_booking import CancelBookingController
from study_room_booking.interface_adapters.list_available_rooms import ListAvailableRoomsController


class StudentShell(cmd.Cmd):
    """Terminal a student types into. Delivery mechanism only; no rules live here."""

    intro = (
        "Study room booking. Type 'help' for commands. Dates look like 2026-11-02T14:00.\n"
        "Data lives in memory and is lost on exit."
    )
    prompt = "rooms> "

    def __init__(
        self,
        book_room: BookRoomController,
        cancel_booking: CancelBookingController,
        list_available_rooms: ListAvailableRoomsController,
    ) -> None:
        super().__init__()
        self._book_room = book_room
        self._cancel_booking = cancel_booking
        self._list_available_rooms = list_available_rooms

    @staticmethod
    def _run(action, usage: str, args: str, min_args: int) -> None:
        parts = args.split()
        if len(parts) < min_args:
            print(f"Usage: {usage}")
            return
        try:
            view_model = action(*parts)
        except TypeError:
            print(f"Usage: {usage}")
            return
        for line in view_model.lines:
            print(line)

    def do_available(self, args: str) -> None:
        """available <start> <end> [group_size]"""
        self._run(self._list_available_rooms.find, "available <start> <end> [group_size]", args, 2)

    def do_book(self, args: str) -> None:
        """book <student_id> <room_id> <start> <end> [group_size]"""
        self._run(
            self._book_room.book, "book <student_id> <room_id> <start> <end> [group_size]", args, 4
        )

    def do_cancel(self, args: str) -> None:
        """cancel <student_id> <booking_id>"""
        self._run(self._cancel_booking.cancel, "cancel <student_id> <booking_id>", args, 2)

    def do_quit(self, _args: str) -> bool:
        """Leave the program."""
        return True

    do_exit = do_quit
    do_EOF = do_quit
