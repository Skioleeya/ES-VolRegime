# Project State

- ACTIVE_SESSION: 2026-08-27/historical-polling-mvp
- CURRENT_STATE: Server-time polling, completed-bar persistence, phase-isolated RV/range metrics, same-key benchmarks, Overnight compression, Pre-market transitions, RV changes, Cash Opening Range, configurable Expansion classification, Cash direction gating, top-level Regime composition, unified replay CLI, and polling lifecycle integration tests are implemented.
- VALIDATION: 68 tests passed; compile and diff checks passed; boundary-aligned live poll succeeded and persisted 2026-08-27T17:35:00Z close 7749.0. Expansion stratified replay produced CASH 336, OVERNIGHT 776, PREMARKET 506 provisional expansions. Full-session continuous coverage remains pending.
- NEXT: Run the continuous poller across a complete research window, then perform final full-session replay validation.
