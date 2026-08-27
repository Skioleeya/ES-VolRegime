"""Thin TWS API adapter for one historical-data request."""

from dataclasses import dataclass, field
import threading
from typing import Any

from ibapi.client import EClient
from ibapi.contract import Contract, ContractDetails
from ibapi.wrapper import EWrapper

from .models import HistoricalRequest


@dataclass(frozen=True)
class RawHistoricalBar:
    """Raw callback payload; normalization belongs to another module."""

    request_id: int
    date_value: int
    open: Any
    high: Any
    low: Any
    close: Any
    volume: Any
    wap: Any
    bar_count: int


@dataclass
class HistoricalResponse:
    """Thread-safe lifecycle state exposed to the collector."""

    bars: list[RawHistoricalBar] = field(default_factory=list)
    ended: threading.Event = field(default_factory=threading.Event)
    error_event: threading.Event = field(default_factory=threading.Event)
    errors: list[tuple[int, str]] = field(default_factory=list)


class HistoricalClient(EWrapper, EClient):
    """Translate TWS callbacks without applying domain policy."""

    def __init__(self) -> None:
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        self.response = HistoricalResponse()
        self.connected_event = threading.Event()
        self.contract_event = threading.Event()
        self.contracts: list[ContractDetails] = []
        self.server_time: int | None = None
        self.server_time_event = threading.Event()

    def reset_response(self) -> None:
        self.response = HistoricalResponse()

    def nextValidId(self, orderId: int) -> None:
        self.connected_event.set()

    def currentTime(self, time_value: int) -> None:
        self.server_time = int(time_value)
        self.server_time_event.set()

    def request_server_time(self, timeout_seconds: float) -> int:
        self.server_time = None
        self.server_time_event.clear()
        self.reqCurrentTime()
        if not self.server_time_event.wait(timeout_seconds):
            raise TimeoutError("IBKR server time callback did not arrive")
        if self.server_time is None:
            raise RuntimeError("IBKR server time callback returned no value")
        return self.server_time

    def contractDetails(self, reqId: int, contractDetails: ContractDetails) -> None:
        self.contracts.append(contractDetails)

    def contractDetailsEnd(self, reqId: int) -> None:
        self.contract_event.set()

    def historicalData(self, reqId: int, bar: Any) -> None:
        self.response.bars.append(
            RawHistoricalBar(
                request_id=reqId,
                date_value=int(bar.date),
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                wap=bar.average,
                bar_count=int(bar.barCount),
            )
        )

    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        self.response.ended.set()

    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = "") -> None:
        if errorCode not in {2104, 2106, 2158}:
            self.response.errors.append((errorCode, errorString))
            self.response.error_event.set()

    def request(self, request_id: int, request: HistoricalRequest) -> None:
        contract = Contract()
        contract.conId = request.contract.con_id
        contract.symbol = request.contract.symbol
        contract.secType = "FUT"
        contract.exchange = request.contract.exchange
        contract.currency = request.contract.currency
        contract.lastTradeDateOrContractMonth = request.contract.contract_month
        self.reqHistoricalData(
            request_id,
            contract,
            request.end_utc.strftime("%Y%m%d-%H:%M:%S"),
            request.duration_str,
            request.bar_size,
            request.what_to_show,
            request.use_rth,
            request.format_date,
            request.keep_up_to_date,
            [],
        )

    def qualify(self, request: HistoricalRequest, request_id: int, timeout_seconds: float) -> Contract:
        contract = Contract()
        contract.symbol = request.contract.symbol
        contract.secType = "FUT"
        contract.exchange = request.contract.exchange
        contract.currency = request.contract.currency
        contract.lastTradeDateOrContractMonth = request.contract.contract_month
        self.reqContractDetails(request_id, contract)
        if not self.contract_event.wait(timeout_seconds):
            raise TimeoutError("contract details callback did not arrive")
        if len(self.contracts) != 1:
            raise ValueError(f"expected one qualified contract, received {len(self.contracts)}")
        return self.contracts[0].contract

    def futures_chain(self, symbol: str, exchange: str, currency: str, request_id: int, timeout_seconds: float):
        """Return IBKR contract details for matching futures, with no expiry guessed locally."""
        self.contracts = []
        self.contract_event.clear()
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "FUT"
        contract.exchange = exchange
        contract.currency = currency
        self.reqContractDetails(request_id, contract)
        if not self.contract_event.wait(timeout_seconds):
            raise TimeoutError("futures chain contract details callback did not arrive")
        if not self.contracts:
            raise ValueError("IBKR returned no futures contracts")
        return tuple(self.contracts)
