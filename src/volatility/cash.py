"""Cash-session opening range derived from completed five-minute bars."""

from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal

from src.historical.models import HistoricalBar

from .models import CashState, ExpansionState


@dataclass(frozen=True)
class OpeningRange:
    session_date: date
    high: Decimal
    low: Decimal

    @property
    def width(self) -> Decimal:
        return self.high - self.low


def build_opening_range(bars: tuple[HistoricalBar, ...], session_date: date) -> OpeningRange:
    """Build the fixed 09:30-09:45 ET Cash opening range."""
    selected = tuple(
        bar for bar in bars
        if bar.bar_start_et.date() == session_date
        and time(9, 30) <= bar.bar_start_et.timetz().replace(tzinfo=None) < time(9, 45)
    )
    if len(selected) != 3:
        raise ValueError(f"expected 3 Cash opening bars, received {len(selected)}")
    return OpeningRange(session_date, max(bar.high for bar in selected), min(bar.low for bar in selected))


def classify_cash(
    bars: tuple[HistoricalBar, ...],
    opening_range: OpeningRange,
    expansion_states: tuple[ExpansionState, ...],
    acceptance_bars: int = 1,
) -> tuple[CashState, ...]:
    """Require opening-range acceptance and RV expansion for direction."""
    if acceptance_bars < 1:
        raise ValueError("acceptance_bars must be positive")
    ordered = sorted(
        (bar for bar in bars if _is_post_opening_bar(bar, opening_range.session_date)),
        key=lambda bar: bar.bar_start_utc,
    )
    if len(ordered) != len(expansion_states):
        raise ValueError("one expansion state is required for each Cash bar")
    result: list[CashState] = []
    direction: CashState | None = None
    count = 0
    for bar, expansion in zip(ordered, expansion_states):
        candidate = _candidate(bar, opening_range)
        if candidate is CashState.NEUTRAL:
            result.append(CashState.NEUTRAL)
            direction = None
            count = 0
            continue
        if candidate is direction:
            count += 1
        else:
            direction = candidate
            count = 1
        accepted = count >= acceptance_bars and expansion is ExpansionState.EXPANSION
        result.append(direction if accepted else CashState.NEUTRAL)
    return tuple(result)


def _is_post_opening_bar(bar: HistoricalBar, session_date: date) -> bool:
    local = bar.bar_start_et
    return local.date() == session_date and local.timetz().replace(tzinfo=None) >= time(9, 45) and local.timetz().replace(tzinfo=None) < time(12)


def _candidate(bar: HistoricalBar, opening_range: OpeningRange) -> CashState:
    if bar.close > opening_range.high:
        return CashState.BULLISH
    if bar.close < opening_range.low:
        return CashState.BEARISH
    return CashState.NEUTRAL
