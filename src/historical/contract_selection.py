"""Select a live ES future from IBKR-provided contract details."""

from datetime import date, datetime, time, timedelta
from typing import Protocol

from .models import QualifiedContract
from src.config import DEFAULT_SESSION_CONFIG, SessionConfig


class ContractDetail(Protocol):
    contract: object
    realExpirationDate: str


def select_cme_equity_lead_contract(
    details: tuple[ContractDetail, ...],
    as_of: datetime,
    session_config: SessionConfig = DEFAULT_SESSION_CONFIG,
) -> QualifiedContract:
    """Choose CME's lead month, effective at the prior Sunday session start."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    local = as_of.astimezone(session_config.timezone)
    candidates = []
    for detail in details:
        expiry = _expiry(detail.realExpirationDate)
        contract = detail.contract
        if local < cme_equity_roll_start(expiry, session_config):
            candidates.append((expiry, contract))
    if not candidates:
        raise ValueError("IBKR returned no eligible CME equity futures contract")
    expiry, selected = min(candidates, key=lambda item: (item[0], item[1].conId))
    return QualifiedContract(
        selected.conId, selected.localSymbol, selected.lastTradeDateOrContractMonth,
        selected.symbol, selected.exchange, selected.currency,
    )


def cme_equity_roll_start(expiration: date, session_config: SessionConfig = DEFAULT_SESSION_CONFIG) -> datetime:
    """Return the Sunday session start before CME's Monday lead-month roll date."""
    third_friday = _third_friday(expiration.year, expiration.month)
    monday = third_friday - timedelta(days=4)
    return datetime.combine(monday - timedelta(days=1), session_config.session_start, session_config.timezone)


def _third_friday(year: int, month: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(4 - first.weekday()) % 7 + 14)


def _expiry(value: str) -> date:
    if len(value) != 8 or not value.isdigit():
        raise ValueError("IBKR contract has no usable real expiration date")
    return date.fromisoformat(f"{value[:4]}-{value[4:6]}-{value[6:]}")
