# Repository Guidelines

## Engineering Principles

- **Shame:** Guessing an interface. **Pride:** Looking it up carefully.
- **Shame:** Executing vaguely. **Pride:** Asking for confirmation.
- **Shame:** Imagining business requirements. **Pride:** Getting confirmation from the human.
- **Shame:** Inventing interfaces. **Pride:** Reusing what already exists.
- **Shame:** Skipping validation. **Pride:** Testing proactively.
- **Shame:** Breaking the architecture. **Pride:** Following established conventions.
- **Shame:** Pretending to understand. **Pride:** Being honestly uncertain.
- **Shame:** Modifying blindly. **Pride:** Refactoring cautiously.

## Architecture Constraints

- Design for high cohesion and low coupling.
- Give each module a single responsibility; keep each responsibility in one focused file.
- Do not introduce reverse dependencies. Dependencies must follow the established architectural direction.
- Do not create unnecessary coupling between modules, layers, or infrastructure components.
- Do not add fallback behavior. Fail explicitly when a required dependency, input, or invariant is unavailable.
- Avoid large, deeply nested `if` blocks. Prefer guard clauses, small functions, and explicit state transitions.
- No single source-code file may exceed 400 lines. Split a file before it reaches that limit.

## Project Structure & Module Organization

The repository currently contains the system whitepaper at `总纲.md`. It defines the ES VolRegime research scope, session boundaries, data contracts, regime states, and acceptance criteria; treat it as the governing specification.

As implementation is added, keep responsibilities separated using a structure such as:

```text
src/                 ingestion, bars, indicators, regimes, API
tests/               unit, integration, and replay tests
dashboard/           browser client and charts
config/              non-secret defaults and examples
notes/               session evidence and handoff records
```

Do not mix credentials, generated market data, or build artifacts into source directories.

## Build, Test, and Development Commands

No build system or test runner exists yet. When adding one, document the canonical commands here and in the project README. At minimum, contributors should provide commands for:

- starting the backend and dashboard locally;
- running the full test suite;
- replaying a fixed historical sample;
- linting and formatting.

Every new command must be runnable from the repository root and use reproducible configuration.

## Coding Style & Naming Conventions

Use 4-space indentation for Python and standard formatter output. Prefer `snake_case` for Python modules, functions, and variables; use `PascalCase` for classes and uppercase names for stable state constants. Keep timezone handling explicit with `America/New_York` and UTC storage. Do not hardcode UTC offsets or core research parameters; load them from configuration. Keep functions small, typed where practical, and free of look-ahead behavior.

## Testing Guidelines

Add tests beside each new subsystem under `tests/`, using names such as `test_rv_percentile.py` and `test_replay_as_of_time.py`. Test completed 5-minute bars, same-elapsed-time benchmarks, DST and cross-midnight boundaries, missing data, contract rollover, reconnect recovery, and state transitions. Replay tests must prove that future bars cannot affect earlier states. No coverage threshold is established yet; new behavior should include focused regression tests.

## Commit & Pull Request Guidelines

There is no Git history yet, so no existing commit convention can be inferred. Use short imperative subjects, for example `Add same-elapsed-time RV benchmark`, and keep each commit focused. Pull requests should explain the research or behavior impact, identify changed configuration or schema, include tests and replay evidence, and note any changes required in `总纲.md`. Never include credentials, private account data, or generated market data.

## Security & Configuration

Use a local `.env` file for IBKR credentials and keep it untracked. Default to Paper Account and read-only access. Verify IBKR API behavior against official documentation before implementation.
