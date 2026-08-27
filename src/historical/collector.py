"""Single-request historical collection lifecycle."""

from dataclasses import dataclass
import time

from .client import HistoricalClient, RawHistoricalBar
from .errors import HistoricalBrokerError, HistoricalEmpty, HistoricalTimeout
from .models import HistoricalRequest
from .pacing import HistoricalPacer


@dataclass(frozen=True)
class CollectedHistory:
    request: HistoricalRequest
    bars: tuple[RawHistoricalBar, ...]

    @property
    def duplicate_timestamps(self) -> int:
        return len(self.bars) - len({bar.date_value for bar in self.bars})


class HistoricalCollector:
    """Submit exactly one request and require an explicit terminal callback."""

    def __init__(self, client: HistoricalClient, pacer: HistoricalPacer | None = None) -> None:
        self.client = client
        self.pacer = pacer or HistoricalPacer()
        self._request_id = 10_000

    def collect(self, request: HistoricalRequest, timeout_seconds: float = 30.0) -> CollectedHistory:
        signature = (
            request.contract.local_symbol,
            request.contract.exchange,
            request.what_to_show,
        )
        self.pacer.acquire(signature)
        request_id = self._next_request_id()
        self.client.reset_response()
        self.client.request(request_id, request)
        if self.client.response.errors:
            code, message = self.client.response.errors[-1]
            raise HistoricalBrokerError(f"IBKR {code}: {message}")
        deadline = time.monotonic() + timeout_seconds
        while True:
            if self.client.response.errors:
                code, message = self.client.response.errors[-1]
                raise HistoricalBrokerError(f"IBKR {code}: {message}")
            if self.client.response.ended.is_set():
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise HistoricalTimeout(f"historical request {request_id} did not end")
            self.client.response.ended.wait(min(0.1, remaining))
        if not self.client.response.bars:
            raise HistoricalEmpty(f"historical request {request_id} returned no bars")
        return CollectedHistory(request, tuple(self.client.response.bars))

    def _next_request_id(self) -> int:
        self._request_id += 1
        return self._request_id
