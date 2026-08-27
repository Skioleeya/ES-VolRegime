"""Pre-market range transitions and breakout acceptance."""

from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal

from src.historical.models import HistoricalBar

from .models import PremarketState, ResearchPhase


@dataclass(frozen=True)
class OvernightRange:
    session_date: date
    high: Decimal
    low: Decimal

    @property
    def width(self) -> Decimal:
        return self.high - self.low


def build_overnight_range(
    bars: tuple[HistoricalBar, ...], session_date: date
) -> OvernightRange:
    """Freeze the Overnight high and low for one research session."""
    selected = tuple(
        bar for bar in bars
        if bar.bar_start_et.date() == session_date
        and bar.bar_start_et.timetz().replace(tzinfo=None) < time(4)
    )
    if not selected:
        raise ValueError(f"no Overnight bars for session {session_date}")
    return OvernightRange(session_date, max(bar.high for bar in selected), min(bar.low for bar in selected))


def classify_premarket(
    bars: tuple[HistoricalBar, ...],
    overnight_range: OvernightRange,
    acceptance_bars: int = 1,
) -> tuple[PremarketState, ...]:
    """Classify each completed Pre-market bar using fixed Overnight levels."""
    if acceptance_bars < 1:
        raise ValueError("acceptance_bars must be positive")
    ordered = sorted(
        (bar for bar in bars if _is_premarket_bar(bar, overnight_range.session_date)),
        key=lambda bar: bar.bar_start_utc,
    )
    states: list[PremarketState] = []
    breakout: PremarketState | None = None
    outside_count = 0
    for bar in ordered:
        state = _breakout_state(bar.close, overnight_range)
        if state is PremarketState.NORMAL:
            if breakout is not None and outside_count >= acceptance_bars:
                states.append(PremarketState.FAILED_BREAKOUT)
                breakout = None
                outside_count = 0
            else:
                states.append(PremarketState.NORMAL)
            continue
        if breakout is None:
            breakout = state
            outside_count = 1
        elif state is breakout:
            outside_count += 1
        else:
            breakout = state
            outside_count = 1
        states.append(_accepted_state(breakout, outside_count, acceptance_bars))
    return tuple(states)


def _is_premarket_bar(bar: HistoricalBar, session_date: date) -> bool:
    local = bar.bar_start_et
    return local.date() == session_date and time(4) <= local.timetz().replace(tzinfo=None) < time(9, 30)


def _breakout_state(close: Decimal, overnight_range: OvernightRange) -> PremarketState:
    if close > overnight_range.high:
        return PremarketState.BULLISH_BREAKOUT
    if close < overnight_range.low:
        return PremarketState.BEARISH_BREAKDOWN
    return PremarketState.NORMAL


def _accepted_state(state: PremarketState, count: int, required: int) -> PremarketState:
    if count < required:
        return state
    if state is PremarketState.BULLISH_BREAKOUT:
        return PremarketState.BULLISH_ACCEPTED
    return PremarketState.BEARISH_ACCEPTED
