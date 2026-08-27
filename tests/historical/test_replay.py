from datetime import datetime, timezone
from decimal import Decimal

from src.historical import QualifiedContract
from src.historical.models import HistoricalBar
from src.historical.replay import replay_as_of


CONTRACT = QualifiedContract(123, "ESU6", "202609")


def make_bar(hour: int) -> HistoricalBar:
    timestamp = datetime(2026, 8, 25, hour, 0, tzinfo=timezone.utc)
    return HistoricalBar(CONTRACT, timestamp, timestamp, Decimal("1"), Decimal("2"), Decimal("1"), Decimal("2"), Decimal("1"), Decimal("1"), 1)


def test_replay_excludes_unfinished_and_future_bars():
    bars = (make_bar(2), make_bar(1), make_bar(3))

    visible = replay_as_of(bars, datetime(2026, 8, 25, 2, 4, tzinfo=timezone.utc), lambda values: values)

    assert [bar.bar_start_utc.hour for bar in visible] == [1]
