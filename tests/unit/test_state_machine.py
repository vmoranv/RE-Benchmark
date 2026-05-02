"""Tests for the run state machine."""

from __future__ import annotations

import pytest

from benchmark.core.domain import RunState
from benchmark.core.orchestration.state_machine import (
    InvalidTransitionError,
    StateMachine,
)


def test_happy_path():
    sm = StateMachine()
    for nxt in [
        RunState.PRECHECK,
        RunState.R1,
        RunState.V1,
        RunState.R2,
        RunState.V2,
        RunState.R3,
        RunState.V3,
        RunState.JUDGE,
        RunState.METRICS,
        RunState.FINALIZED,
    ]:
        sm.transition(nxt)
    assert sm.state == RunState.FINALIZED
    assert sm.is_terminal()


def test_failed_is_terminal_from_anywhere():
    for src in [RunState.PLANNED, RunState.R2, RunState.JUDGE, RunState.METRICS]:
        sm = StateMachine(src)
        sm.transition(RunState.FAILED)
        assert sm.is_terminal()


def test_invalid_transition_rejected():
    sm = StateMachine()  # PLANNED
    with pytest.raises(InvalidTransitionError):
        sm.transition(RunState.R1)  # must go through PRECHECK


def test_v1_can_skip_to_judge():
    sm = StateMachine(RunState.V1)
    sm.transition(RunState.JUDGE)
    assert sm.state == RunState.JUDGE


def test_finalized_has_no_outgoing():
    sm = StateMachine(RunState.FINALIZED)
    assert not sm.can_transition(RunState.METRICS)
    with pytest.raises(InvalidTransitionError):
        sm.transition(RunState.METRICS)
