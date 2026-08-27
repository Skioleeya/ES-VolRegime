from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from src.historical.models import HistoricalBar, QualifiedContract
from src.volatility import CashState, ExpansionState, build_opening_range, classify_cash

UTC = timezone.utc
CONTRACT = QualifiedContract(1, "ESU6", "202609")


def bar(iso: str, close: int, high: int, low: int):
    start = datetime.fromisoformat(iso)
    value = Decimal(close)
    return HistoricalBar(CONTRACT, start, start.astimezone(ZoneInfo("America/New_York")), value, Decimal(high), Decimal(low), value, Decimal(1), value, 1)


def test_opening_range_requires_and_uses_three_cash_bars():
    bars = tuple(bar(f"2026-08-27T{hour:02d}:{minute:02d}:00+00:00", 100 + minute, 101 + minute, 99 + minute) for hour, minute in ((13, 30), (13, 35), (13, 40)))
    result = build_opening_range(bars, date(2026, 8, 27))
    assert result.high == Decimal("141")
    assert result.low == Decimal("129")
    assert result.width == Decimal("12")


def test_opening_range_fails_when_a_bar_is_missing():
    bars = (bar("2026-08-27T13:30:00+00:00", 100, 101, 99),)
    with pytest.raises(ValueError, match="expected 3"):
        build_opening_range(bars, date(2026, 8, 27))


def test_cash_requires_breakout_acceptance_and_expansion():
    opening = build_opening_range(tuple(bar(f"2026-08-27T{hour:02d}:{minute:02d}:00+00:00", 100, 101, 99) for hour, minute in ((13, 30), (13, 35), (13, 40))), date(2026, 8, 27))
    bars = (
        bar("2026-08-27T13:45:00+00:00", 102, 103, 101),
        bar("2026-08-27T13:50:00+00:00", 103, 104, 102),
    )
    assert classify_cash(bars, opening, (ExpansionState.EXPANSION, ExpansionState.NORMAL)) == (CashState.BULLISH, CashState.NEUTRAL)


def test_cash_rejects_mismatched_expansion_inputs():
    opening = build_opening_range(tuple(bar(f"2026-08-27T{hour:02d}:{minute:02d}:00+00:00", 100, 101, 99) for hour, minute in ((13, 30), (13, 35), (13, 40))), date(2026, 8, 27))
    with pytest.raises(ValueError, match="one expansion"):
        classify_cash((bar("2026-08-27T13:45:00+00:00", 102, 103, 101),), opening, ())
