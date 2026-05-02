"""Run state machine.

Linear pipeline:
    PLANNED -> PRECHECK -> R1 -> V1 -> R2 -> V2 -> R3 -> V3 -> JUDGE -> METRICS -> FINALIZED
Any state may also transition to FAILED on a non-recoverable error.
"""

from __future__ import annotations

from dataclasses import dataclass

from benchmark.core.domain import RunState


class InvalidTransitionError(RuntimeError):
    """Raised when a state transition is not permitted."""


@dataclass(frozen=True, slots=True)
class StateTransition:
    src: RunState
    dst: RunState
    label: str


# Allowed forward transitions, in declaration order.
ALLOWED_TRANSITIONS: dict[RunState, set[RunState]] = {
    RunState.PLANNED: {RunState.PRECHECK, RunState.FAILED},
    RunState.PRECHECK: {RunState.R1, RunState.FAILED},
    RunState.R1: {RunState.V1, RunState.FAILED},
    RunState.V1: {RunState.R2, RunState.JUDGE, RunState.FAILED},
    RunState.R2: {RunState.V2, RunState.FAILED},
    RunState.V2: {RunState.R3, RunState.JUDGE, RunState.FAILED},
    RunState.R3: {RunState.V3, RunState.FAILED},
    RunState.V3: {RunState.JUDGE, RunState.FAILED},
    RunState.JUDGE: {RunState.METRICS, RunState.FAILED},
    RunState.METRICS: {RunState.FINALIZED, RunState.FAILED},
    RunState.FINALIZED: set(),
    RunState.FAILED: set(),
}


class StateMachine:
    """Pure state-machine logic, free of I/O."""

    def __init__(self, current: RunState = RunState.PLANNED) -> None:
        self._current = current

    @property
    def state(self) -> RunState:
        return self._current

    def can_transition(self, dst: RunState) -> bool:
        return dst in ALLOWED_TRANSITIONS.get(self._current, set())

    def transition(self, dst: RunState) -> StateTransition:
        if not self.can_transition(dst):
            msg = f"Invalid transition {self._current} -> {dst}"
            raise InvalidTransitionError(msg)
        prev = self._current
        self._current = dst
        return StateTransition(src=prev, dst=dst, label=f"{prev}->{dst}")

    def is_terminal(self) -> bool:
        return self._current in (RunState.FINALIZED, RunState.FAILED)
