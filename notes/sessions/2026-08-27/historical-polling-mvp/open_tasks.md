# Open Tasks

## Active

- Run the continuous poller during a market window.
- Run continuous polling acceptance across a full market window.
- Review provisional Expansion thresholds by Phase/session/elapsed; do not treat them as validated yet.
- Add an integration test with recorded callbacks for the poller lifecycle.
- Connect persisted polled bars to session and indicator inputs.

## Closed In Session

- Added IBKR server-time calibration callback.
- Added boundary-plus-delay scheduler and one-target-bar validation.
- Added continuous/one-shot polling CLI.
- Added the detailed volatility analysis roadmap.
- Added phase-isolated Close-to-Close RV and independent range metrics.
- Added same-phase plus same-elapsed RV and range percentiles with minimum samples.
- Added Overnight compression classification and point-in-time analysis composition.
- Added explicit-contract SQLite loading and read-only analysis CLI.
- Added frozen Overnight range and Pre-market breakout, acceptance, and failed-breakout states.
- Added RV change/slope/acceleration metrics and Cash Opening Range.
- Added configurable Expansion classification with explicit unavailable behavior.
- Added top-level Regime composition with fail-closed DATA_INSUFFICIENT behavior.
- Added unified replay snapshots and CLI.
