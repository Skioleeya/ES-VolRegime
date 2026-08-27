"""Deterministic request planning for missing completed bars."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .models import HistoricalRequest, QualifiedContract


def build_gap_requests(
    contract: QualifiedContract,
    missing: tuple[datetime, ...],
    bar_minutes: int = 5,
) -> tuple[HistoricalRequest, ...]:
    """Merge adjacent missing starts into bounded historical requests."""
    if bar_minutes <= 0:
        raise ValueError("bar_minutes must be positive")
    ordered = sorted(set(missing))
    if not ordered:
        return ()
    step = timedelta(minutes=bar_minutes)
    groups: list[list[datetime]] = [[ordered[0]]]
    for value in ordered[1:]:
        if value - groups[-1][-1] == step:
            groups[-1].append(value)
        else:
            groups.append([value])
    return tuple(_request(contract, group[0], group[-1] + step, step) for group in groups)


def _request(contract: QualifiedContract, start: datetime, end: datetime, step: timedelta) -> HistoricalRequest:
    zone = ZoneInfo(contract.time_zone)
    return HistoricalRequest(
        contract=contract,
        start_utc=start.astimezone(timezone.utc),
        end_utc=end.astimezone(timezone.utc),
        start_et=start.astimezone(zone),
        end_et=end.astimezone(zone),
        duration_str=f"{int((end - start).total_seconds())} S",
    )
