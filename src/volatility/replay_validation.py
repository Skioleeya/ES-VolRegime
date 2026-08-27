"""Validate that replay prefixes are invariant to future bars."""

from datetime import datetime, timedelta, timezone

from .engine import RegimeSnapshot, build_regime_snapshots
from src.historical.models import HistoricalBar

UTC = timezone.utc


def validate_prefix_invariance(
    bars: tuple[HistoricalBar, ...],
    as_of_utc: datetime,
) -> int:
    """Return checked snapshot count or raise if future bars alter a prefix."""
    if as_of_utc.tzinfo is None or as_of_utc.utcoffset() is None:
        raise ValueError("as_of_utc must be timezone-aware")
    as_of_utc = as_of_utc.astimezone(UTC)
    ordered = tuple(sorted(bars, key=lambda bar: bar.bar_start_utc))
    prefix_bars = tuple(
        bar for bar in ordered
        if bar.bar_start_utc + timedelta(minutes=5) <= as_of_utc
    )
    full = build_regime_snapshots(ordered)
    prefix = build_regime_snapshots(prefix_bars)
    prefix_times = {bar.bar_start_utc for bar in prefix_bars}
    expected = tuple(snapshot for snapshot in full if snapshot.metric.bar_start_utc in prefix_times)
    if expected != prefix:
        raise AssertionError("future bars changed an earlier replay prefix")
    return len(prefix)
