#!/usr/bin/env python3
"""Poll and persist the latest completed ES 5-minute bar from IB Gateway."""

import argparse
from pathlib import Path
import sys
import threading
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from src.connectivity.config import IbkrConfig
from src.config import DEFAULT_SESSION_CONFIG
from src.historical import HistoricalRepository, QualifiedContract, recover_session, select_cme_equity_lead_contract
from src.historical import retry_operation
from src.historical.client import HistoricalClient
from src.historical.collector import HistoricalCollector
from src.historical.polling import LatestBarPoller, active_session_date


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/historical.sqlite"))
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--once", action="store_true", help="poll once immediately after calibration")
    parser.add_argument("--max-polls", type=int, help="stop after this many boundary-aligned polls")
    parser.add_argument("--retries", type=int, default=3, help="finite retries for collection operations")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv()
    config = IbkrConfig.from_environment()
    client = HistoricalClient()
    repository = HistoricalRepository(args.database)
    try:
        client.connect(config.host, config.port, config.client_id)
        threading.Thread(target=client.run, daemon=True).start()
        if not client.connected_event.wait(args.timeout_seconds):
            raise TimeoutError("IBKR connection callback did not arrive")
        collector = HistoricalCollector(client)
        contract = _select_live_contract(client, config, args.timeout_seconds)
        poller = LatestBarPoller(client, collector, contract, args.timeout_seconds)
        if args.once:
            contract = _lock_session_contract(client, repository, config, args.timeout_seconds)
            poller = LatestBarPoller(client, collector, contract, args.timeout_seconds)
            _recover_current_session(client, repository, collector, contract, args.timeout_seconds)
            bar = retry_operation(poller.poll_once, attempts=args.retries)
            repository.save_bars((bar,))
            _refresh_coverage(repository, contract, bar)
            print(f"POLL RESULT: PASS bar_start_utc={bar.bar_start_utc.isoformat()} close={bar.close}")
            return 0
        poll_count = 0
        locked_session = None
        while args.max_polls is None or poll_count < args.max_polls:
            poller.wait_for_next_poll()
            contract, session_date = _lock_session_contract(client, repository, config, args.timeout_seconds, with_session=True)
            if session_date != locked_session:
                poller = LatestBarPoller(client, collector, contract, args.timeout_seconds)
                _recover_current_session(client, repository, collector, contract, args.timeout_seconds)
                locked_session = session_date
            bar = retry_operation(poller.poll_once, attempts=args.retries)
            repository.save_bars((bar,))
            _refresh_coverage(repository, contract, bar)
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


def _select_live_contract(client, config, timeout_seconds: float) -> QualifiedContract:
    epoch = client.request_server_time(timeout_seconds)
    server_now = datetime.fromtimestamp(epoch, timezone.utc)
    details = client.futures_chain(config.symbol, config.exchange, config.currency, 20_000, timeout_seconds)
    return select_cme_equity_lead_contract(details, server_now)


def _lock_session_contract(client, repository, config, timeout_seconds: float, with_session: bool = False):
    epoch = client.request_server_time(timeout_seconds)
    server_now = datetime.fromtimestamp(epoch, timezone.utc)
    session_date = active_session_date(server_now)
    if session_date is None:
        raise RuntimeError("contract selection requires an active CME research session")
    contract = repository.load_contract_selection(session_date.isoformat())
    if contract is None:
        details = client.futures_chain(config.symbol, config.exchange, config.currency, 20_000, timeout_seconds)
        contract = select_cme_equity_lead_contract(details, server_now)
        repository.save_contract_selection(session_date.isoformat(), contract, server_now)
    return (contract, session_date) if with_session else contract


def _refresh_coverage(repository, contract, bar) -> None:
    local = bar.bar_start_et
    session_date = local.date() + timedelta(days=1) if local.timetz().replace(tzinfo=None) >= DEFAULT_SESSION_CONFIG.session_start else local.date()
    actual, missing = repository.refresh_coverage(session_date, contract)
    print(f"COVERAGE: session_date={session_date} actual={actual} missing={missing}", flush=True)


def _recover_current_session(client, repository, collector, contract, timeout_seconds: float) -> None:
    epoch = client.request_server_time(timeout_seconds)
    server_now = datetime.fromtimestamp(epoch, timezone.utc)
    session_date = active_session_date(server_now)
    if session_date is None:
        return
    result = recover_session(session_date, contract, repository, collector, server_now)
    print(f"RECOVERY: session_date={result.session_date} requested={result.requested_bars} recovered={result.recovered_bars} remaining={result.remaining_bars}", flush=True)


def _require_active_session(client, timeout_seconds: float) -> None:
    epoch = client.request_server_time(timeout_seconds)
    server_now = datetime.fromtimestamp(epoch, timezone.utc)
    if active_session_date(server_now) is None:
        raise RuntimeError("--once requires an active CME research session")


if __name__ == "__main__":
    raise SystemExit(main())
