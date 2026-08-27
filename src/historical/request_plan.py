"""Create bounded historical requests using the CME Equity calendar."""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas_market_calendars as market_calendars

from .models import HistoricalRequest, QualifiedContract, ensure_aware, ensure_date_order

ET = ZoneInfo("America/New_York")
UTC = timezone.utc


def build_request_plan(
    contract: QualifiedContract,
    start_date: date,
    end_date: date,
    trading_days_per_request: int = 30,
) -> list[HistoricalRequest]:
    """Build non-overlapping requests for CME Equity session labels.

    The date range is half-open: ``start_date`` is included and ``end_date``
    is excluded. Session labels come from the third-party CME calendar, while
    request boundaries use the project's 20:15 ET to 12:00 ET research span.
    """
    ensure_date_order(start_date, end_date)
    if trading_days_per_request < 1:
        raise ValueError("trading_days_per_request must be positive")

    session_dates = _trading_session_dates(start_date, end_date)
    if not session_dates:
        raise ValueError("requested range contains no CME trading sessions")

    return [
        _make_request(contract, chunk[0], chunk[-1])
        for chunk in _chunks(session_dates, trading_days_per_request)
    ]


def _trading_session_dates(start_date: date, end_date: date) -> list[date]:
    calendar = market_calendars.get_calendar("CME_Equity")
    schedule = calendar.schedule(start_date, end_date - timedelta(days=1))
    return [session_date.date() for session_date in schedule.index]


def _chunks(values: list[date], size: int) -> list[list[date]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def _make_request(contract: QualifiedContract, first: date, last: date) -> HistoricalRequest:
    start_et = datetime.combine(first - timedelta(days=1), time(20, 15), ET)
    end_et = datetime.combine(last, time(12, 0), ET)
    start_utc = start_et.astimezone(UTC)
    end_utc = end_et.astimezone(UTC)
    ensure_aware(start_utc, "start_utc")
    ensure_aware(end_utc, "end_utc")
    if start_utc >= end_utc:
        raise ValueError("request window must be positive")
    duration_days = (end_utc.date() - start_utc.date()).days + 1
    return HistoricalRequest(
        contract=contract,
        start_utc=start_utc,
        end_utc=end_utc,
        start_et=start_et,
        end_et=end_et,
        duration_str=f"{duration_days} D",
    )

