from enum import Enum


class OrderStatus(str, Enum):
    RESERVED = "reserved"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    FAILED = "failed"
    REFUNDED = "refunded"


class Source(str, Enum):
    USER = "user"
    WEBHOOK = "webhook"
    WORKER = "worker"


S = OrderStatus

# Payment webhooks can arrive before we process the reservation, so RESERVED -> PAID is allowed.
ALLOWED: dict[OrderStatus, frozenset[OrderStatus]] = {
    S.RESERVED: frozenset({S.PAYMENT_PENDING, S.PAID, S.EXPIRED, S.FAILED}),
    S.PAYMENT_PENDING: frozenset({S.PAID, S.EXPIRED, S.FAILED}),
    S.PAID: frozenset({S.CONFIRMED, S.REFUNDED}),
    # Payment arriving after expiry is auto-refunded (see README policy).
    S.EXPIRED: frozenset({S.REFUNDED}),
    # Terminal states: a late duplicate webhook must never revive them.
    S.CONFIRMED: frozenset(),
    S.FAILED: frozenset(),
    S.REFUNDED: frozenset(),
}


class InvalidTransition(Exception):
    def __init__(self, current: OrderStatus, target: OrderStatus) -> None:
        super().__init__(f"Invalid transition: {current.value} -> {target.value}")
        self.current = current
        self.target = target


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    return target in ALLOWED[current]


def assert_transition(current: OrderStatus, target: OrderStatus) -> None:
    if not can_transition(current, target):
        raise InvalidTransition(current, target)
