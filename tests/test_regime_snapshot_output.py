from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from src.historical.models import HistoricalBar, QualifiedContract
from src.volatility import build_regime_snapshots

UTC = ZoneInfo("UTC")
ET = ZoneInfo("America/New_York")
CONTRACT = QualifiedContract(1, "ESU6", "202609")


def test_snapshot_preserves_benchmark_explanations():
    start_et = datetime(2026, 8, 27, 9, 30, tzinfo=ET)
    start_utc = start_et.astimezone(UTC)
    bar = HistoricalBar(CONTRACT, start_utc, start_et, Decimal("100"), Decimal("101"), Decimal("99"), Decimal("100"), Decimal("1"), Decimal("100"), 1)
    snapshot = build_regime_snapshots((bar,))[0]
    assert snapshot.sample_count == 0
    assert snapshot.rv_percentile is None
    assert snapshot.range_percentile is None
    assert snapshot.regime.value == "CASH_OPEN"
