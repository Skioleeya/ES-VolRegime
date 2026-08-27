from datetime import date, datetime, timezone
from decimal import Decimal

from src.volatility import PhaseMetric, ResearchPhase, calculate_rv_changes

UTC = timezone.utc


def metric(day: int, minute: int, rv: str, phase=ResearchPhase.PREMARKET):
    return PhaseMetric(phase, date(2026, 8, day), minute, datetime(2026, 8, day, tzinfo=UTC), Decimal("0"), Decimal(rv), Decimal(rv), Decimal("1"))


def test_rv_changes_are_calculated_within_one_phase_sequence():
    result = calculate_rv_changes((metric(27, 0, "1"), metric(27, 5, "1.2"), metric(27, 10, "1.5")))
    assert [item.change for item in result] == [Decimal("0"), Decimal("0.2"), Decimal("0.3")]
    assert result[1].percentage_change == Decimal("20.00")
    assert result[2].acceleration == Decimal("0.1")


def test_rv_changes_reset_on_phase_or_session_boundary():
    result = calculate_rv_changes((metric(27, 0, "1"), metric(28, 0, "2"), metric(28, 0, "3", ResearchPhase.CASH)))
    assert result[1].change == Decimal("0")
    assert result[1].percentage_change is None
    assert result[2].change == Decimal("0")
