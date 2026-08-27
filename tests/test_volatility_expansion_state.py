from datetime import date, datetime, timezone
from decimal import Decimal

from src.volatility import BenchmarkResult, ExpansionConfig, ExpansionState, PhaseMetric, RVChange, ResearchPhase, classify_expansion

UTC = timezone.utc


def change(amount: str):
    metric = PhaseMetric(ResearchPhase.PREMARKET, date(2026, 8, 27), 60, datetime(2026, 8, 27, tzinfo=UTC), Decimal("0"), Decimal("1"), Decimal("1"), Decimal("1"))
    return RVChange(metric, Decimal(amount), Decimal("1"), Decimal(amount), None)


def benchmark(percentile: str | None, samples=20):
    return BenchmarkResult(ResearchPhase.PREMARKET, 60, Decimal(percentile) if percentile else None, Decimal("50") if percentile else None, samples)


def test_expansion_uses_explicit_percentile_and_change_thresholds():
    assert classify_expansion(change("0.1"), benchmark("80")) is ExpansionState.EXPANSION
    assert classify_expansion(change("0"), benchmark("90")) is ExpansionState.NORMAL
    assert classify_expansion(change("0.1"), benchmark("79.99")) is ExpansionState.NORMAL


def test_expansion_is_unavailable_without_history():
    assert classify_expansion(change("0.1"), benchmark(None, 19)) is ExpansionState.UNAVAILABLE


def test_expansion_threshold_is_validated():
    try:
        classify_expansion(change("0.1"), benchmark("90"), ExpansionConfig(Decimal("101")))
    except ValueError as exc:
        assert "between 0 and 100" in str(exc)
    else:
        raise AssertionError("expected invalid expansion threshold to fail")
