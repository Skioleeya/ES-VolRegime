from datetime import date, datetime, timezone

from src.historical.coverage import expected_bar_starts, missing_bar_starts, session_window


def test_session_window_is_18_to_noon_eastern():
    start, end = session_window(date(2026, 8, 27))
    assert start == datetime.fromisoformat("2026-08-26T22:00:00+00:00")
    assert end == datetime.fromisoformat("2026-08-27T16:00:00+00:00")


def test_expected_grid_and_missing_bars():
    expected = expected_bar_starts(date(2026, 8, 27))
    assert len(expected) == 216
    assert missing_bar_starts(date(2026, 8, 27), expected[:-1]) == (expected[-1],)
