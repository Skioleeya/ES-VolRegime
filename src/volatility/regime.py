"""Explicit, threshold-based Overnight compression classification."""

from .models import BenchmarkResult, CompressionState, PhaseMetric, ResearchPhase


def classify_compression(
    metric: PhaseMetric,
    benchmark: BenchmarkResult,
    consecutive_qualifying_bars: int,
    confirmation_bars: int = 2,
) -> CompressionState:
    """Classify compression after the configured consecutive-bar confirmation."""
    if confirmation_bars < 1:
        raise ValueError("confirmation_bars must be positive")
    if metric.phase is not ResearchPhase.OVERNIGHT:
        raise ValueError("compression classification requires an Overnight metric")
    if not benchmark.available:
        return CompressionState.UNAVAILABLE
    if consecutive_qualifying_bars < confirmation_bars:
        return CompressionState.NORMAL
    if benchmark.realized_volatility_percentile is None:
        return CompressionState.UNAVAILABLE
    if benchmark.realized_volatility_percentile > 20:
        return CompressionState.NORMAL
    if benchmark.range_percentile is not None and benchmark.range_percentile <= 30:
        return CompressionState.STRONG_COMPRESSION
    return CompressionState.WEAK_COMPRESSION
