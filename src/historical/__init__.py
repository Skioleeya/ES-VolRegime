"""Historical market-data models and request planning."""

from .models import HistoricalBar, HistoricalRequest, QualifiedContract
from .normalizer import normalize_completed_bar
from .repository import HistoricalRepository
from .request_plan import build_request_plan
from .polling import LatestBarPoller, build_latest_bar_request, completed_boundary, in_research_window, next_poll_at, next_window_start
from .coverage import expected_bar_starts, is_trading_session, missing_bar_starts, next_trading_session, session_window

__all__ = [
    "HistoricalBar",
    "HistoricalRequest",
    "QualifiedContract",
    "HistoricalRepository",
    "build_request_plan",
    "normalize_completed_bar",
    "LatestBarPoller",
    "build_latest_bar_request",
    "completed_boundary",
    "next_poll_at",
    "in_research_window",
    "next_window_start",
    "session_window",
    "expected_bar_starts",
    "missing_bar_starts",
    "is_trading_session",
    "next_trading_session",
]
