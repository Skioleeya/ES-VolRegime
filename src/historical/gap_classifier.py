"""Classify observed gaps without assuming every Globex minute must trade."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

import pandas_market_calendars as market_calendars

from .report import FIVE_MINUTES, research_phase

ET = ZoneInfo("America/New_York")


class GapCategory(StrEnum):
    CME_BREAK = "CME_BREAK"
    WEEKEND_OR_HOLIDAY = "WEEKEND_OR_HOLIDAY"
    OUTSIDE_RESEARCH_WINDOW = "OUTSIDE_RESEARCH_WINDOW"
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass(frozen=True)
class ClassifiedGap:
    start_utc: datetime
    end_utc: datetime
    category: GapCategory


def classify_gaps(gaps: tuple[tuple[datetime, datetime], ...]) -> tuple[ClassifiedGap, ...]:
    """Classify gaps using the packaged CME Equity schedule and ET rules."""
    calendar = market_calendars.get_calendar("CME_Equity")
    return tuple(
        ClassifiedGap(start, end, _classify(start, end, calendar))
        for start, end in gaps
    )


def _classify(start: datetime, end: datetime, calendar) -> GapCategory:
    start_et = start.astimezone(ET)
    end_et = end.astimezone(ET)
    if _contains_non_session_day(start_et, end_et, calendar):
        return GapCategory.WEEKEND_OR_HOLIDAY
    if _overlaps_cme_break(start, end, calendar):
        return GapCategory.CME_BREAK
    if research_phase(start_et) is None and research_phase(end_et) is None:
        return GapCategory.OUTSIDE_RESEARCH_WINDOW
    return GapCategory.UNCLASSIFIED


def _overlaps_cme_break(start: datetime, end: datetime, calendar) -> bool:
    dates = {start.astimezone(ET).date(), end.astimezone(ET).date()}
    for session_date in dates:
        schedule = calendar.schedule(session_date, session_date)
        if schedule.empty:
            continue
        row = schedule.iloc[0]
        break_start = row.get("break_start")
        break_end = row.get("break_end")
        if break_start is not None and break_end is not None:
            if _intervals_overlap(start, end, break_start.to_pydatetime(), break_end.to_pydatetime()):
                return True
    return False


def _contains_non_session_day(start: datetime, end: datetime, calendar) -> bool:
    schedule = calendar.schedule(start.date(), end.date())
    session_dates = {value.date() for value in schedule.index}
    cursor = start.date()
    while cursor <= end.date():
        if cursor.weekday() >= 5 or cursor not in session_dates:
            return True
        cursor += timedelta(days=1)
    return False


def _intervals_overlap(start: datetime, end: datetime, other_start: datetime, other_end: datetime) -> bool:
    return max(start, other_start) < min(end, other_end)
