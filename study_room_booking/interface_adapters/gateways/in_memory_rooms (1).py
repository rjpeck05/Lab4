from __future__ import annotations

from typing import Iterable, Optional

from study_room_booking.entities.room import Room
from study_room_booking.use_cases.room_gateway import RoomGateway


class InMemoryRoomGateway(RoomGateway):
    def __init__(self, rooms: Iterable[Room] = ()) -> None:
        self._rooms = {room.id: room for room in rooms}

    def get(self, room_id: str) -> Optional[Room]:
        return self._rooms.get(room_id)

    def list_all(self) -> list[Room]:
        return sorted(self._rooms.values(), key=lambda r: r.id)
