"""Historical same-elapsed-time benchmarks for phase metrics."""

from collections import defaultdict
from decimal import Decimal

from .models import BenchmarkResult, PhaseMetric

MINIMUM_HISTORY_SAMPLES = 20


def compare_to_history(
    current: PhaseMetric,
    history: tuple[PhaseMetric, ...],
    minimum_samples: int = MINIMUM_HISTORY_SAMPLES,
) -> BenchmarkResult:
    """Compare one observation only with prior sessions at the same key."""
    if minimum_samples < 1:
        raise ValueError("minimum_samples must be positive")
    samples = [
        metric for metric in history
        if metric.phase == current.phase
        and metric.elapsed_minutes == current.elapsed_minutes
        and metric.session_date < current.session_date
    ]
    if len(samples) < minimum_samples:
        return BenchmarkResult(current.phase, current.elapsed_minutes, None, None, len(samples))
    return BenchmarkResult(
        current.phase,
        current.elapsed_minutes,
        _percentile(current.realized_volatility, [item.realized_volatility for item in samples]),
        _percentile(current.range_value, [item.range_value for item in samples]),
        len(samples),
    )


def _percentile(value: Decimal, samples: list[Decimal]) -> Decimal:
    """Return the empirical percentile using the count at or below value."""
    return (Decimal(sum(sample <= value for sample in samples)) / Decimal(len(samples)) * 100).quantize(Decimal("0.01"))
