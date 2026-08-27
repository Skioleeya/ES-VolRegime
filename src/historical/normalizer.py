"""Validate and normalize raw IBKR historical bars."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import math
from zoneinfo import ZoneInfo

from .client import RawHistoricalBar
from .errors import HistoricalError
from .models import HistoricalBar, QualifiedContract

ET = ZoneInfo("America/New_York")
UTC = timezone.utc


def normalize_completed_bar(
    raw: RawHistoricalBar,
    contract: QualifiedContract,
    as_of_utc: datetime,
) -> HistoricalBar:
    """Convert one epoch callback into a validated completed bar."""
    _ensure_utc(as_of_utc, "as_of_utc")
    if raw.request_id <= 0:
        raise HistoricalError("raw bar request id must be positive")
    bar_start_utc = datetime.fromtimestamp(raw.date_value, UTC)
    bar_end_utc = bar_start_utc.timestamp() + 300
    if bar_start_utc.timestamp() % 300 != 0:
        raise HistoricalError("bar timestamp is not aligned to a 5-minute boundary")
    if bar_end_utc > as_of_utc.timestamp():
        raise HistoricalError("bar is not complete at the request as-of time")

    values = [_decimal(value, name) for name, value in _price_values(raw)]
    open_price, high, low, close = values
    volume = _decimal(raw.volume, "volume")
    wap = _decimal(raw.wap, "wap")
    if any(value <= 0 for value in values):
        raise HistoricalError("OHLC prices must be positive")
    if low > open_price or low > close or high < open_price or high < close:
        raise HistoricalError("OHLC relationship is invalid")
    if volume < 0 or raw.bar_count < 0:
        raise HistoricalError("volume and bar count cannot be negative")

    return HistoricalBar(
        contract=contract,
        bar_start_utc=bar_start_utc,
        bar_start_et=bar_start_utc.astimezone(ET),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
        wap=wap,
        bar_count=raw.bar_count,
    )


def _price_values(raw: RawHistoricalBar):
    return (("open", raw.open), ("high", raw.high), ("low", raw.low), ("close", raw.close))


def _decimal(value: object, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise HistoricalError(f"{field_name} is not numeric") from exc
    if not result.is_finite() or not math.isfinite(float(result)):
        raise HistoricalError(f"{field_name} is not finite")
    return result


def _ensure_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise HistoricalError(f"{field_name} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise HistoricalError(f"{field_name} must be UTC")
