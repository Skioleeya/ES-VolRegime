import pytest

from src.volatility import CashState, CompressionState, ExpansionState, PremarketState, RegimeState, ResearchPhase, compose_regime


@pytest.mark.parametrize(("state", "expected"), [
    (CompressionState.NORMAL, RegimeState.NORMAL),
    (CompressionState.WEAK_COMPRESSION, RegimeState.WEAK_COMPRESSION),
    (CompressionState.STRONG_COMPRESSION, RegimeState.STRONG_COMPRESSION),
])
def test_compose_overnight_states(state, expected):
    assert compose_regime(ResearchPhase.OVERNIGHT, compression=state) is expected


def test_compose_premarket_expansion_and_direction():
    assert compose_regime(ResearchPhase.PREMARKET, premarket=PremarketState.NORMAL, expansion=ExpansionState.EXPANSION) is RegimeState.PREMARKET_EXPANSION_WATCH
    assert compose_regime(ResearchPhase.PREMARKET, premarket=PremarketState.BULLISH_ACCEPTED) is RegimeState.PREMARKET_BULLISH
    assert compose_regime(ResearchPhase.PREMARKET, premarket=PremarketState.FAILED_BREAKOUT) is RegimeState.PREMARKET_FAILED_BREAKOUT


def test_compose_cash_states_and_missing_inputs_fail_closed():
    assert compose_regime(ResearchPhase.CASH, cash=CashState.BULLISH) is RegimeState.CASH_BULLISH
    assert compose_regime(ResearchPhase.CASH) is RegimeState.DATA_INSUFFICIENT
