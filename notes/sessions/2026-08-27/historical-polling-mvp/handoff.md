# Handoff: historical-polling-mvp

CHANGE-ID: N/A:standalone MVP implementation
PROPOSAL-PATH: N/A:no OpenSpec proposal
TASKS-PATH: N/A:no OpenSpec tasks file
STARTUP-PROOF: Read AGENTS.md, prior historical session records, source modules, and official IBKR documentation.
CHANGED-PATHS: src/historical/client.py; src/historical/polling.py; src/historical/__init__.py; scripts/poll_ibkr_latest.py; tests/historical/test_polling.py; docs/historical-module-design.md; notes/sessions/2026-08-27/historical-polling-mvp/
VALIDATION-SUMMARY: PASS: 68 tests, Python compile, git diff, live one-shot, persisted-data analysis, as-of Expansion replay, unified regime replay, polling lifecycle integration, compression continuity, real prefix invariance, incomplete-bar gate, boundary-aligned live poll, and stratified Expansion replay checks. Full-session continuous coverage remains pending.
COMMAND-EVIDENCE: `.venv/bin/python -u scripts/poll_ibkr_latest.py --max-polls 1 --timeout-seconds 30` => PASS, bar 2026-08-27T17:35:00Z close 7749.0; database row con_id 649180671, local_symbol ESU6, contract_month 202609, is_complete 1. Expansion replay => CASH 336, OVERNIGHT 776, PREMARKET 506 provisional expansions.
COMMAND-EVIDENCE: Real database prefix validation at 2026-08-20T16:00:00Z => PASS, checked_snapshots 14175.
COMMAND-EVIDENCE: `TMPDIR=/tmp .venv/bin/pytest -q tests` => 45 passed; `python3 -m compileall -q src scripts tests` => PASS; `git diff --check` => PASS; `.venv/bin/python scripts/poll_ibkr_latest.py --once --timeout-seconds 30` => PASS, bar 2026-08-27T13:05:00Z close 7711.75; `.venv/bin/python scripts/analyze_latest.py --con-id 649180671 --local-symbol ESU6 --contract-month 202609` => PASS, PREMARKET RV percentile 43.04, Range percentile 36.71, samples 79.
ACCEPTANCE-BUNDLE: N/A:standalone MVP acceptance recorded in this handoff.
ACCEPTANCE-MODE: offline unit validation plus live Paper Gateway one-shot.
ACCEPTANCE-RESULT: PASS: server-time calibration, boundary selection, one-bar historical request, normalization, SQLite persistence, phase-isolated RV metrics, same-key benchmark rules, Overnight compression thresholds, Pre-market range transitions, RV change metrics, Cash Opening Range, configurable Expansion classification, Cash direction gating, analysis composition, and read-only CLI validated.
ACCEPTANCE-EVIDENCE: Live Gateway returned and persisted one completed ES 5-minute bar; database verification returned the expected contract identity and completed flag. Real database analysis returned PREMARKET elapsed 305 with RV percentile 43.04, Range percentile 36.71, and 79 matching historical samples. Unit tests prove frozen range, acceptance, failed breakout, RV reset, and exact three-bar Cash opening range.
HARNESS-IMPROVEMENT: Added deterministic polling boundary tests.
NOTES-PATHS: notes/sessions/2026-08-27/historical-polling-mvp/
OPEN-RISKS: Full-session continuous polling and final full-session replay remain open; Expansion thresholds remain provisional and require research review.
FAST-FAIL-CHECK: Missing server time, target bar, or completed-bar invariant raises an explicit error.
NO-COMPAT-BRANCH: No alternate clock or data path.
NO-ROLLBACK-PATH: N/A:no production deployment.
NO-PATCH-BANDAGE: No workaround for unavailable data was added.
NO-FALLBACK-BEHAVIOR: No local clock fallback, tick fallback, or automatic retry.
