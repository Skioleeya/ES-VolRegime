from datetime import date, datetime, timezone
from decimal import Decimal
from dataclasses import replace

import pytest

from src.volatility import BenchmarkResult, CompressionState, PhaseMetric, ResearchPhase, classify_compression

UTC = timezone.utc


def metric():
    return PhaseMetric(ResearchPhase.OVERNIGHT, date(2026, 8, 27), 120, datetime(2026, 8, 27, tzinfo=UTC), Decimal("0.01"), Decimal("0.01"), Decimal("0.1"), Decimal("1"))


def benchmark(rv: str | None, range_value: str | None, samples=20):
    return BenchmarkResult(ResearchPhase.OVERNIGHT, 120, Decimal(rv) if rv else None, Decimal(range_value) if range_value else None, samples)


def test_compression_requires_two_confirming_bars():
    assert classify_compression(metric(), benchmark("10", "20"), 1) is CompressionState.NORMAL
    assert classify_compression(metric(), benchmark("10", "20"), 2) is CompressionState.STRONG_COMPRESSION


def test_compression_distinguishes_weak_and_normal():
    assert classify_compression(metric(), benchmark("10", "40"), 2) is CompressionState.WEAK_COMPRESSION
    assert classify_compression(metric(), benchmark("21", "20"), 2) is CompressionState.NORMAL


def test_compression_is_unavailable_without_history():
    assert classify_compression(metric(), benchmark(None, None, 19), 2) is CompressionState.UNAVAILABLE


def test_compression_rejects_other_phases_and_invalid_confirmation():
    with pytest.raises(ValueError, match="Overnight"):
        classify_compression(replace(metric(), phase=ResearchPhase.CASH), benchmark("10", "20"), 2)
    with pytest.raises(ValueError, match="positive"):
        classify_compression(metric(), benchmark("10", "20"), 2, 0)
