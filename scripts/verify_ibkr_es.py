#!/usr/bin/env python3
"""Run the non-trading Linux IBKR ES connectivity MVP."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from src.connectivity.config import IbkrConfig
from src.connectivity.probe import execute


def main() -> int:
    load_dotenv()
    try:
        result = execute(IbkrConfig.from_environment())
    except Exception as exc:
        print(f"MVP RESULT: FAIL - {exc}", file=sys.stderr)
        return 1
    for name, status in result.items():
        print(f"{name}: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
