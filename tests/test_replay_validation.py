from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from src.historical.models import HistoricalBar, QualifiedContract
from src.volatility import validate_prefix_invariance

UTC = timezone.utc
CONTRACT = QualifiedContract(1, "ESU6", "202609")


def test_replay_prefix_is_invariant_to_future_bar():
    bars = tuple(
        HistoricalBar(CONTRACT, datetime(2026, 8, 27, 13, minute, tzinfo=UTC), datetime(2026, 8, 27, 9, minute, tzinfo=ZoneInfo("America/New_York")), Decimal(100 + minute), Decimal(101 + minute), Decimal(99 + minute), Decimal(100 + minute), Decimal(1), Decimal(100 + minute), 1)
        for minute in (30, 35, 40, 45)
    )
    assert validate_prefix_invariance(bars, datetime(2026, 8, 27, 13, 50, tzinfo=UTC)) == 4
