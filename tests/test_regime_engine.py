from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from src.historical.models import HistoricalBar, QualifiedContract
from src.volatility import RegimeState, build_regime_snapshots

ET = ZoneInfo("America/New_York")
CONTRACT = QualifiedContract(1, "ESU6", "202609")


def bar(clock: str):
    start_et = datetime.fromisoformat(f"2026-08-27T{clock}:00-04:00")
    start = start_et.astimezone(ZoneInfo("UTC"))
    return HistoricalBar(CONTRACT, start, start_et, Decimal("100"), Decimal("101"), Decimal("99"), Decimal("100"), Decimal("1"), Decimal("100"), 1)


def test_engine_marks_opening_range_bars_as_cash_open():
    snapshots = build_regime_snapshots((bar("09:30"), bar("09:35"), bar("09:40")))
    assert [snapshot.regime for snapshot in snapshots] == [RegimeState.CASH_OPEN] * 3


def test_engine_rejects_incomplete_bar():
    incomplete = bar("09:30").__class__(**{**bar("09:30").__dict__, "is_complete": False})
    try:
        build_regime_snapshots((incomplete,))
    except ValueError as exc:
        assert "completed bars only" in str(exc)
    else:
        raise AssertionError("expected incomplete bar to fail")
