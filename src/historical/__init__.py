"""Historical market-data models and request planning."""

from .models import HistoricalBar, HistoricalRequest, QualifiedContract
from .normalizer import normalize_completed_bar
from .repository import HistoricalRepository
from .request_plan import build_request_plan
from .polling import LatestBarPoller, build_latest_bar_request, completed_boundary, in_research_window, next_poll_at, next_window_start

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
]
