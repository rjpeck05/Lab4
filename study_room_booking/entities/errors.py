class DomainError(Exception):
    """Base class for every business-rule violation."""


class InvalidTimeSlot(DomainError):
    pass


class BookingRuleViolation(DomainError):
    pass


class RoomNotFound(DomainError):
    pass


class BookingNotFound(DomainError):
    pass
