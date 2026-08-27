#!/usr/bin/env python3
"""Replay persisted ES bars and print the latest top-level regime snapshot."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.historical import HistoricalRepository, QualifiedContract
from src.volatility import build_regime_snapshots


def main() -> int:
    args = parse_args()
    repository = HistoricalRepository(args.database)
    try:
        contract = QualifiedContract(args.con_id, args.local_symbol, args.contract_month)
        snapshots = build_regime_snapshots(repository.load_bars(contract))
        if not snapshots:
            raise ValueError("no in-window completed bars were found")
        latest = snapshots[-1]
        print(f"snapshots={len(snapshots)}")
        print(f"bar_start_utc={latest.metric.bar_start_utc.isoformat()}")
        print(f"phase={latest.metric.phase.value} elapsed_minutes={latest.metric.elapsed_minutes}")
        print(f"samples={latest.sample_count} expansion={latest.expansion.value}")
        print(f"rv_percentile={latest.rv_percentile} range_percentile={latest.range_percentile}")
        print(f"compression={latest.compression.value if latest.compression else 'UNAVAILABLE'}")
        print(f"premarket={latest.premarket.value if latest.premarket else 'UNAVAILABLE'}")
        print(f"regime={latest.regime.value}")
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
