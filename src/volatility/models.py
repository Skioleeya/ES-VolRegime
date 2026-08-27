"""Domain records for phase-level volatility measurements."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from decimal import Decimal


class ResearchPhase(str, Enum):
    OVERNIGHT = "OVERNIGHT"
    PREMARKET = "PREMARKET"
    CASH = "CASH"


class CompressionState(str, Enum):
    NORMAL = "NORMAL"
    WEAK_COMPRESSION = "WEAK_COMPRESSION"
    STRONG_COMPRESSION = "STRONG_COMPRESSION"
    UNAVAILABLE = "UNAVAILABLE"


class PremarketState(str, Enum):
    NORMAL = "PREMARKET_NORMAL"
    BULLISH_BREAKOUT = "PREMARKET_BULLISH_BREAKOUT"
    BEARISH_BREAKDOWN = "PREMARKET_BEARISH_BREAKDOWN"
    BULLISH_ACCEPTED = "PREMARKET_BULLISH"
    BEARISH_ACCEPTED = "PREMARKET_BEARISH"
    FAILED_BREAKOUT = "PREMARKET_FAILED_BREAKOUT"


class ExpansionState(str, Enum):
    NORMAL = "NORMAL"
    EXPANSION = "EXPANSION"
    UNAVAILABLE = "UNAVAILABLE"


class CashState(str, Enum):
    NEUTRAL = "CASH_NEUTRAL"
    BULLISH = "CASH_BULLISH"
    BEARISH = "CASH_BEARISH"


@dataclass(frozen=True)
class PhaseMetric:
    phase: ResearchPhase
    session_date: date
    elapsed_minutes: int
    bar_start_utc: datetime
    close_to_close_return: Decimal
    realized_variance: Decimal
    realized_volatility: Decimal
    range_value: Decimal


@dataclass(frozen=True)
class BenchmarkResult:
    """Same-phase and same-elapsed historical comparison."""

    phase: ResearchPhase
    elapsed_minutes: int
    realized_volatility_percentile: Decimal | None
    range_percentile: Decimal | None
    sample_count: int

    @property
    def available(self) -> bool:
        return self.sample_count >= 20


@dataclass(frozen=True)
class ExpansionConfig:
    """Explicit, provisional thresholds for research classification."""

    rv_percentile_threshold: Decimal = Decimal("80")
    require_positive_change: bool = True
