from datetime import date, datetime, timezone
from decimal import Decimal

from src.volatility import CompressionState, PhaseMetric, ResearchPhase, analyze_latest

UTC = timezone.utc


def metric(day: int, value: int):
    return PhaseMetric(ResearchPhase.OVERNIGHT, date(2026, 1, day), 120, datetime(2026, 1, day, tzinfo=UTC), Decimal(value), Decimal(value), Decimal(value), Decimal(value))


def test_analysis_uses_latest_metric_and_explicit_history():
    current = metric(31, 25)
    history = tuple(metric(day, day) for day in range(1, 21))
    result = analyze_latest((current,), history, 2)
    assert result.metric is current
    assert result.benchmark.sample_count == 20
    assert result.compression is CompressionState.NORMAL


def test_analysis_fails_without_current_metrics():
    try:
        analyze_latest((), (), 0)
    except ValueError as exc:
        assert "cannot be empty" in str(exc)
    else:
        raise AssertionError("expected empty metrics to fail")
