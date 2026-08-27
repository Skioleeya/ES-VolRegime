"""Bounded retry policy for recoverable broker operations."""

from collections.abc import Callable
from time import sleep
from typing import TypeVar


T = TypeVar("T")


def retry_operation(
    operation: Callable[[], T],
    attempts: int = 3,
    delay_seconds: float = 5.0,
    sleeper: Callable[[float], None] = sleep,
) -> T:
    """Retry a failing operation a finite number of times, then re-raise."""
    if attempts < 1:
        raise ValueError("attempts must be positive")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must not be negative")
    for attempt in range(attempts):
        try:
            return operation()
        except Exception:
            if attempt == attempts - 1:
                raise
            sleeper(delay_seconds * (attempt + 1))
    raise RuntimeError("unreachable")
