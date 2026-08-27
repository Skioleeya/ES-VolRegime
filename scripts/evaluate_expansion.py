#!/usr/bin/env python3
"""Evaluate provisional Expansion thresholds on persisted ES bars."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.historical import HistoricalRepository, QualifiedContract
from src.volatility import calculate_phase_metrics
from src.volatility.evaluation import evaluate_expansion


def main() -> int:
    args = parse_args()
    repository = HistoricalRepository(args.database)
    try:
        bars = repository.load_bars(QualifiedContract(args.con_id, args.local_symbol, args.contract_month))
        result = evaluate_expansion(calculate_phase_metrics(bars))
        print(f"observations={result.observations}")
        print(f"available_benchmarks={result.available_benchmarks}")
        print(f"expansion_observations={result.expansion_observations}")
        for phase, observations, available, expansions in result.by_phase:
            print(f"phase={phase} observations={observations} available={available} expansions={expansions}")
        return 0
    finally:
        repository.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/historical.sqlite"))
    parser.add_argument("--con-id", type=int, required=True)
    parser.add_argument("--local-symbol", required=True)
    parser.add_argument("--contract-month", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
