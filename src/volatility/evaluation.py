"""Point-in-time evaluation of provisional expansion rules."""

from dataclasses import dataclass

from .benchmark import compare_to_history
from .expansion import calculate_rv_changes
from .expansion_state import classify_expansion
from .models import ExpansionConfig, ExpansionState, PhaseMetric


@dataclass(frozen=True)
class ExpansionEvaluation:
    observations: int
    available_benchmarks: int
    expansion_observations: int
    by_phase: tuple[tuple[str, int, int, int], ...]


def evaluate_expansion(
    metrics: tuple[PhaseMetric, ...],
    config: ExpansionConfig = ExpansionConfig(),
) -> ExpansionEvaluation:
    """Evaluate each observation against historical data available at that date."""
    ordered = tuple(sorted(metrics, key=lambda metric: metric.bar_start_utc))
    changes = calculate_rv_changes(ordered)
    available = 0
    expansions = 0
    phase_counts: dict[str, list[int]] = {}
    for index, change in enumerate(changes):
        history = ordered[:index]
        benchmark = compare_to_history(change.metric, _same_key_history(change.metric, history))
        if benchmark.available:
            available += 1
            phase_counts.setdefault(change.metric.phase.value, [0, 0, 0])[1] += 1
        if classify_expansion(change, benchmark, config) is ExpansionState.EXPANSION:
            expansions += 1
            phase_counts.setdefault(change.metric.phase.value, [0, 0, 0])[2] += 1
        phase_counts.setdefault(change.metric.phase.value, [0, 0, 0])[0] += 1
    breakdown = tuple((phase, *counts) for phase, counts in sorted(phase_counts.items()))
    return ExpansionEvaluation(len(changes), available, expansions, breakdown)


def _same_key_history(current: PhaseMetric, history: tuple[PhaseMetric, ...]) -> tuple[PhaseMetric, ...]:
    return tuple(
        metric for metric in history
        if metric.phase == current.phase and metric.elapsed_minutes == current.elapsed_minutes
    )
