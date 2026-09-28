import itertools

import pytest

from app.domain.state_machine import (
    ALLOWED,
    InvalidTransition,
    OrderStatus,
    assert_transition,
    can_transition,
)

S = OrderStatus

VALID = [
    (S.RESERVED, S.PAYMENT_PENDING),
    (S.RESERVED, S.PAID),          # payment.succeeded may arrive before processing
    (S.RESERVED, S.EXPIRED),
    (S.RESERVED, S.FAILED),
    (S.PAYMENT_PENDING, S.PAID),
    (S.PAYMENT_PENDING, S.FAILED),
    (S.PAYMENT_PENDING, S.EXPIRED),
    (S.PAID, S.CONFIRMED),
    (S.PAID, S.REFUNDED),
    (S.EXPIRED, S.REFUNDED),
]


@pytest.mark.parametrize("current,target", VALID)
def test_valid_transitions_are_allowed(current: S, target: S) -> None:
    assert can_transition(current, target)
    assert_transition(current, target)  # must not raise


@pytest.mark.parametrize("target", list(S))
def test_failed_can_never_move_anywhere(target: S) -> None:
    # A late duplicate webhook must never move failed -> paid (or anything).
    with pytest.raises(InvalidTransition):
        assert_transition(S.FAILED, target)


def test_late_paid_after_failed_is_rejected() -> None:
    with pytest.raises(InvalidTransition):
        assert_transition(S.FAILED, S.PAID)


@pytest.mark.parametrize("terminal", [S.CONFIRMED, S.FAILED, S.REFUNDED])
def test_terminal_states_have_no_exits(terminal: S) -> None:
    assert ALLOWED[terminal] == frozenset()


def test_every_pair_not_explicitly_allowed_is_rejected() -> None:
    allowed = set(VALID)
    for current, target in itertools.product(S, S):
        if (current, target) in allowed:
            continue
        with pytest.raises(InvalidTransition):
            assert_transition(current, target)


def test_self_transition_is_rejected() -> None:
    for status in S:
        assert not can_transition(status, status)


def test_every_status_has_an_entry() -> None:
    assert set(ALLOWED) == set(S)
