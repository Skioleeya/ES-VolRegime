"""Explicit environment configuration for the IBKR MVP probe."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class IbkrConfig:
    host: str
    port: int
    client_id: int
    timeout_seconds: int
    realtime_seconds: int
    symbol: str
    exchange: str
    currency: str
    last_trade_date: str | None
    roll_mode: str

    @classmethod
    def from_environment(cls) -> "IbkrConfig":
        required = {"IBKR_HOST", "IBKR_PORT", "IBKR_CLIENT_ID"}
        missing = sorted(name for name in required if not os.getenv(name))
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        last_trade_date = os.getenv("ES_LAST_TRADE_DATE")
        if last_trade_date and last_trade_date.startswith("REPLACE_"):
            raise ValueError("ES_LAST_TRADE_DATE must not contain a placeholder")
        roll_mode = os.getenv("ES_ROLL_MODE", "cme_equity_lead_month")
        if roll_mode != "cme_equity_lead_month":
            raise ValueError(f"unsupported ES_ROLL_MODE: {roll_mode}")
        return cls(
            host=os.environ["IBKR_HOST"],
            port=int(os.environ["IBKR_PORT"]),
            client_id=int(os.environ["IBKR_CLIENT_ID"]),
            timeout_seconds=int(os.getenv("IBKR_TIMEOUT_SECONDS", "15")),
            realtime_seconds=int(os.getenv("IBKR_REALTIME_SECONDS", "10")),
            symbol=os.getenv("ES_SYMBOL", "ES"),
            exchange=os.getenv("ES_EXCHANGE", "CME"),
            currency=os.getenv("ES_CURRENCY", "USD"),
            last_trade_date=last_trade_date,
            roll_mode=roll_mode,
        )
