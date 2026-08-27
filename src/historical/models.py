"""Immutable domain records for historical ES market data."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from src.config import DEFAULT_SESSION_CONFIG


@dataclass(frozen=True)
class QualifiedContract:
    """The fully qualified expiring contract used as the data identity."""

    con_id: int
    local_symbol: str
    contract_month: str
    symbol: str = "ES"
    exchange: str = "CME"
    currency: str = "USD"
    time_zone: str = "America/New_York"


@dataclass(frozen=True)
class HistoricalRequest:
    """One bounded request window expressed in UTC and ET."""

    contract: QualifiedContract
    start_utc: datetime
    end_utc: datetime
    start_et: datetime
    end_et: datetime
    duration_str: str
    bar_size: str = DEFAULT_SESSION_CONFIG.bar_size
    what_to_show: str = "TRADES"
    use_rth: int = 0
    format_date: int = 2
    keep_up_to_date: bool = False


@dataclass(frozen=True)
class HistoricalBar:
    """A normalized completed bar returned by the historical adapter."""

    contract: QualifiedContract
    bar_start_utc: datetime
    bar_start_et: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    wap: Decimal
    bar_count: int
    source: str = "IBKR_HISTORICAL"
    is_complete: bool = True


def ensure_date_order(start: date, end: date) -> None:
    if start >= end:
        raise ValueError("start date must be before end date")


def ensure_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
