"""Compose phase outputs into the project's top-level regime state."""

from enum import Enum

from .models import CashState, CompressionState, ExpansionState, PremarketState, ResearchPhase


class RegimeState(str, Enum):
    DATA_INSUFFICIENT = "DATA_INSUFFICIENT"
    NORMAL = "NORMAL"
    WEAK_COMPRESSION = "WEAK_COMPRESSION"
    STRONG_COMPRESSION = "STRONG_COMPRESSION"
    PREMARKET_EXPANSION_WATCH = "PREMARKET_EXPANSION_WATCH"
    PREMARKET_BULLISH = "PREMARKET_BULLISH"
    PREMARKET_BEARISH = "PREMARKET_BEARISH"
    PREMARKET_FAILED_BREAKOUT = "PREMARKET_FAILED_BREAKOUT"
    CASH_OPEN = "CASH_OPEN"
    CASH_NEUTRAL = "CASH_NEUTRAL"
    CASH_BULLISH = "CASH_BULLISH"
    CASH_BEARISH = "CASH_BEARISH"


def compose_regime(
    phase: ResearchPhase,
    compression: CompressionState | None = None,
    premarket: PremarketState | None = None,
    expansion: ExpansionState | None = None,
    cash: CashState | None = None,
) -> RegimeState:
    """Map already-computed phase states without applying hidden thresholds."""
    if phase is ResearchPhase.OVERNIGHT:
        return _overnight(compression)
    if phase is ResearchPhase.PREMARKET:
        return _premarket(premarket, expansion)
    return _cash(cash)


def _overnight(state: CompressionState | None) -> RegimeState:
    mapping = {
        CompressionState.WEAK_COMPRESSION: RegimeState.WEAK_COMPRESSION,
        CompressionState.STRONG_COMPRESSION: RegimeState.STRONG_COMPRESSION,
        CompressionState.NORMAL: RegimeState.NORMAL,
    }
    if state not in mapping:
        return RegimeState.DATA_INSUFFICIENT
    return mapping[state]


def _premarket(state: PremarketState | None, expansion: ExpansionState | None) -> RegimeState:
    if state is PremarketState.BULLISH_ACCEPTED:
        return RegimeState.PREMARKET_BULLISH
    if state is PremarketState.BEARISH_ACCEPTED:
        return RegimeState.PREMARKET_BEARISH
    if state is PremarketState.FAILED_BREAKOUT:
        return RegimeState.PREMARKET_FAILED_BREAKOUT
    if expansion is ExpansionState.EXPANSION:
        return RegimeState.PREMARKET_EXPANSION_WATCH
    if state in {PremarketState.NORMAL, PremarketState.BULLISH_BREAKOUT, PremarketState.BEARISH_BREAKDOWN}:
        return RegimeState.NORMAL
    return RegimeState.DATA_INSUFFICIENT


def _cash(state: CashState | None) -> RegimeState:
    if state is CashState.BULLISH:
        return RegimeState.CASH_BULLISH
    if state is CashState.BEARISH:
        return RegimeState.CASH_BEARISH
    if state is CashState.NEUTRAL:
        return RegimeState.CASH_NEUTRAL
    return RegimeState.DATA_INSUFFICIENT
