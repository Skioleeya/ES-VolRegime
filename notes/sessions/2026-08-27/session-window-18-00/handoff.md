# Handoff

CHANGE-ID: N/A:no OpenSpec change
PROPOSAL-PATH: docs/session-collection-18-00-plan.md
TASKS-PATH: N/A:plan phases are the task source
STARTUP-PROOF: 2026-08-27 implementation of the 18:00 ET to 12:00 ET session collection plan
CHANGED-PATHS: config/session.toml; config/cme_equity_roll_dates.csv; src/config/; src/historical/; scripts/poll_ibkr_latest.py; deploy/es-volregime-poller.service; docs/; tests/
VALIDATION-SUMMARY: 94 tests passed; official CME roll-date calendar replaces local date derivation
COMMAND-EVIDENCE: TMPDIR=/tmp ./.venv/bin/pytest tests -q -> 94 passed; git diff --check -> clean; verify_ibkr_es.py -> connection, contract, historical, and realtime PASS
ACCEPTANCE-BUNDLE: N/A:no live acceptance bundle
ACCEPTANCE-MODE: automated tests and static audit
ACCEPTANCE-RESULT: implementation complete; live acceptance pending
ACCEPTANCE-EVIDENCE: coverage/recovery end-to-end test uses temporary SQLite and a fake collector
HARNESS-IMPROVEMENT: added coverage, recovery, retry, CME calendar, and session-window tests
NOTES-PATHS: notes/sessions/2026-08-27/session-window-18-00/
OPEN-RISKS: configured Paper Gateway is required to prove live IBKR behavior across five trading days
