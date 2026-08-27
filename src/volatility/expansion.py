"""Derive auditable RV change metrics without inventing regime thresholds."""

from dataclasses import dataclass
from decimal import Decimal

from .models import PhaseMetric


@dataclass(frozen=True)
class RVChange:
    """Change in cumulative RV between adjacent completed bars."""

    metric: PhaseMetric
    change: Decimal
    percentage_change: Decimal | None
    slope: Decimal
    acceleration: Decimal | None


def calculate_rv_changes(metrics: tuple[PhaseMetric, ...]) -> tuple[RVChange, ...]:
    """Calculate changes only within the same phase and research session."""
    ordered = sorted(metrics, key=lambda metric: metric.bar_start_utc)
    result: list[RVChange] = []
    previous: PhaseMetric | None = None
    previous_change: Decimal | None = None
    for metric in ordered:
        same_sequence = previous is not None and _same_sequence(metric, previous)
        change = metric.realized_volatility - previous.realized_volatility if same_sequence else Decimal("0")
        percentage = _percentage_change(previous.realized_volatility, change) if same_sequence else None
        acceleration = change - previous_change if same_sequence and previous_change is not None else None
        result.append(RVChange(metric, change, percentage, change, acceleration))
        previous = metric
        previous_change = change if same_sequence else None
    return tuple(result)


def _same_sequence(current: PhaseMetric, previous: PhaseMetric) -> bool:
    return current.phase == previous.phase and current.session_date == previous.session_date


def _percentage_change(previous: Decimal, change: Decimal) -> Decimal | None:
    if previous == 0:
        return None
    return (change / previous * 100).quantize(Decimal("0.01"))
