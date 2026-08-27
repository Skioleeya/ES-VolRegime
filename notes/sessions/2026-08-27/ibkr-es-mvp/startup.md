# Startup: ibkr-es-mvp
STARTUP-PROOF: Read 总纲.md and AGENTS.md before implementing the IBKR ES MVP.

## Session
- Date: 2026-08-27
- Task: Build a non-trading Linux IBKR connectivity and ES market-data MVP.

## Scope Understanding
- In scope: explicit configuration, connection callback, one ES contract, historical 5-minute bars, realtime market-data probe.
- Out of scope: orders, trading, automatic reconnect, fallback behavior, indicators, database, dashboard.

## Prior Context Read
- 总纲.md sections 7-12, 45-50, 52-58, 65-68.
- AGENTS.md engineering and architecture constraints.

## Recent Git Context
- N/A: repository has no commits yet.

## Worker Readiness
- Risks noticed: IB Gateway/TWS and market-data entitlements are external prerequisites.
- Blockers noticed: ibapi is not installed and no live IBKR endpoint is currently verified.
