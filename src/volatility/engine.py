"""Coordinate completed bars into replay-safe top-level regime snapshots."""

from dataclasses import dataclass
from datetime import date

from src.historical.models import HistoricalBar

from .benchmark import compare_to_history
from .cash import build_opening_range, classify_cash
from .expansion import calculate_rv_changes
from .expansion_state import classify_expansion
from .metrics import calculate_phase_metrics
from .models import CompressionState, ExpansionConfig, ExpansionState, PhaseMetric, PremarketState, ResearchPhase
from .premarket import build_overnight_range, classify_premarket
from .regime import classify_compression
from .state_machine import RegimeState, compose_regime


@dataclass(frozen=True)
class RegimeSnapshot:
    metric: PhaseMetric
    regime: RegimeState
    expansion: ExpansionState
    sample_count: int
    rv_percentile: object
    range_percentile: object
    compression: CompressionState | None
    premarket: PremarketState | None


def build_regime_snapshots(
    bars: tuple[HistoricalBar, ...],
    config: ExpansionConfig = ExpansionConfig(),
) -> tuple[RegimeSnapshot, ...]:
    """Evaluate every completed research-window bar with no future sessions."""
    if any(not bar.is_complete for bar in bars):
        raise ValueError("regime engine accepts completed bars only")
    metrics = calculate_phase_metrics(bars)
    changes = calculate_rv_changes(metrics)
    expansions, benchmarks = _expansions(metrics, changes, config)
    compression = _compression(metrics, benchmarks)
    metric_index = {metric.bar_start_utc: metric for metric in metrics}
    premarket = _premarket_states(bars, metric_index)
    cash = _cash_states(bars, metric_index, expansions)
    snapshots: list[RegimeSnapshot] = []
    for metric in metrics:
        timestamp = metric.bar_start_utc
        regime = _regime(metric, compression.get(timestamp), premarket.get(timestamp), expansions[timestamp], cash.get(timestamp))
        benchmark = benchmarks[timestamp]
        snapshots.append(RegimeSnapshot(
            metric, regime, expansions[timestamp], benchmark.sample_count,
            benchmark.realized_volatility_percentile, benchmark.range_percentile,
            compression.get(timestamp), premarket.get(timestamp),
        ))
    return tuple(snapshots)


def _expansions(
    metrics: tuple[PhaseMetric, ...], changes, config: ExpansionConfig):
    benchmarks = {}
    states = {}
    history_by_key: dict[tuple[ResearchPhase, int], list[PhaseMetric]] = {}
    for index, change in enumerate(changes):
        current = change.metric
        key = (current.phase, current.elapsed_minutes)
        history = tuple(history_by_key.get(key, ()))
        benchmark = compare_to_history(current, history)
        benchmarks[current.bar_start_utc] = benchmark
        states[current.bar_start_utc] = classify_expansion(change, benchmark, config)
        history_by_key.setdefault(key, []).append(current)
    return states, benchmarks


def _compression(metrics: tuple[PhaseMetric, ...], benchmarks):
    states = {}
    counts: dict[date, int] = {}
    previous: dict[date, PhaseMetric] = {}
    for metric in metrics:
        if metric.phase is not ResearchPhase.OVERNIGHT:
            continue
        benchmark = benchmarks[metric.bar_start_utc]
        qualifies = benchmark.available and benchmark.realized_volatility_percentile is not None and benchmark.realized_volatility_percentile <= 20
        prior = previous.get(metric.session_date)
        contiguous = prior is not None and metric.elapsed_minutes - prior.elapsed_minutes == 5
        if not contiguous:
            counts[metric.session_date] = 0
        counts[metric.session_date] = counts.get(metric.session_date, 0) + 1 if qualifies else 0
        states[metric.bar_start_utc] = classify_compression(metric, benchmark, counts[metric.session_date])
        previous[metric.session_date] = metric
    return states


def _premarket_states(bars: tuple[HistoricalBar, ...], metric_index):
    states = {}
    for session in _session_dates(metric_index):
        try:
            levels = build_overnight_range(bars, session)
        except ValueError:
            continue
        values = classify_premarket(bars, levels)
        timestamps = _phase_timestamps(metric_index, session, ResearchPhase.PREMARKET)
        states.update(dict(zip(timestamps, values)))
    return states


def _cash_states(bars: tuple[HistoricalBar, ...], metric_index, expansions):
    states = {}
    for session in _session_dates(metric_index):
        try:
            opening = build_opening_range(bars, session)
        except ValueError:
            continue
        timestamps = _post_opening_timestamps(metric_index, session)
        values = classify_cash(bars, opening, tuple(expansions[timestamp] for timestamp in timestamps))
        states.update(dict(zip(timestamps, values)))
    return states


def _regime(metric, compression, premarket, expansion, cash):
    if metric.phase is ResearchPhase.CASH and metric.elapsed_minutes < 15:
        return RegimeState.CASH_OPEN
    return compose_regime(metric.phase, compression, premarket, expansion, cash)


def _session_dates(metric_index):
    return {metric.session_date for metric in metric_index.values()}


def _phase_timestamps(metric_index, session: date, phase: ResearchPhase):
    return tuple(
        metric.bar_start_utc for metric in sorted(metric_index.values(), key=lambda metric: metric.bar_start_utc)
        if metric.phase is phase and metric.session_date == session
    )


def _post_opening_timestamps(metric_index, session: date):
    return tuple(
        metric.bar_start_utc for metric in sorted(metric_index.values(), key=lambda metric: metric.bar_start_utc)
        if metric.phase is ResearchPhase.CASH
        and metric.session_date == session
        and metric.elapsed_minutes >= 15
    )
