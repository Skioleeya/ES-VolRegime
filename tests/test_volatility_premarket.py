from datetime import date, datetime, timezone
from decimal import Decimal

from src.historical.models import HistoricalBar, QualifiedContract
from src.volatility import PremarketState, build_overnight_range, classify_premarket

UTC = timezone.utc
CONTRACT = QualifiedContract(1, "ESU6", "202609")


def bar(iso: str, close: int, high: int, low: int):
    start = datetime.fromisoformat(iso)
    value = Decimal(close)
    return HistoricalBar(CONTRACT, start, start.astimezone(UTC), value, Decimal(high), Decimal(low), value, Decimal(1), value, 1)


def test_premarket_uses_frozen_overnight_range_and_acceptance():
    overnight = (
        bar("2026-08-27T02:15:00+00:00", 100, 105, 98),
        bar("2026-08-27T03:15:00+00:00", 103, 106, 99),
    )
    premarket = (
        bar("2026-08-27T08:00:00+00:00", 107, 108, 106),
        bar("2026-08-27T08:05:00+00:00", 108, 109, 107),
    )
    levels = build_overnight_range(overnight, date(2026, 8, 27))
    assert levels.high == Decimal("106")
    assert levels.low == Decimal("98")
    assert classify_premarket(premarket, levels) == (
        PremarketState.BULLISH_ACCEPTED,
        PremarketState.BULLISH_ACCEPTED,
    )


def test_premarket_detects_failed_breakout():
    levels = build_overnight_range((bar("2026-08-27T02:15:00+00:00", 100, 105, 98),), date(2026, 8, 27))
    bars = (
        bar("2026-08-27T08:00:00+00:00", 106, 107, 105),
        bar("2026-08-27T08:05:00+00:00", 100, 101, 99),
    )
    assert classify_premarket(bars, levels) == (PremarketState.BULLISH_ACCEPTED, PremarketState.FAILED_BREAKOUT)


def test_premarket_requires_overnight_data():
    try:
        build_overnight_range((), date(2026, 8, 27))
    except ValueError as exc:
        assert "no Overnight" in str(exc)
    else:
        raise AssertionError("expected missing Overnight data to fail")
