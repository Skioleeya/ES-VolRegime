"""Historical-bar quality measurements and research-session coverage."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from .models import HistoricalBar
from src.config import DEFAULT_SESSION_CONFIG, SessionConfig

ET = ZoneInfo("America/New_York")
FIVE_MINUTES = timedelta(minutes=5)
OVERNIGHT_START = DEFAULT_SESSION_CONFIG.session_start
PREMARKET_START = DEFAULT_SESSION_CONFIG.overnight_end
CASH_START = time(9, 30)
CASH_END = DEFAULT_SESSION_CONFIG.session_end


@dataclass(frozen=True)
class HistoricalQualityReport:
    """Auditable quality summary for one returned request or dataset."""

    total_bars: int
    unique_timestamps: int
    duplicate_timestamps: int
    invalid_contract_bars: int
    research_phase_counts: dict[str, int]
    gaps: tuple[tuple[datetime, datetime], ...]

    @property
    def status(self) -> str:
        # Overlap between adjacent IBKR duration windows is expected; the
        # repository removes it by the canonical contract/timestamp key.
        return "PASS" if self.invalid_contract_bars == 0 else "FAIL"


def build_quality_report(
    bars: tuple[HistoricalBar, ...],
    expected_contract_id: int,
) -> HistoricalQualityReport:
    timestamps = [bar.bar_start_utc for bar in bars]
    unique = set(timestamps)
    phases = {"OVERNIGHT": 0, "PRE-MARKET": 0, "CASH": 0}
    for bar in bars:
        phase = research_phase(bar.bar_start_et)
        if phase is not None:
            phases[phase] += 1
    return HistoricalQualityReport(
        total_bars=len(bars),
        unique_timestamps=len(unique),
        duplicate_timestamps=len(timestamps) - len(unique),
        invalid_contract_bars=sum(bar.contract.con_id != expected_contract_id for bar in bars),
        research_phase_counts=phases,
        gaps=_find_gaps(bars),
    )


def research_phase(timestamp_et: datetime, session_config: SessionConfig = DEFAULT_SESSION_CONFIG) -> str | None:
    """Return the whitepaper phase for a bar, or None outside research hours."""
    local_time = timestamp_et.astimezone(ET).time()
    if local_time >= session_config.session_start or local_time < session_config.overnight_end:
        return "OVERNIGHT"
    if session_config.overnight_end <= local_time < session_config.premarket_end:
        return "PRE-MARKET"
    if session_config.premarket_end <= local_time < session_config.session_end:
        return "CASH"
    return None


def _find_gaps(bars: tuple[HistoricalBar, ...]) -> tuple[tuple[datetime, datetime], ...]:
    ordered = sorted({bar.bar_start_utc for bar in bars})
    return tuple(
        (previous, current)
        for previous, current in zip(ordered, ordered[1:])
        if current - previous > FIVE_MINUTES
    )
