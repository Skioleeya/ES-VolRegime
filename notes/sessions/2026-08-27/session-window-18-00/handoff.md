# Handoff

CHANGE-ID: N/A:no OpenSpec change
PROPOSAL-PATH: docs/session-collection-18-00-plan.md
TASKS-PATH: N/A:plan phases are the task source
STARTUP-PROOF: 2026-08-27 implementation of the 18:00 ET to 12:00 ET session collection plan
CHANGED-PATHS: config/session.toml; src/config/; src/historical/; scripts/poll_ibkr_latest.py; deploy/es-volregime-poller.service; docs/operations.md; tests/
VALIDATION-SUMMARY: 86 tests passed; no executable 20:15 or hardcoded bar interval remains
COMMAND-EVIDENCE: TMPDIR=/tmp ./.venv/bin/pytest tests -q -> 86 passed; git diff --check -> clean; static boundary scan -> no matches; verify_ibkr_es.py -> connection, contract, historical, and realtime PASS
ACCEPTANCE-BUNDLE: N/A:no live acceptance bundle
ACCEPTANCE-MODE: automated tests and static audit
ACCEPTANCE-RESULT: implementation complete; live acceptance pending
ACCEPTANCE-EVIDENCE: coverage/recovery end-to-end test uses temporary SQLite and a fake collector
HARNESS-IMPROVEMENT: added coverage, recovery, retry, CME calendar, and session-window tests
NOTES-PATHS: notes/sessions/2026-08-27/session-window-18-00/
OPEN-RISKS: configured Paper Gateway is required to prove live IBKR behavior across five trading days
