"""Select a live ES future from IBKR's contract chain and a calendar rule."""

from datetime import date, datetime, timedelta
from typing import Protocol

from src.config import DEFAULT_SESSION_CONFIG, SessionConfig

from .models import QualifiedContract


class ContractDetail(Protocol):
    contract: object


def select_cme_equity_lead_contract(
    details: tuple[ContractDetail, ...],
    as_of: datetime,
    session_config: SessionConfig = DEFAULT_SESSION_CONFIG,
) -> QualifiedContract:
    """Choose the configured quarterly lead month from the IBKR contract chain."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    local = as_of.astimezone(session_config.timezone)
    candidates = sorted(
        ((_contract_month(detail.contract.lastTradeDateOrContractMonth), detail.contract) for detail in details),
        key=lambda item: (item[0], item[1].conId),
    )
    if not candidates:
        raise ValueError("IBKR returned no ES futures contracts")
    for contract_month, candidate in candidates:
        if contract_month.month not in session_config.roll_quarterly_months:
            raise ValueError(f"IBKR returned non-quarterly ES contract month {contract_month:%Y%m}")
        if local < calendar_rule_roll_start(contract_month, session_config):
            return QualifiedContract(
                candidate.conId, candidate.localSymbol, candidate.lastTradeDateOrContractMonth,
                candidate.symbol, candidate.exchange, candidate.currency,
            )
    raise ValueError("IBKR returned no eligible ES futures contract after calendar-rule roll")


def calendar_rule_roll_start(contract_month: date, session_config: SessionConfig = DEFAULT_SESSION_CONFIG) -> datetime:
    """Return the prior-session start for the configured monthly roll rule."""
    roll_date = calendar_rule_roll_date(contract_month, session_config)
    return datetime.combine(roll_date - timedelta(days=1), session_config.session_start, session_config.timezone)


def calendar_rule_roll_date(contract_month: date, session_config: SessionConfig = DEFAULT_SESSION_CONFIG) -> date:
    """Compute the configured roll weekday before the nth reference weekday."""
    if contract_month.month not in session_config.roll_quarterly_months:
        raise ValueError(f"contract month {contract_month:%Y%m} is not configured for quarterly rolling")
    first_day = contract_month.replace(day=1)
    reference = first_day + timedelta(
        days=(session_config.roll_reference_weekday - first_day.weekday()) % 7
        + 7 * (session_config.roll_reference_occurrence - 1)
    )
    return reference - timedelta(days=(reference.weekday() - session_config.roll_weekday) % 7)


def _contract_month(value: str) -> date:
    if len(value) not in {6, 8} or not value.isdigit():
        raise ValueError("IBKR contract has no usable contract month")
    return date(int(value[:4]), int(value[4:6]), 1)
