from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from study_room_booking.entities.room import Room


class RoomGateway(ABC):
    """What the use cases need to know about the university's study rooms."""

    @abstractmethod
    def get(self, room_id: str) -> Optional[Room]: ...

    @abstractmethod
    def list_all(self) -> list[Room]: ...
