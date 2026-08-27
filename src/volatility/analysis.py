"""Compose a point-in-time volatility analysis without data-source coupling."""

from dataclasses import dataclass

from .benchmark import compare_to_history
from .models import BenchmarkResult, CompressionState, PhaseMetric, ResearchPhase
from .regime import classify_compression


@dataclass(frozen=True)
class VolatilityAnalysis:
    metric: PhaseMetric
    benchmark: BenchmarkResult
    compression: CompressionState


def analyze_latest(
    metrics: tuple[PhaseMetric, ...],
    historical_metrics: tuple[PhaseMetric, ...],
    consecutive_qualifying_bars: int,
) -> VolatilityAnalysis:
    """Analyze the latest metric using only explicitly supplied history."""
    if not metrics:
        raise ValueError("metrics cannot be empty")
    latest = max(metrics, key=lambda metric: metric.bar_start_utc)
    benchmark = compare_to_history(latest, historical_metrics)
    compression = CompressionState.NORMAL
    if latest.phase is ResearchPhase.OVERNIGHT:
        compression = classify_compression(latest, benchmark, consecutive_qualifying_bars)
    return VolatilityAnalysis(latest, benchmark, compression)
