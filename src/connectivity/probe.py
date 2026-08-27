"""Fail-fast IBKR connectivity and ES market-data probe; never places orders."""

from datetime import datetime, timezone
import threading
import time

from ibapi.client import EClient
from ibapi.contract import Contract, ContractDetails
from ibapi.wrapper import EWrapper

from .config import IbkrConfig
from src.config import DEFAULT_SESSION_CONFIG


class IbkrProbe(EWrapper, EClient):
    def __init__(self, config: IbkrConfig):
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        self.config = config
        self.connected_event = threading.Event()
        self.contract_event = threading.Event()
        self.history_event = threading.Event()
        self.realtime_event = threading.Event()
        self.errors: list[str] = []
        self.contracts: list[ContractDetails] = []
        self.history_count = 0
        self.tick_count = 0
        self._next_request_id = 1000

    def nextValidId(self, orderId: int) -> None:
        self.connected_event.set()

    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = "") -> None:
        if errorCode not in {2104, 2106, 2158}:
            self.errors.append(f"{errorCode}: {errorString}")

    def contractDetails(self, reqId: int, contractDetails: ContractDetails) -> None:
        self.contracts.append(contractDetails)

    def contractDetailsEnd(self, reqId: int) -> None:
        self.contract_event.set()

    def historicalData(self, reqId: int, bar) -> None:
        self.history_count += 1

    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        self.history_event.set()

    def tickPrice(self, reqId: int, tickType: int, price: float, attrib) -> None:
        if price > 0:
            self.tick_count += 1
            self.realtime_event.set()

    def _request_id(self) -> int:
        self._next_request_id += 1
        return self._next_request_id

    def run_probe(self) -> dict[str, str | int]:
        self.connect(self.config.host, self.config.port, self.config.client_id)
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        self._require(self.connected_event, "connection", self.config.timeout_seconds)
        contract = self._qualify_es()
        self._request_history(contract)
        self._request_realtime(contract)
        self.disconnect()
        return {
            "IBKR connection": "PASS",
            "ES contract qualification": "PASS",
            "Historical ES 5m data": f"PASS ({self.history_count} bars)",
            "Realtime ES market data": f"PASS ({self.tick_count} ticks)",
            "Order capability used": "NO",
            "Fallback behavior used": "NO",
        }

    def _qualify_es(self) -> Contract:
        request_id = self._request_id()
        contract = Contract()
        contract.symbol = self.config.symbol
        contract.secType = "FUT"
        contract.exchange = self.config.exchange
        contract.currency = self.config.currency
        contract.lastTradeDateOrContractMonth = self.config.last_trade_date
        self.reqContractDetails(request_id, contract)
        self._require(self.contract_event, "ES contract qualification", self.config.timeout_seconds)
        if len(self.contracts) != 1:
            raise RuntimeError(f"Expected exactly one ES contract, received {len(self.contracts)}")
        return self.contracts[0].contract

    def _request_history(self, contract: Contract) -> None:
        self.reqHistoricalData(self._request_id(), contract, "", "2 D", DEFAULT_SESSION_CONFIG.bar_size, "TRADES", 1, 2, False, [])
        self._require(self.history_event, "historical ES 5m data", self.config.timeout_seconds)
        if self.history_count == 0:
            raise RuntimeError("Historical request completed without bars")

    def _request_realtime(self, contract: Contract) -> None:
        request_id = self._request_id()
        self.reqMktData(request_id, contract, "", False, False, [])
        self._require(self.realtime_event, "realtime ES market data", self.config.realtime_seconds)
        self.cancelMktData(request_id)

    def _require(self, event: threading.Event, stage: str, timeout: int) -> None:
        if not event.wait(timeout):
            detail = "; ".join(self.errors[-3:]) or "no callback received"
            raise TimeoutError(f"{stage} failed: {detail}")


def execute(config: IbkrConfig) -> dict[str, str | int]:
    return IbkrProbe(config).run_probe()
