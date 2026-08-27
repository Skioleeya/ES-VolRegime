# Handoff: historical-module-design

CHANGE-ID: N/A:standalone documentation and design task
PROPOSAL-PATH: N/A:no OpenSpec proposal
TASKS-PATH: N/A:no OpenSpec tasks file
STARTUP-PROOF: Read AGENTS.md, prior MVP handoff, source connectivity modules, and official IBKR documentation.
CHANGED-PATHS: .gitignore; requirements.txt; src/historical/; scripts/backfill_ibkr_history.py; tests/historical/; docs/ibkr-historical-data.md; docs/historical-module-design.md; notes/sessions/2026-08-27/historical-module-design/
VALIDATION-SUMMARY: PASS: dependency installation, git diff check, Python compile check, full test suite, Linux Gateway live MVP, 60-trading-day backfill, request audit, gap classification, and as-of replay completed.
COMMAND-EVIDENCE: .venv/bin/pip3 install 'pandas_market_calendars>=5.4,<6' => PASS (5.4.0); git diff --check => PASS; python3 -m compileall -q src tests => PASS; TMPDIR=/tmp .venv/bin/pytest -q tests => PASS (27 passed); 2-day live backfill => PASS (492 returned, 492 persisted); 60-trading-day backfill => PASS (25,803 returned, 21,831 unique persisted, quality PASS, 79 observable gaps, 3 request audit rows); SQLite gap audit => PASS (16 WEEKEND_OR_HOLIDAY, 63 OUTSIDE_RESEARCH_WINDOW, 0 contract mismatch); SQLite as-of replay => PASS (last in-progress bar excluded).
ACCEPTANCE-BUNDLE: N/A:design-only task.
ACCEPTANCE-MODE: N/A:no live behavior changed.
ACCEPTANCE-RESULT: PASS: historical planning, pacing, callback collection, normalization, SQLite persistence, quality reporting, request audit, gap classification, as-of replay, and 60-trading-day Linux backfill validated.
ACCEPTANCE-EVIDENCE: Linux Paper Gateway returned 25,803 ES 5-minute TRADES bars across three bounded requests; SQLite primary-key upsert persisted 21,831 unique rows and historical_requests contains 3 PASS rows; gap classification found 16 weekend/holiday and 63 outside-research-window gaps; as-of replay excluded the final in-progress bar; no order capability was used.
HARNESS-IMPROVEMENT: Added quality reporting, session-phase coverage, gap visibility, and replay-oriented acceptance tests.
NOTES-PATHS: notes/sessions/2026-08-27/historical-module-design/
OPEN-RISKS: Session-level acceptance of classified gaps and integration of indicator inputs remain open; raw 60-day backfill, batch audit, and replay MVP are complete.
FAST-FAIL-CHECK: Design requires explicit contract qualification and explicit error handling.
NO-COMPAT-BRANCH: No alternate API or implicit contract path designed.
NO-ROLLBACK-PATH: N/A:no production changes.
NO-PATCH-BANDAGE: No implementation patch added.
NO-FALLBACK-BEHAVIOR: Design specifies explicit failure for missing, malformed, ambiguous, or paced requests.
