from datetime import date, datetime, timezone
from decimal import Decimal

from src.volatility import ExpansionConfig, PhaseMetric, ResearchPhase
from src.volatility.evaluation import evaluate_expansion

UTC = timezone.utc


def metric(day: int, value: int):
    return PhaseMetric(ResearchPhase.PREMARKET, date(2026, 1, day), 60, datetime(2026, 1, day, tzinfo=UTC), Decimal(value), Decimal(value), Decimal(value), Decimal(value))


def test_evaluation_is_point_in_time_and_needs_prior_history():
    result = evaluate_expansion(tuple(metric(day, day) for day in range(1, 31)), ExpansionConfig(Decimal("0")))
    assert result.observations == 30
    assert result.available_benchmarks == 10
    assert result.expansion_observations == 0
    assert result.by_phase == (("PREMARKET", 30, 10, 0),)
