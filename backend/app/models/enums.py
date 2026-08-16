from enum import Enum
from typing import TypeVar


class UserRole(str, Enum):
    ORGANIZER = "ORGANIZER"
    CUSTOMER = "CUSTOMER"
    GATE = "GATE"


class EventStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CANCELLED = "CANCELLED"


class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class PaymentStatus(str, Enum):
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"


class RefundStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    FAILED = "FAILED"


class TicketStatus(str, Enum):
    ACTIVE = "ACTIVE"
    USED = "USED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class ValidationResult(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    ALREADY_USED = "ALREADY_USED"
    WRONG_EVENT = "WRONG_EVENT"


EnumType = TypeVar("EnumType", bound=Enum)


def enum_values(enum_class: type[EnumType]) -> list[str]:
    return [str(item.value) for item in enum_class]
