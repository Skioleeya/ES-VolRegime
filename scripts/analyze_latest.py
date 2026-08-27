#!/usr/bin/env python3
"""Print a point-in-time volatility analysis from persisted ES bars."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.historical import HistoricalRepository, QualifiedContract
from src.volatility import analyze_latest, calculate_phase_metrics


def main() -> int:
    args = _parse_args()
    contract = QualifiedContract(args.con_id, args.local_symbol, args.contract_month)
    repository = HistoricalRepository(args.database)
    try:
        bars = repository.load_bars(contract)
        metrics = calculate_phase_metrics(bars)
        result = analyze_latest(metrics, metrics, args.confirmation_bars)
        print(f"bar_start_utc={result.metric.bar_start_utc.isoformat()}")
        print(f"phase={result.metric.phase.value} elapsed_minutes={result.metric.elapsed_minutes}")
        print(f"rv={result.metric.realized_volatility} range={result.metric.range_value}")
        print(f"rv_percentile={result.benchmark.realized_volatility_percentile}")
        print(f"range_percentile={result.benchmark.range_percentile}")
        print(f"samples={result.benchmark.sample_count} compression={result.compression.value}")
        return 0
    finally:
        repository.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/historical.sqlite"))
    parser.add_argument("--con-id", type=int, required=True)
    parser.add_argument("--local-symbol", required=True)
    parser.add_argument("--contract-month", required=True)
    parser.add_argument("--confirmation-bars", type=int, default=2)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
