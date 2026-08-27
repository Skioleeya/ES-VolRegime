from datetime import date

from src.historical.coverage import is_trading_session, next_trading_session


def test_cme_calendar_excludes_weekend():
    assert not is_trading_session(date(2026, 8, 29))


def test_next_trading_session_skips_weekend():
    assert next_trading_session(date(2026, 8, 29)) == date(2026, 8, 31)
