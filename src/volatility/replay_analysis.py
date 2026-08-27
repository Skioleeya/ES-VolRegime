"""Build unified point-in-time observations for historical replay."""

from dataclasses import dataclass

from .benchmark import compare_to_history
from .expansion import calculate_rv_changes
from .expansion_state import classify_expansion
from .models import BenchmarkResult, ExpansionConfig, ExpansionState, PhaseMetric, ResearchPhase
from .state_machine import RegimeState, compose_regime


@dataclass(frozen=True)
class ReplayObservation:
    metric: PhaseMetric
    benchmark: BenchmarkResult
    expansion: ExpansionState
    regime: RegimeState


def build_replay_observations(
    metrics: tuple[PhaseMetric, ...],
    config: ExpansionConfig = ExpansionConfig(),
) -> tuple[ReplayObservation, ...]:
    """Create ordered observations using only metrics from earlier sessions."""
    ordered = tuple(sorted(metrics, key=lambda metric: metric.bar_start_utc))
    changes = calculate_rv_changes(ordered)
    observations: list[ReplayObservation] = []
    for index, change in enumerate(changes):
        current = change.metric
        history = tuple(
            item for item in ordered[:index]
            if item.phase == current.phase
            and item.elapsed_minutes == current.elapsed_minutes
        )
        benchmark = compare_to_history(current, history)
        expansion = classify_expansion(change, benchmark, config)
        regime = compose_regime(current.phase, expansion=expansion)
        observations.append(ReplayObservation(current, benchmark, expansion, regime))
    return tuple(observations)
