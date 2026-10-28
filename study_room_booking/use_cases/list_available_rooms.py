from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from study_room_booking.entities.booking import Booking
from study_room_booking.entities.errors import DomainError
from study_room_booking.entities.time_slot import TimeSlot

from .booking_gateway import BookingGateway
from .room_gateway import RoomGateway


@dataclass(frozen=True)
class ListAvailableRoomsRequest:
    start: datetime
    end: datetime
    group_size: int


@dataclass(frozen=True)
class AvailableRoom:
    room_id: str
    name: str
    building: str
    capacity: int


@dataclass(frozen=True)
class ListAvailableRoomsResponse:
    start: datetime
    end: datetime
    rooms: tuple[AvailableRoom, ...]


class ListAvailableRoomsOutputBoundary(ABC):
    @abstractmethod
    def present_rooms(self, response: ListAvailableRoomsResponse) -> None: ...

    @abstractmethod
    def present_error(self, message: str) -> None: ...


class ListAvailableRooms:
    def __init__(
        self,
        rooms: RoomGateway,
        bookings: BookingGateway,
        output: ListAvailableRoomsOutputBoundary,
    ) -> None:
        self._rooms = rooms
        self._bookings = bookings
        self._output = output

    def execute(self, request: ListAvailableRoomsRequest) -> None:
        try:
            slot = TimeSlot(request.start, request.end)
        except DomainError as error:
            self._output.present_error(str(error))
            return

        probe = Booking(id="probe", room_id="", student_id="", slot=slot)
        available = []
        for room in self._rooms.list_all():
            if not room.fits(request.group_size):
                continue
            probe.room_id = room.id
            if any(probe.conflicts_with(b) for b in self._bookings.list_for_room(room.id)):
                continue
            available.append(AvailableRoom(room.id, room.name, room.building, room.capacity))

        self._output.present_rooms(
            ListAvailableRoomsResponse(slot.start, slot.end, tuple(available))
        )
