import pytest

from src.historical.retry import retry_operation


def test_retry_succeeds_after_transient_failures():
    calls = []

    def operation():
        calls.append(1)
        if len(calls) < 3:
            raise TimeoutError("temporary")
        return "ok"

    assert retry_operation(operation, attempts=3, delay_seconds=0) == "ok"
    assert len(calls) == 3


def test_retry_reraises_after_final_attempt():
    with pytest.raises(TimeoutError):
        retry_operation(lambda: (_ for _ in ()).throw(TimeoutError("failed")), attempts=2, delay_seconds=0)
