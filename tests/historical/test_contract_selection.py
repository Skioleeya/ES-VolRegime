from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from src.historical.contract_selection import calendar_rule_roll_date, calendar_rule_roll_start, select_cme_equity_lead_contract


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
    realExpirationDate: str = ""


def test_calendar_rule_starts_at_sunday_session_before_third_friday():
    assert calendar_rule_roll_start(date(2026, 9, 1)) == datetime(2026, 9, 13, 18, tzinfo=ZoneInfo("America/New_York"))


def test_calendar_rule_preserves_18_et_through_spring_dst_transition():
    assert calendar_rule_roll_start(date(2027, 3, 1)) == datetime(2027, 3, 14, 18, tzinfo=ZoneInfo("America/New_York"))


def test_calendar_rule_ignores_holiday_adjusted_real_expiration_date():
    assert calendar_rule_roll_date(date(2026, 6, 1)) == date(2026, 6, 15)
    details = (
        Detail(Contract(1, "ESM6", "202606"), "20260618"),
        Detail(Contract(2, "ESU6", "202609"), "20260918"),
    )
    result = select_cme_equity_lead_contract(details, datetime(2026, 6, 14, 22, tzinfo=timezone.utc))
    assert result.local_symbol == "ESU6"


def test_selects_next_contract_at_calendar_rule_roll():
    details = (
        Detail(Contract(1, "ESU6", "202609"), "20260918"),
        Detail(Contract(2, "ESZ6", "202612"), "20261218"),
    )
    before = select_cme_equity_lead_contract(details, datetime(2026, 9, 13, 21, 59, tzinfo=timezone.utc))
    result = select_cme_equity_lead_contract(details, datetime(2026, 9, 13, 22, tzinfo=timezone.utc))
    assert before.local_symbol == "ESU6"
    assert result.local_symbol == "ESZ6"


def test_selection_fails_without_next_contract_after_roll():
    details = (Detail(Contract(1, "ESU6", "202609"), "20260918"),)
    with pytest.raises(ValueError, match="no eligible ES futures contract"):
        select_cme_equity_lead_contract(details, datetime(2026, 9, 13, 22, tzinfo=timezone.utc))


def test_selection_fails_for_non_quarterly_contract_month():
    details = (Detail(Contract(1, "ESN6", "202607"), "20260717"),)
    with pytest.raises(ValueError, match="non-quarterly"):
        select_cme_equity_lead_contract(details, datetime(2026, 7, 1, tzinfo=timezone.utc))


def test_calendar_rule_has_no_end_date():
    assert calendar_rule_roll_date(date(2037, 12, 1)) == date(2037, 12, 14)
