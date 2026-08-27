# Historical Data Module Design

## Objective

Download reproducible ES 5-minute `TRADES` bars from the active expiring
contract, preserve source metadata, and expose completed, timezone-aware bars
to later session and volatility modules.

## Boundaries

The module owns request planning, pacing, callback collection, validation, and
raw persistence. It does not own contract selection policy, session labeling,
roll selection, indicators, regime classification, or dashboard concerns.

## Proposed Layout

```text
src/historical/
    __init__.py
    models.py          # immutable request, bar, contract metadata records
    request_plan.py    # validates ranges and creates non-overlapping chunks
    pacing.py          # request timing and rolling-window accounting
    client.py          # thin TWS API adapter and callback translation
    collector.py       # one request lifecycle and completion/error state
    normalizer.py      # epoch/date conversion and completed-bar validation
    repository.py      # raw bar persistence and deterministic upsert
tests/historical/
    test_request_plan.py
    test_pacing.py
    test_normalizer.py
    test_replay.py
```

Dependencies point inward in one direction:

```text
connectivity.config -> historical.client -> historical.collector
historical.models <- request_plan, pacing, normalizer, repository
normalizer/repository -> later bars/session modules
```

No historical module imports indicators, regimes, dashboard code, or CLI
entrypoints. The TWS callback object is isolated in `client.py`.

## Data Contract

Each persisted row must contain:

```text
con_id, local_symbol, contract_month, bar_start_utc, bar_start_et,
open, high, low, close, volume, wap, bar_count,
what_to_show, use_rth, source, is_complete
```

`bar_start_utc` is the canonical key. `bar_start_et` is derived with
`America/New_York`; it is not independently trusted input. Numeric fields must
be finite, prices must be positive, and timestamps must align to five-minute
boundaries after normalization.

## Backfill Workflow

1. Require an explicitly qualified ES contract; fail on zero or multiple
   matches.
2. Validate the requested UTC interval and split it into bounded chunks.
3. Submit one chunk, collect callbacks, and require `historicalDataEnd`.
4. Record request parameters and gateway errors as structured evidence.
5. Normalize timestamps, reject incomplete/invalid bars, and upsert by the
   canonical key.
6. Advance to the next chunk only after the pacing policy permits it.
7. Emit a summary containing requested range, returned range, row count,
   duplicates, gaps, and errors.

IBKR requests are expressed as an end time plus duration, so adjacent duration
windows may overlap after server-side calendar rounding. This is reported as
an overlap metric and removed deterministically by the repository primary key;
it is not silently counted as additional stored data.

No retry or alternate data source is implicit. A retry, if later approved, must
be an explicit operator action with a new request record.

## Initial Configuration

The first implementation should use:

```text
bar_size = 5 mins
what_to_show = TRADES
use_rth = 0
format_date = 2
keep_up_to_date = False
chunk_duration = 30 D
max_in_flight = 1
minimum_same_request_gap = 15 s
```

The 30-day chunk is an implementation policy, not an IBKR limit. It keeps
response sizes bounded and makes gaps or partial failures observable.

## Acceptance Tests

- A fixed two-day ES request returns normalized 5-minute bars.
- A request spanning midnight preserves the correct ET calendar labels.
- DST transition days use timezone rules rather than fixed offsets.
- Duplicate chunk boundaries produce one row per canonical timestamp.
- Empty history, ambiguous contract, pacing error, and malformed timestamp
  fail explicitly.
- Replaying bars in reverse order does not change earlier persisted states.
- A future bar cannot affect a prior session or volatility result.

Observed gaps are classified after retrieval as `CME_BREAK`,
`WEEKEND_OR_HOLIDAY`, `OUTSIDE_RESEARCH_WINDOW`, or `UNCLASSIFIED`. A gap is
reported for review; it is not filled or silently discarded. Replay evaluates
only bars whose five-minute interval has ended at the requested UTC as-of time.

Implementation begins with `models.py`, `request_plan.py`, and focused unit
tests, followed by the single-request collector against the already validated
Linux Gateway connection.

## Live Five-Minute Polling MVP

The live input path does not synthesize bars from ticks. It reuses the
historical collector and requests one 300-second window after each completed
five-minute boundary. On startup, the client obtains IBKR server time through
`reqCurrentTime`; local WSL time is never used to choose the target bar.

The scheduler waits until the next boundary plus seven seconds, then requests
the bar immediately before that boundary. The normalizer accepts it only when
`bar_start_utc + 5 minutes <= server_now`, and the repository upserts it by
`(con_id, bar_start_utc)`. Missing, incomplete, ambiguous, or mismatched bars
fail explicitly. The CLI is `scripts/poll_ibkr_latest.py`; `--once` is for
verification and the default mode continues polling.
