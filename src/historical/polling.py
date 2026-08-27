"""Server-time-aligned polling for one completed ES 5-minute bar."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import time

from .client import HistoricalClient
from .collector import HistoricalCollector
from .errors import HistoricalError
from .models import HistoricalBar, HistoricalRequest, QualifiedContract
from .normalizer import normalize_completed_bar
from src.config import DEFAULT_SESSION_CONFIG, SessionConfig
from .coverage import is_trading_session, next_trading_session

UTC = timezone.utc
BAR_LENGTH = timedelta(minutes=DEFAULT_SESSION_CONFIG.bar_minutes)
POLL_DELAY = timedelta(seconds=7)


def in_research_window(server_now: datetime, config: SessionConfig = DEFAULT_SESSION_CONFIG) -> bool:
    """Return whether an instant is inside the configured 18:00-12:00 window."""
    _ensure_utc(server_now)
    local = server_now.astimezone(config.timezone)
    clock = local.timetz().replace(tzinfo=None)
    return clock >= config.session_start or clock < config.session_end


def active_session_date(server_now: datetime, config: SessionConfig = DEFAULT_SESSION_CONFIG):
    """Return the CME session label when the instant is collectable, else None."""
    if not in_research_window(server_now, config):
        return None
    local = server_now.astimezone(config.timezone)
    clock = local.timetz().replace(tzinfo=None)
    session_date = local.date() + timedelta(days=1) if clock >= config.session_start else local.date()
    return session_date if is_trading_session(session_date) else None


def next_window_start(server_now: datetime, config: SessionConfig = DEFAULT_SESSION_CONFIG) -> datetime:
    """Return the next configured evening session start in UTC."""
    _ensure_utc(server_now)
    local = server_now.astimezone(config.timezone)
    clock = local.timetz().replace(tzinfo=None)
    session_date = local.date() if clock < config.session_end else local.date() + timedelta(days=1)
    session_date = next_trading_session(session_date)
    target = datetime.combine(session_date - timedelta(days=1), config.session_start, config.timezone)
    if target.astimezone(UTC) <= server_now:
        session_date = next_trading_session(session_date + timedelta(days=1))
        target = datetime.combine(session_date - timedelta(days=1), config.session_start, config.timezone)
    return target.astimezone(UTC)


def completed_boundary(server_now: datetime, config: SessionConfig = DEFAULT_SESSION_CONFIG) -> datetime:
    """Return the latest 5-minute boundary at or before server_now."""
    _ensure_utc(server_now)
    timestamp = int(server_now.timestamp())
    return datetime.fromtimestamp(timestamp - timestamp % config.bar_seconds, UTC)


def next_poll_at(server_now: datetime, delay: timedelta = POLL_DELAY, config: SessionConfig = DEFAULT_SESSION_CONFIG) -> datetime:
    """Return the next boundary plus the configured finalization delay."""
    if delay < timedelta(seconds=5) or delay > timedelta(seconds=10):
        raise ValueError("poll delay must be between 5 and 10 seconds")
    return completed_boundary(server_now, config) + timedelta(minutes=config.bar_minutes) + delay


def build_latest_bar_request(contract: QualifiedContract, server_now: datetime, config: SessionConfig = DEFAULT_SESSION_CONFIG) -> HistoricalRequest:
    """Build a 300-second request ending at the latest completed boundary."""
    boundary = completed_boundary(server_now, config)
    target_start = boundary - timedelta(minutes=config.bar_minutes)
    return HistoricalRequest(
        contract=contract,
        start_utc=target_start,
        end_utc=boundary,
        start_et=target_start.astimezone(contract_zone(contract)),
        end_et=boundary.astimezone(contract_zone(contract)),
        duration_str=f"{config.bar_seconds} S",
    )


@dataclass
class LatestBarPoller:
    """Calibrate once, then collect exactly the completed target bar."""

    client: HistoricalClient
    collector: HistoricalCollector
    contract: QualifiedContract
    timeout_seconds: float = 30.0
    session_config: SessionConfig = DEFAULT_SESSION_CONFIG

    def poll_once(self) -> HistoricalBar:
        epoch = self.client.request_server_time(self.timeout_seconds)
        server_now = datetime.fromtimestamp(epoch, UTC)
        request = build_latest_bar_request(self.contract, server_now, self.session_config)
        collected = self.collector.collect(request, self.timeout_seconds)
        normalized = tuple(
            normalize_completed_bar(raw, self.contract, server_now, self.session_config)
            for raw in collected.bars
        )
        target = tuple(bar for bar in normalized if bar.bar_start_utc == request.start_utc)
        if len(target) != 1:
            raise HistoricalError("IBKR did not return exactly one target completed bar")
        return target[0]

    def wait_for_next_poll(self, sleep: callable = time.sleep, config: SessionConfig | None = None) -> datetime:
        """Wait using a fresh server-time calibration and return the poll time."""
        config = config or self.session_config
        epoch = self.client.request_server_time(self.timeout_seconds)
        server_now = datetime.fromtimestamp(epoch, UTC)
        if active_session_date(server_now, config) is None:
            poll_at = next_window_start(server_now, config) + POLL_DELAY
        else:
            poll_at = next_poll_at(server_now, config=config)
        sleep(max(0.0, (poll_at - server_now).total_seconds()))
        return poll_at


def contract_zone(contract: QualifiedContract):
    from zoneinfo import ZoneInfo

    return ZoneInfo(contract.time_zone)


def _ensure_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("server_now must be timezone-aware UTC")
