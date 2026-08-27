from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from src.historical.contract_selection import CmeEquityRollCalendar, cme_equity_roll_start, select_cme_equity_lead_contract


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


def test_cme_roll_starts_sunday_before_expiration_week():
    calendar = CmeEquityRollCalendar.load()
    assert cme_equity_roll_start(date(2026, 9, 18), calendar) == datetime(2026, 9, 13, 18, tzinfo=ZoneInfo("America/New_York"))


def test_selects_next_contract_at_cme_lead_month_roll():
    details = (
        Detail(Contract(1, "ESU6", "202609"), "20260918"),
        Detail(Contract(2, "ESZ6", "202612"), "20261218"),
    )
    before = select_cme_equity_lead_contract(details, datetime(2026, 9, 13, 21, 59, tzinfo=timezone.utc))
    result = select_cme_equity_lead_contract(details, datetime(2026, 9, 13, 22, tzinfo=timezone.utc))
    assert before.local_symbol == "ESU6"
    assert result.local_symbol == "ESZ6"


def test_selection_fails_without_eligible_contract():
    details = (Detail(Contract(1, "ESU6", "202609"), "20260918"),)
    with pytest.raises(ValueError, match="no eligible CME equity"):
        select_cme_equity_lead_contract(details, datetime(2026, 9, 13, 22, tzinfo=timezone.utc))


def test_selection_fails_when_official_roll_date_is_unavailable():
    details = (Detail(Contract(1, "ESH9", "202903"), "20290316"),)
    with pytest.raises(ValueError, match="roll date unavailable"):
        select_cme_equity_lead_contract(details, datetime(2029, 3, 1, tzinfo=timezone.utc))


def test_unneeded_far_contract_does_not_require_a_roll_date():
    details = (
        Detail(Contract(1, "ESU6", "202609"), "20260918"),
        Detail(Contract(2, "ESH9", "202903"), "20290316"),
    )
    result = select_cme_equity_lead_contract(details, datetime(2026, 8, 27, tzinfo=timezone.utc))
    assert result.local_symbol == "ESU6"
