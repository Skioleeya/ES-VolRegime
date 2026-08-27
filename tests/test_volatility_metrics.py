from datetime import datetime, timezone
from decimal import Decimal

from src.historical.models import HistoricalBar, QualifiedContract
from src.volatility import ResearchPhase, calculate_phase_metrics

UTC = timezone.utc
CONTRACT = QualifiedContract(1, "ESU6", "202609")


def bar(iso: str, close: int, high: int | None = None, low: int | None = None):
    value = Decimal(close)
    return HistoricalBar(CONTRACT, datetime.fromisoformat(iso), datetime.fromisoformat(iso).astimezone(UTC), value, Decimal(high or close), Decimal(low or close), value, Decimal(1), value, 1)


def test_metrics_reset_between_overnight_and_cash():
    bars = (
        bar("2026-08-27T03:30:00+00:00", 100),
        bar("2026-08-27T03:35:00+00:00", 110, 112, 99),
        bar("2026-08-27T13:30:00+00:00", 120),
        bar("2026-08-27T13:35:00+00:00", 121),
    )
    metrics = calculate_phase_metrics(bars)
    assert [metric.phase for metric in metrics] == [ResearchPhase.OVERNIGHT] * 2 + [ResearchPhase.CASH] * 2
    assert metrics[0].realized_variance == Decimal("0")
    assert metrics[2].realized_variance == Decimal("0")
    assert metrics[1].range_value == Decimal("13")
    assert metrics[1].elapsed_minutes == 200


def test_metrics_exclude_bar_after_cash_research_window():
    assert calculate_phase_metrics((bar("2026-08-27T16:05:00+00:00", 100),)) == ()
