# Handoff

CHANGE-ID: N/A:no OpenSpec change
PROPOSAL-PATH: N/A:user-approved direct implementation
TASKS-PATH: N/A:tracked in this session's open_tasks.md
STARTUP-PROOF: 2026-08-27 user approved automated ES roll without CME calendar retrieval
CHANGED-PATHS: config/session.toml; config/cme_equity_roll_dates.csv (deleted); src/config/settings.py; src/connectivity/config.py; src/historical/contract_selection.py; src/historical/__init__.py; scripts/poll_ibkr_latest.py; docs/contract-roll-policy.md; docs/cme-roll-calendar.md (deleted); docs/operations.md; .env.example; tests/historical/test_contract_selection.py; tests/test_config.py; tests/test_session_config.py; notes/
VALIDATION-SUMMARY: 97 tests passed; diff check passed; runtime references to the old CME date table and roll mode are absent; read-only IBKR chain selection passed.
COMMAND-EVIDENCE: TMPDIR=/tmp ./.venv/bin/pytest tests -q -> 97 passed; git diff --check -> clean; rg old calendar identifiers -> no runtime references; live IBKR futures-chain selection -> PASS, ESU6 conId=649180671.
ACCEPTANCE-BUNDLE: N/A:no live trading acceptance bundle
ACCEPTANCE-MODE: unit and integration-style selector tests
ACCEPTANCE-RESULT: implementation complete; live multi-day collection acceptance remains pending
ACCEPTANCE-EVIDENCE: contract-selector tests cover Sunday 18:00 cutover, June holiday-adjusted expiration, DST, invalid contract months, and unavailable next contract
HARNESS-IMPROVEMENT: added configuration and calendar-rule regression tests
NOTES-PATHS: notes/sessions/2026-08-27/calendar-rule-roll/
OPEN-RISKS: exceptional exchange policy changes are not discoverable without an external source; malformed or insufficient IBKR chains stop the poller explicitly
FAST-FAIL-CHECK: invalid chain, missing next contract, non-quarterly month, or malformed policy fails explicitly in tests
NO-COMPAT-BRANCH: no CME date-table lookup remains in contract selection
NO-ROLLBACK-PATH: N/A:normal Git rollback is available for this configuration change
NO-PATCH-BANDAGE: no expiry-minus-days heuristic
NO-FALLBACK-BEHAVIOR: malformed or insufficient IBKR contract chains fail explicitly; there is no date-table, expiry-minus-days, or volume fallback
