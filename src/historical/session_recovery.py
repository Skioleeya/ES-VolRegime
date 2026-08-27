"""Recover missing bars for one labelled CME session."""

from dataclasses import dataclass
from datetime import date, datetime, timezone

from .collector import HistoricalCollector
from .coverage import missing_bar_starts, expected_bar_starts
from .models import QualifiedContract
from .normalizer import normalize_completed_bar
from .recovery import build_gap_requests
from .repository import HistoricalRepository


@dataclass(frozen=True)
class RecoveryResult:
    session_date: date
    requested_bars: int
    recovered_bars: int
    remaining_bars: int


def recover_session(
    session_date: date,
    contract: QualifiedContract,
    repository: HistoricalRepository,
    collector: HistoricalCollector,
    server_now: datetime,
) -> RecoveryResult:
    """Fetch and persist every currently missing completed bar in a session."""
    expected = expected_bar_starts(session_date)
    existing = _existing_starts(repository, contract, expected)
    missing = missing_bar_starts(session_date, existing)
    requests = build_gap_requests(contract, missing)
    recovered = 0
    for request in requests:
        collected = collector.collect(request)
        bars = tuple(normalize_completed_bar(raw, contract, server_now) for raw in collected.bars)
        target = tuple(bar for bar in bars if bar.bar_start_utc in set(missing))
        repository.save_bars(target)
        recovered += len(target)
    actual = _existing_starts(repository, contract, expected)
    remaining = len(missing_bar_starts(session_date, actual))
    repository.save_coverage(session_date.isoformat(), len(expected), len(actual), remaining, "COMPLETE" if remaining == 0 else "DEGRADED")
    return RecoveryResult(session_date, len(missing), recovered, remaining)


def _existing_starts(repository, contract, expected):
    start, end = expected[0], expected[-1]
    bars = repository.load_bars(contract)
    return tuple(bar.bar_start_utc for bar in bars if start <= bar.bar_start_utc <= end)
