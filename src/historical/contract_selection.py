"""Select a live ES future from IBKR-provided contract details."""

from datetime import date, datetime, timedelta
from typing import Protocol

from .models import QualifiedContract


class ContractDetail(Protocol):
    contract: object
    realExpirationDate: str


def select_front_contract(
    details: tuple[ContractDetail, ...],
    as_of: datetime,
    roll_days_before_expiry: int,
) -> QualifiedContract:
    """Choose the earliest eligible future using an explicit calendar rule."""
    if roll_days_before_expiry < 0:
        raise ValueError("roll_days_before_expiry must not be negative")
    cutoff = as_of.date() + timedelta(days=roll_days_before_expiry)
    candidates = []
    for detail in details:
        expiry = _expiry(detail.realExpirationDate)
        contract = detail.contract
        if expiry > cutoff:
            candidates.append((expiry, contract))
    if not candidates:
        raise ValueError("IBKR returned no eligible futures contract after roll cutoff")
    expiry, selected = min(candidates, key=lambda item: (item[0], item[1].conId))
    return QualifiedContract(
        selected.conId, selected.localSymbol, selected.lastTradeDateOrContractMonth,
        selected.symbol, selected.exchange, selected.currency,
    )


def _expiry(value: str) -> date:
    if len(value) != 8 or not value.isdigit():
        raise ValueError("IBKR contract has no usable real expiration date")
    return date.fromisoformat(f"{value[:4]}-{value[4:6]}-{value[6:]}")
