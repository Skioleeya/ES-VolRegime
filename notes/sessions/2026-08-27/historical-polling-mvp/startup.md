# Startup: historical-polling-mvp

STARTUP-PROOF: Read AGENTS.md, the prior historical-module-design session, existing historical client/collector/normalizer/repository modules, and official IBKR historical-bar/current-time documentation.

## Session

- Date: 2026-08-27
- Scope: Implement server-time-calibrated polling of one completed ES 5-minute historical bar.

## Scope Understanding

- In scope: IBKR server-time callback, five-minute boundary scheduling, one-bar request/validation, Linux CLI, focused tests.
- Out of scope: tick aggregation, orders, automatic retries, alternate data sources, cloud deployment.

## Prior Context Read

- `AGENTS.md`
- `notes/sessions/2026-08-27/historical-module-design/`
- `src/historical/client.py`, `collector.py`, `normalizer.py`, `repository.py`
- `docs/ibkr-historical-data.md`, `docs/historical-module-design.md`

## Recent Git Context

- Key commits reviewed: N/A: repository has no commits yet.

## Worker Readiness

- Risks noticed: Gateway finalization delay, server/local clock skew, historical pacing, and missing target bars.
- Blockers noticed: N/A.
