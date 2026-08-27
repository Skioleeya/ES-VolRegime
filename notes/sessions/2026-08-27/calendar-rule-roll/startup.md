# Startup: calendar-rule-roll

STARTUP-PROOF: 2026-08-27 user approved automated ES roll without CME calendar retrieval.

## Session
- Scope: Replace versioned CME roll-date table selection with a configured calendar rule and IBKR contract-chain selection.

## Scope Understanding
- In scope: Unified rule configuration, deterministic lead-contract selection, explicit invalid-chain failure, tests, documentation, and validation.
- Out of scope: CME calendar scraping, alternate market-data sources, and discretionary volume-based rolling.

## Prior Context Read
- `AGENTS.md`
- `config/session.toml`
- `src/config/settings.py`
- `src/historical/contract_selection.py`
- `tests/historical/test_contract_selection.py`

## Recent Git Context
- Key commits reviewed: `895137c`, `a2a4135`, `2ea3ad3`.

## Worker Readiness
- Risks noticed: A CME exceptional rule change cannot be learned without an external source; malformed IBKR chains must fail explicitly.
- Blockers noticed: N/A:IBKR provides contract month and conId for the existing chain query.
