"""As-of historical replay primitives."""

from datetime import datetime, timedelta, timezone
from typing import Callable, TypeVar

from .models import HistoricalBar

T = TypeVar("T")
UTC = timezone.utc


def replay_as_of(
    bars: tuple[HistoricalBar, ...],
    as_of_utc: datetime,
    evaluator: Callable[[tuple[HistoricalBar, ...]], T],
) -> T:
    """Evaluate only bars fully completed by ``as_of_utc``."""
    if as_of_utc.tzinfo is None or as_of_utc.utcoffset() is None:
        raise ValueError("as_of_utc must be timezone-aware")
    as_of_utc = as_of_utc.astimezone(UTC)
    visible = tuple(
        bar for bar in sorted(bars, key=lambda value: value.bar_start_utc)
        if bar.bar_start_utc + timedelta(minutes=5) <= as_of_utc
    )
    return evaluator(visible)

