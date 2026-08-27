#!/usr/bin/env python3
"""Backfill one bounded ES history window through Linux IB Gateway."""

import argparse
from datetime import date, timedelta
from dataclasses import replace
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from src.connectivity.config import IbkrConfig
from src.historical import HistoricalRepository, QualifiedContract, build_request_plan, normalize_completed_bar
from src.historical.client import HistoricalClient
from src.historical.collector import HistoricalCollector
from src.historical.report import build_quality_report


def parse_args() -> argparse.Namespace:
    today = date.today()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", type=date.fromisoformat, default=today - timedelta(days=2))
    parser.add_argument("--end-date", type=date.fromisoformat, default=today + timedelta(days=1))
    parser.add_argument("--database", type=Path, default=Path("data/historical.sqlite"))
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv()
    config = IbkrConfig.from_environment()
    requested_contract = QualifiedContract(0, "", config.last_trade_date, config.symbol, config.exchange, config.currency)
    plan = build_request_plan(requested_contract, args.start_date, args.end_date, 30)
    client = HistoricalClient()
    repository = HistoricalRepository(args.database)
    collector = HistoricalCollector(client)
    try:
        client.connect(config.host, config.port, config.client_id)
        threading.Thread(target=client.run, daemon=True).start()
        if not client.connected_event.wait(args.timeout_seconds):
            raise TimeoutError("IBKR connection callback did not arrive")
        actual = client.qualify(plan[0], 20_000, args.timeout_seconds)
        contract = QualifiedContract(actual.conId, actual.localSymbol, config.last_trade_date, config.symbol, config.exchange, config.currency)
        stored = 0
        all_bars = []
        for planned in plan:
            request = replace(planned, contract=contract)
            collected = collector.collect(request, args.timeout_seconds)
            bars = tuple(normalize_completed_bar(raw, contract, request.end_utc) for raw in collected.bars)
            request_id = collected.bars[0].request_id
            repository.record_request(request_id, contract.con_id, request.start_utc, request.end_utc, bars, collected.duplicate_timestamps, "PASS")
            stored += repository.save_bars(bars)
            all_bars.extend(bars)
            print(f"request={collected.request.duration_str} returned={len(bars)} stored={stored}")
        report = build_quality_report(tuple(all_bars), contract.con_id)
        print(f"quality={report.status} unique={report.unique_timestamps} duplicates={report.duplicate_timestamps} gaps={len(report.gaps)} phases={report.research_phase_counts}")
        if report.status != "PASS":
            raise RuntimeError("historical quality report failed")
        print(f"BACKFILL RESULT: PASS (returned={stored} unique_persisted={repository.count()} requests={repository.request_count()} bars)")
        return 0
    except Exception as exc:
        print(f"BACKFILL RESULT: FAIL - {exc}", file=sys.stderr)
        return 1
    finally:
        if client.isConnected():
            client.disconnect()
        repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
