from datetime import datetime, timezone

from src.historical.polling import active_session_date, in_research_window, next_window_start


UTC = timezone.utc


def test_window_uses_eastern_session_boundaries():
    assert in_research_window(datetime.fromisoformat("2026-08-28T02:00:00+00:00"))
    assert in_research_window(datetime.fromisoformat("2026-08-27T15:00:00+00:00"))
    assert not in_research_window(datetime.fromisoformat("2026-08-27T17:00:00+00:00"))


def test_next_window_start_is_timezone_aware():
    result = next_window_start(datetime.fromisoformat("2026-08-27T17:00:00+00:00"))
    assert result == datetime.fromisoformat("2026-08-27T22:00:00+00:00")
    assert result.tzinfo is UTC


def test_active_session_excludes_weekend_evening():
    assert active_session_date(datetime.fromisoformat("2026-08-29T22:30:00+00:00")) is None


def test_next_window_start_skips_to_sunday_before_monday_session():
    result = next_window_start(datetime.fromisoformat("2026-08-28T17:00:00+00:00"))
    assert result == datetime.fromisoformat("2026-08-30T22:00:00+00:00")
