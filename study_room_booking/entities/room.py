from dataclasses import dataclass


@dataclass(frozen=True)
class Room:
    id: str
    name: str
    building: str
    capacity: int

    def fits(self, group_size: int) -> bool:
        return 1 <= group_size <= self.capacity
