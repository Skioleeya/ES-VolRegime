"""Expected session grids and persisted coverage checks."""

from datetime import date, datetime, timedelta, timezone

from src.config import DEFAULT_SESSION_CONFIG, SessionConfig
import pandas_market_calendars as market_calendars


def session_window(session_date: date, config: SessionConfig = DEFAULT_SESSION_CONFIG) -> tuple[datetime, datetime]:
    """Return the UTC half-open window for one labelled session date."""
    start = datetime.combine(session_date - timedelta(days=1), config.session_start, config.timezone)
    end = datetime.combine(session_date, config.session_end, config.timezone)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def expected_bar_starts(session_date: date, config: SessionConfig = DEFAULT_SESSION_CONFIG) -> tuple[datetime, ...]:
    start, end = session_window(session_date, config)
    step = timedelta(minutes=config.bar_minutes)
    return tuple(start + step * index for index in range(int((end - start) / step)))


def missing_bar_starts(session_date: date, actual: tuple[datetime, ...], config: SessionConfig = DEFAULT_SESSION_CONFIG) -> tuple[datetime, ...]:
    expected = set(expected_bar_starts(session_date, config))
    return tuple(value for value in sorted(expected - set(actual)))


def is_trading_session(session_date: date) -> bool:
    """Return whether CME Equity lists the labelled session date."""
    calendar = market_calendars.get_calendar("CME_Equity")
    schedule = calendar.schedule(session_date, session_date)
    return not schedule.empty


def next_trading_session(session_date: date) -> date:
    """Return the first CME session on or after the supplied date."""
    calendar = market_calendars.get_calendar("CME_Equity")
    end = session_date + timedelta(days=14)
    schedule = calendar.schedule(session_date, end)
    if schedule.empty:
        raise ValueError("no CME Equity session found in two-week search window")
    return schedule.index[0].date()
