# Startup: historical-module-design

STARTUP-PROOF: Read AGENTS.md, the ibkr-es-mvp handoff, and official IBKR TWS API historical-data documentation before design.

## Session

- Date: 2026-08-27
- Scope: Record official historical-data constraints and design the first historical module.

## Scope Understanding

- In scope: technical documentation and implementation design for ES 5-minute historical bars.
- Out of scope: code implementation, production deployment, order placement, and cloud operations.

## Prior Context Read

- `AGENTS.md`
- `notes/sessions/2026-08-27/ibkr-es-mvp/handoff.md`
- `src/connectivity/config.py`
- `src/connectivity/probe.py`
- Official IBKR TWS API pages listed in `docs/ibkr-historical-data.md`.

## Recent Git Context

- Key commits reviewed: N/A: repository has no commits yet.

## Worker Readiness

- Risks noticed: IBKR pacing, contract expiry, session/DST boundaries, and partial-bar handling.
- Blockers noticed: N/A for design-only scope.

