"""Expected session grids and persisted coverage checks."""

from datetime import date, datetime, timedelta, timezone

from src.config import DEFAULT_SESSION_CONFIG, SessionConfig


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
