from datetime import datetime

from study_room_booking.use_cases.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now()
