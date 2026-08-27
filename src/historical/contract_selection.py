"""Select a live ES future from IBKR-provided contract details."""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path
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
    roll_calendar: "CmeEquityRollCalendar | None" = None,
) -> QualifiedContract:
    """Choose CME's lead month, effective at the prior Sunday session start."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    local = as_of.astimezone(session_config.timezone)
    calendar = roll_calendar or CmeEquityRollCalendar.load()
    candidates = sorted(
        ((_expiry(detail.realExpirationDate), detail.contract) for detail in details),
        key=lambda item: (item[0], item[1].conId),
    )
    for expiry, candidate in candidates:
        if local < cme_equity_roll_start(expiry, calendar, session_config):
            return QualifiedContract(
                candidate.conId, candidate.localSymbol, candidate.lastTradeDateOrContractMonth,
                candidate.symbol, candidate.exchange, candidate.currency,
            )
    raise ValueError("IBKR returned no eligible CME equity futures contract")


class CmeEquityRollCalendar:
    """Versioned CME-published U.S. Equity Index futures roll dates."""

    def __init__(self, roll_dates: dict[date, date]) -> None:
        self._roll_dates = roll_dates

    @classmethod
    def load(cls, path: Path | None = None) -> "CmeEquityRollCalendar":
        source = path or Path(__file__).resolve().parents[2] / "config" / "cme_equity_roll_dates.csv"
        with source.open(newline="") as handle:
            rows = csv.DictReader(handle)
            dates = {date.fromisoformat(row["expiration_date"]): date.fromisoformat(row["roll_date"]) for row in rows}
        if not dates:
            raise ValueError("CME equity roll calendar is empty")
        return cls(dates)

    def roll_date(self, expiration: date) -> date:
        try:
            return self._roll_dates[expiration]
        except KeyError as exc:
            raise ValueError(f"CME equity roll date unavailable for expiration {expiration}") from exc


def cme_equity_roll_start(
    expiration: date,
    roll_calendar: CmeEquityRollCalendar,
    session_config: SessionConfig = DEFAULT_SESSION_CONFIG,
) -> datetime:
    """Return session start before the official CME-published roll date."""
    return datetime.combine(roll_calendar.roll_date(expiration) - timedelta(days=1), session_config.session_start, session_config.timezone)




def _expiry(value: str) -> date:
    if len(value) != 8 or not value.isdigit():
        raise ValueError("IBKR contract has no usable real expiration date")
    return date.fromisoformat(f"{value[:4]}-{value[4:6]}-{value[6:]}")
