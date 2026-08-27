"""Classify RV expansion using explicit configuration and raw RV changes."""

from .expansion import RVChange
from .models import BenchmarkResult, ExpansionConfig, ExpansionState


def classify_expansion(
    change: RVChange,
    benchmark: BenchmarkResult,
    config: ExpansionConfig = ExpansionConfig(),
) -> ExpansionState:
    """Return expansion only when the configured, observable conditions hold."""
    if config.rv_percentile_threshold < 0 or config.rv_percentile_threshold > 100:
        raise ValueError("rv_percentile_threshold must be between 0 and 100")
    if not benchmark.available or benchmark.realized_volatility_percentile is None:
        return ExpansionState.UNAVAILABLE
    if benchmark.realized_volatility_percentile < config.rv_percentile_threshold:
        return ExpansionState.NORMAL
    if config.require_positive_change and change.change <= 0:
        return ExpansionState.NORMAL
    return ExpansionState.EXPANSION
