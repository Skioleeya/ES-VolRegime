from dataclasses import dataclass
from datetime import date

import pytest

from src.historical import QualifiedContract, build_request_plan
from src.historical.client import RawHistoricalBar, HistoricalResponse
from src.historical.collector import HistoricalCollector
from src.historical.errors import HistoricalBrokerError, HistoricalEmpty, HistoricalTimeout
from src.historical.pacing import HistoricalPacer


CONTRACT = QualifiedContract(con_id=123, local_symbol="ESU6", contract_month="202609")
REQUEST = build_request_plan(CONTRACT, date(2026, 8, 24), date(2026, 8, 25))[0]


@dataclass
class FakeClient:
    response: HistoricalResponse
    complete: bool = True
    emit_bar: bool = True
    error: tuple[int, str] | None = None

    def reset_response(self) -> None:
        self.response = HistoricalResponse()
        if self.error is not None:
            self.response.errors.append(self.error)
            self.response.error_event.set()

    def request(self, request_id: int, request) -> None:
        if self.complete:
            if self.emit_bar:
                self.response.bars.append(
                    RawHistoricalBar(request_id, 1787515200, 6000, 6001, 5999, 6000, 12, 6000, 3)
                )
            self.response.ended.set()


def test_collector_returns_callbacks_after_historical_end():
    client = FakeClient(HistoricalResponse())
    result = HistoricalCollector(client, HistoricalPacer()).collect(REQUEST)

    assert len(result.bars) == 1
    assert result.bars[0].request_id == 10001


def test_collector_fails_on_timeout():
    client = FakeClient(HistoricalResponse(), complete=False)

    with pytest.raises(HistoricalTimeout):
        HistoricalCollector(client, HistoricalPacer()).collect(REQUEST, timeout_seconds=0.001)


def test_collector_fails_on_empty_response():
    client = FakeClient(HistoricalResponse(), emit_bar=False)

    with pytest.raises(HistoricalEmpty):
        HistoricalCollector(client, HistoricalPacer()).collect(REQUEST)


def test_collector_fails_on_ibkr_error():
    client = FakeClient(HistoricalResponse(), error=(162, "historical data request pacing violation"))

    with pytest.raises(HistoricalBrokerError, match="162"):
        HistoricalCollector(client, HistoricalPacer()).collect(REQUEST)
