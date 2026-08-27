# Startup: session-window-18-00

STARTUP-PROOF: 2026-08-27 implementation of the 18:00 ET to 12:00 ET session collection plan

## Session
- Scope: Implement the configured session window, coverage, recovery, and deployment handoff.

## Scope Understanding
- In scope: Time configuration, CME session selection, completed-bar persistence, coverage, recovery, retries, and service template.
- Out of scope: Live IBKR Gateway deployment and multi-day live acceptance.

## Prior Context Read
- `AGENTS.md`
- `总纲.md`
- `docs/session-collection-18-00-plan.md`

## Recent Git Context
- Key commits reviewed: `fedfb56`, `f1f3b9a`

## Worker Readiness
- Risks noticed: Existing local coverage tables lack contract identity and must fail explicitly.
- Blockers noticed: Live Gateway validation needs a configured Paper Gateway.
