from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from src.historical.contract_selection import select_front_contract


@dataclass
class Contract:
    conId: int
    localSymbol: str
    lastTradeDateOrContractMonth: str
    symbol: str = "ES"
    exchange: str = "CME"
    currency: str = "USD"


@dataclass
class Detail:
    contract: Contract
    realExpirationDate: str


def test_selects_nearest_contract_outside_roll_cutoff():
    details = (
        Detail(Contract(1, "ESU6", "202609"), "20260918"),
        Detail(Contract(2, "ESZ6", "202612"), "20261218"),
    )
    result = select_front_contract(details, datetime(2026, 9, 12, tzinfo=timezone.utc), 7)
    assert result.local_symbol == "ESZ6"


def test_selection_fails_without_eligible_contract():
    details = (Detail(Contract(1, "ESU6", "202609"), "20260918"),)
    with pytest.raises(ValueError, match="no eligible futures"):
        select_front_contract(details, datetime(2026, 9, 12, tzinfo=timezone.utc), 7)
