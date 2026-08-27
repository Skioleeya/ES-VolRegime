"""Deterministic pacing gate for IBKR historical requests."""

from collections import deque
from dataclasses import dataclass, field
from time import monotonic, sleep
from typing import Callable


@dataclass
class HistoricalPacer:
    """Enforce conservative historical-request intervals.

    The injected clock and sleeper make the policy independently testable.
    A request signature is the contract, exchange, and tick type tuple used by
    IBKR's small-bar pacing rule.
    """

    now: Callable[[], float] = monotonic
    sleeper: Callable[[float], None] = sleep
    same_signature_gap: float = 15.0
    signature_window: float = 2.0
    signature_limit: int = 5
    global_window: float = 600.0
    global_limit: int = 60
    _last_by_signature: dict[tuple[str, str, str], float] = field(default_factory=dict)
    _signature_history: dict[tuple[str, str, str], deque[float]] = field(default_factory=dict)
    _global_history: deque[float] = field(default_factory=deque)

    def acquire(self, signature: tuple[str, str, str]) -> None:
        """Block until submitting this request is within the configured limits."""
        while True:
            delay = self._required_delay(signature)
            if delay <= 0:
                self._record(signature)
                return
            self.sleeper(delay)

    def _required_delay(self, signature: tuple[str, str, str]) -> float:
        current = self.now()
        self._prune(current)
        delays = [self._same_request_delay(signature, current)]
        delays.append(self._signature_window_delay(signature, current))
        delays.append(self._global_window_delay(current))
        return max(delays)

    def _same_request_delay(self, signature: tuple[str, str, str], current: float) -> float:
        previous = self._last_by_signature.get(signature)
        if previous is None:
            return 0.0
        return max(0.0, previous + self.same_signature_gap - current)

    def _signature_window_delay(self, signature: tuple[str, str, str], current: float) -> float:
        history = self._signature_history.get(signature, deque())
        if len(history) < self.signature_limit:
            return 0.0
        return max(0.0, history[0] + self.signature_window - current)

    def _global_window_delay(self, current: float) -> float:
        if len(self._global_history) < self.global_limit:
            return 0.0
        return max(0.0, self._global_history[0] + self.global_window - current)

    def _record(self, signature: tuple[str, str, str]) -> None:
        current = self.now()
        history = self._signature_history.setdefault(signature, deque())
        history.append(current)
        self._global_history.append(current)
        self._last_by_signature[signature] = current

    def _prune(self, current: float) -> None:
        cutoff = current - self.global_window
        while self._global_history and self._global_history[0] <= cutoff:
            self._global_history.popleft()
        for history in self._signature_history.values():
            while history and history[0] <= current - self.signature_window:
                history.popleft()

