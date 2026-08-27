from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.historical import QualifiedContract
from src.historical.client import RawHistoricalBar
from src.historical.errors import HistoricalError
from src.historical.normalizer import normalize_completed_bar


CONTRACT = QualifiedContract(con_id=123, local_symbol="ESU6", contract_month="202609")
AS_OF = datetime(2026, 8, 24, 21, 5, tzinfo=timezone.utc)


def raw_bar(timestamp: int = 1787515200, **changes) -> RawHistoricalBar:
    values = dict(request_id=1, date_value=timestamp, open=6000, high=6001, low=5999, close=6000, volume=12, wap=6000, bar_count=3)
    values.update(changes)
    return RawHistoricalBar(**values)


def test_normalizer_creates_utc_and_et_timestamps():
    bar = normalize_completed_bar(raw_bar(), CONTRACT, AS_OF)

    assert bar.bar_start_utc.tzinfo == timezone.utc
    assert bar.bar_start_et.tzname() == "EDT"
    assert bar.open == Decimal("6000")
    assert bar.is_complete is True


@pytest.mark.parametrize("changes", [{"open": 0}, {"low": 6002}, {"volume": -1}, {"bar_count": -1}])
def test_normalizer_rejects_invalid_values(changes):
    with pytest.raises(HistoricalError):
        normalize_completed_bar(raw_bar(**changes), CONTRACT, AS_OF)


def test_normalizer_rejects_unaligned_or_incomplete_bar():
    with pytest.raises(HistoricalError, match="aligned"):
        normalize_completed_bar(raw_bar(timestamp=1787515210), CONTRACT, AS_OF)

    with pytest.raises(HistoricalError, match="complete"):
        normalize_completed_bar(raw_bar(timestamp=AS_OF.timestamp()), CONTRACT, AS_OF)

