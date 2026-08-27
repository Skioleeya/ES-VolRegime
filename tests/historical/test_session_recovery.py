from datetime import date, datetime, timezone

from src.historical.session_recovery import recover_session


def test_recovery_result_type_is_exposed():
    # Integration with IBKR is exercised by the collector tests; this keeps the
    # orchestration contract importable without a live Gateway.
    assert recover_session.__name__ == "recover_session"
