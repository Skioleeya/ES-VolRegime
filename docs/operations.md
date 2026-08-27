# Linux Operations

## Preconditions

1. Start exactly one Paper IB Gateway session for the configured account.
2. Confirm API access is enabled and the configured port is reachable from the
   Linux process.
3. Keep `.env` outside version control. It must contain the explicitly
   qualified active contract month, for example `ES_LAST_TRADE_DATE=202609`.
4. Do not run another TWS/Gateway session for the same account from a second
   IP. IBKR may reject the request with error 162.
5. Keep `config/session.toml` under version control as the sole research-session
   configuration source. Missing or invalid values stop the process at startup.
6. The poller resolves and locks the active ES future through IBKR at the first
   bar of each research session. `ES_LAST_TRADE_DATE` is no longer required for
   the poller; configure `ES_ROLL_DAYS_BEFORE_EXPIRY` instead.

## One-Cycle Acceptance

From the repository root:

```bash
.venv/bin/python scripts/poll_ibkr_latest.py --max-polls 1 --timeout-seconds 30
```

The process obtains IBKR server time, waits until the next five-minute
boundary plus seven seconds, requests one 300-second historical window, keeps
the previous completed bar, normalizes it to UTC, and upserts it into
`data/historical.sqlite`.

## Continuous Mode

```bash
.venv/bin/python scripts/poll_ibkr_latest.py --timeout-seconds 30
```

The process remains attached to the terminal and polls once per boundary. A
Gateway error, timeout, missing bar, or contract mismatch exits explicitly;
After finite retries are exhausted, the process exits explicitly. There is no
local-clock substitution, Tick aggregation, or alternate data source.

## Service Deployment

Install `deploy/es-volregime-poller.service` as a systemd unit after setting
the absolute repository path and service user. The unit restarts only when the
poller exits. The poller itself retries an individual collection operation a
finite number of times (`--retries`, default `3`) and then exits explicitly;
it never silently changes data sources or time semantics.

## Analysis and Replay

```bash
.venv/bin/python scripts/analyze_latest.py --con-id 649180671 --local-symbol ESU6 --contract-month 202609
.venv/bin/python scripts/replay_regimes.py --con-id 649180671 --local-symbol ESU6 --contract-month 202609
```

Use `scripts/evaluate_expansion.py` to inspect the provisional Expansion
threshold by Phase. Its result is a research diagnostic, not an automatic
configuration update.

## Acceptance Gates

Before cloud deployment, require one successful live cycle, a full market
window without duplicate timestamps, a 20-session same-elapsed benchmark,
prefix-invariant replay, and an operator-reviewed Gateway session policy.
