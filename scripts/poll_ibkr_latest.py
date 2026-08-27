#!/usr/bin/env python3
"""Poll and persist the latest completed ES 5-minute bar from IB Gateway."""

import argparse
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from src.connectivity.config import IbkrConfig
from src.historical import HistoricalRepository, QualifiedContract
from src.historical.client import HistoricalClient
from src.historical.collector import HistoricalCollector
from src.historical.polling import LatestBarPoller


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/historical.sqlite"))
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--once", action="store_true", help="poll once immediately after calibration")
    parser.add_argument("--max-polls", type=int, help="stop after this many boundary-aligned polls")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv()
    config = IbkrConfig.from_environment()
    requested = QualifiedContract(0, "", config.last_trade_date, config.symbol, config.exchange, config.currency)
    client = HistoricalClient()
    repository = HistoricalRepository(args.database)
    try:
        client.connect(config.host, config.port, config.client_id)
        threading.Thread(target=client.run, daemon=True).start()
        if not client.connected_event.wait(args.timeout_seconds):
            raise TimeoutError("IBKR connection callback did not arrive")
        actual = client.qualify(
            _qualification_request(requested), 20_000, args.timeout_seconds
        )
        contract = QualifiedContract(
            actual.conId, actual.localSymbol, config.last_trade_date,
            config.symbol, config.exchange, config.currency,
        )
        poller = LatestBarPoller(client, HistoricalCollector(client), contract, args.timeout_seconds)
        if args.once:
            bar = poller.poll_once()
            repository.save_bars((bar,))
            print(f"POLL RESULT: PASS bar_start_utc={bar.bar_start_utc.isoformat()} close={bar.close}")
            return 0
        poll_count = 0
        while args.max_polls is None or poll_count < args.max_polls:
            poller.wait_for_next_poll()
            bar = poller.poll_once()
            repository.save_bars((bar,))
            poll_count += 1
            print(f"POLL RESULT: PASS bar_start_utc={bar.bar_start_utc.isoformat()} close={bar.close}", flush=True)
        return 0
    except Exception as exc:
        print(f"POLL RESULT: FAIL - {exc}", file=sys.stderr)
        return 1
    finally:
        if client.isConnected():
            client.disconnect()
        repository.close()


def _qualification_request(contract: QualifiedContract):
    from datetime import datetime, timezone
    from src.historical.models import HistoricalRequest

    now = datetime.now(timezone.utc)
    return HistoricalRequest(contract, now, now, now, now, "300 S")


if __name__ == "__main__":
    raise SystemExit(main())
