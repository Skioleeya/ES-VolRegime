# Handoff: ibkr-es-mvp
CHANGE-ID: N/A:standalone MVP task
PROPOSAL-PATH: N/A:no proposal
TASKS-PATH: N/A:no tasks file
STARTUP-PROOF: Read 总纲.md and AGENTS.md before implementation.
CHANGED-PATHS: requirements.txt; .env.example; .gitignore; src/; scripts/; tests/; notes/sessions/2026-08-27/ibkr-es-mvp/
VALIDATION-SUMMARY: Dependencies installed in .venv; local tests, compile check, and live Linux-native Paper IB Gateway probe pass.
COMMAND-EVIDENCE: .venv/bin/pip install -r requirements.txt => PASS; TMPDIR=/tmp .venv/bin/pytest -q tests => PASS (3 passed); python3 -m compileall -q src scripts => PASS; 127.0.0.1:4002 socket check => PASS; .venv/bin/python scripts/verify_ibkr_es.py => PASS (connection, contract, 180 historical bars, 1 realtime tick).
ACCEPTANCE-BUNDLE: N/A:standalone MVP probe output is the acceptance evidence
ACCEPTANCE-MODE: live Paper Linux IB Gateway through 127.0.0.1:4002; Windows TWS/portproxy not used.
ACCEPTANCE-RESULT: PASS: Linux-native ES connectivity MVP accepted.
ACCEPTANCE-EVIDENCE: IBKR connection PASS; ES contract qualification PASS; Historical ES 5m data PASS (180 bars); Realtime ES market data PASS (1 tick); Order capability used NO; Fallback behavior used NO.
HARNESS-IMPROVEMENT: Added deterministic configuration test and non-trading probe entry point.
NOTES-PATHS: notes/sessions/2026-08-27/ibkr-es-mvp/
OPEN-RISKS: IB Gateway daily restart/re-authentication and VNC session persistence need operational setup before unattended cloud use.
FAST-FAIL-CHECK: Missing connection or contract-month configuration raises immediately.
NO-COMPAT-BRANCH: No alternate client or implicit contract path.
NO-ROLLBACK-PATH: N/A:no production deployment changed.
NO-PATCH-BANDAGE: No fallback patch added.
NO-FALLBACK-BEHAVIOR: Missing callbacks, ambiguous contracts, empty history, and no realtime ticks fail explicitly.
