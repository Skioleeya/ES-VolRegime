from datetime import date, datetime, timezone
from decimal import Decimal

from src.volatility import BenchmarkResult, PhaseMetric, ResearchPhase, compare_to_history

UTC = timezone.utc


def metric(day: int, value: int, phase=ResearchPhase.CASH, elapsed=60):
    return PhaseMetric(phase, date(2026, 1, day), elapsed, datetime(2026, 1, day, tzinfo=UTC), Decimal(value), Decimal(value), Decimal(value), Decimal(value))


def test_benchmark_requires_twenty_same_key_history_samples():
    current = metric(31, 25)
    history = tuple(metric(day, day) for day in range(1, 21))
    result = compare_to_history(current, history)
    assert isinstance(result, BenchmarkResult)
    assert result.available is True
    assert result.sample_count == 20
    assert result.realized_volatility_percentile == Decimal("100.00")


def test_benchmark_is_unavailable_without_enough_history():
    result = compare_to_history(metric(31, 25), tuple(metric(day, day) for day in range(1, 6)))
    assert result.available is False
    assert result.realized_volatility_percentile is None
    assert result.range_percentile is None


def test_benchmark_does_not_borrow_other_phase_or_current_session():
    current = metric(31, 25)
    history = tuple(metric(day, day) for day in range(1, 20))
    history += (metric(31, 1, ResearchPhase.OVERNIGHT),)
    result = compare_to_history(current, history)
    assert result.sample_count == 19
    assert result.available is False


def test_benchmark_does_not_use_future_sessions():
    current = metric(10, 25)
    history = tuple(metric(day, day) for day in range(1, 10))
    history += tuple(metric(day, day) for day in range(11, 31))
    result = compare_to_history(current, history)
    assert result.sample_count == 9
    assert result.available is False
