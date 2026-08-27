from datetime import date, datetime, timezone
from decimal import Decimal

from src.volatility import ExpansionConfig, ExpansionState, PhaseMetric, ResearchPhase, RegimeState, build_replay_observations

UTC = timezone.utc


def metric(day: int, value: int):
    return PhaseMetric(ResearchPhase.PREMARKET, date(2026, 1, day), 60, datetime(2026, 1, day, tzinfo=UTC), Decimal(value), Decimal(value), Decimal(value), Decimal(value))


def test_replay_observations_are_ordered_and_as_of():
    result = build_replay_observations(tuple(metric(day, day) for day in range(1, 31)), ExpansionConfig(require_positive_change=False))
    assert len(result) == 30
    assert result[0].benchmark.sample_count == 0
    assert result[19].benchmark.sample_count == 19
    assert result[20].benchmark.sample_count == 20
    assert result[20].expansion is ExpansionState.EXPANSION
    assert result[20].regime is RegimeState.PREMARKET_EXPANSION_WATCH
