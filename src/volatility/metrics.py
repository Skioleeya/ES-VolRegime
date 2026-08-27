"""Calculate completed-bar volatility metrics by research phase."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal, getcontext
import math
from zoneinfo import ZoneInfo

from src.historical.models import HistoricalBar

from .models import PhaseMetric, ResearchPhase

ET = ZoneInfo("America/New_York")
ZERO = Decimal("0")
getcontext().prec = 28


def calculate_phase_metrics(bars: tuple[HistoricalBar, ...]) -> tuple[PhaseMetric, ...]:
    """Return cumulative RV metrics, resetting independently at each phase."""
    ordered = sorted(bars, key=lambda bar: bar.bar_start_utc)
    result: list[PhaseMetric] = []
    previous_close: Decimal | None = None
    phase_key: tuple[ResearchPhase, date] | None = None
    variance = ZERO
    phase_high: Decimal | None = None
    phase_low: Decimal | None = None
    for bar in ordered:
        classification = _classify(bar.bar_start_et)
        if classification is None:
            continue
        phase, session_date, elapsed = classification
        current_key = (phase, session_date)
        if current_key != phase_key:
            variance = ZERO
            phase_high = None
            phase_low = None
            previous_close = None
            phase_key = current_key
        log_return = _log_return(previous_close, bar.close)
        variance += log_return * log_return
        phase_high = bar.high if phase_high is None else max(phase_high, bar.high)
        phase_low = bar.low if phase_low is None else min(phase_low, bar.low)
        result.append(PhaseMetric(phase, session_date, elapsed, bar.bar_start_utc,
                                  log_return, variance, variance.sqrt(), phase_high - phase_low))
        previous_close = bar.close
    return tuple(result)


def _classify(value: datetime) -> tuple[ResearchPhase, date, int] | None:
    local = value.astimezone(ET)
    clock = local.timetz().replace(tzinfo=None)
    if clock >= time(20, 15):
        start = datetime.combine(local.date(), time(20, 15), ET)
        return ResearchPhase.OVERNIGHT, local.date() + timedelta(days=1), _elapsed(local, start)
    if clock < time(4):
        start = datetime.combine(local.date() - timedelta(days=1), time(20, 15), ET)
        return ResearchPhase.OVERNIGHT, local.date(), _elapsed(local, start)
    if clock < time(9, 30):
        start = datetime.combine(local.date(), time(4), ET)
        return ResearchPhase.PREMARKET, local.date(), _elapsed(local, start)
    if clock < time(12):
        start = datetime.combine(local.date(), time(9, 30), ET)
        return ResearchPhase.CASH, local.date(), _elapsed(local, start)
    return None


def _elapsed(value: datetime, start: datetime) -> int:
    return int((value - start).total_seconds() // 60)


def _log_return(previous: Decimal | None, close: Decimal) -> Decimal:
    if previous is None:
        return ZERO
    if previous <= ZERO or close <= ZERO:
        raise ValueError("close prices must be positive")
    return Decimal(str(math.log(float(close / previous))))
