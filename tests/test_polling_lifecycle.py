from dataclasses import dataclass
from datetime import datetime, timezone

from src.historical.client import RawHistoricalBar
from src.historical.collector import CollectedHistory
from src.historical.models import QualifiedContract
from src.historical.polling import LatestBarPoller

UTC = timezone.utc
CONTRACT = QualifiedContract(1, "ESU6", "202609")


@dataclass
class FakeClient:
    epoch: int

    def request_server_time(self, timeout_seconds: float) -> int:
        return self.epoch


class FakeCollector:
    def __init__(self, bars):
        self.bars = bars

    def collect(self, request, timeout_seconds):
        return CollectedHistory(request, tuple(self.bars))


def test_poller_calibrates_server_time_and_selects_previous_completed_bar():
    server_now = datetime(2026, 8, 27, 13, 10, 7, tzinfo=UTC)
    raw = RawHistoricalBar(1, int(datetime(2026, 8, 27, 13, 5, tzinfo=UTC).timestamp()), 100, 101, 99, 100, 1, 100, 1)
    result = LatestBarPoller(FakeClient(int(server_now.timestamp())), FakeCollector((raw,)), CONTRACT).poll_once()
    assert result.bar_start_utc == datetime(2026, 8, 27, 13, 5, tzinfo=UTC)
    assert result.is_complete is True
