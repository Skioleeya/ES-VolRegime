from datetime import datetime, timedelta, timezone

import pytest

from src.historical import QualifiedContract
from src.historical.polling import build_latest_bar_request, completed_boundary, next_poll_at

UTC = timezone.utc
CONTRACT = QualifiedContract(123, "ESU6", "202609")


def test_boundary_and_target_request_are_server_time_aligned():
    now = datetime(2026, 8, 27, 13, 42, 18, tzinfo=UTC)
    assert completed_boundary(now) == datetime(2026, 8, 27, 13, 40, tzinfo=UTC)
    request = build_latest_bar_request(CONTRACT, now)
    assert request.start_utc == datetime(2026, 8, 27, 13, 35, tzinfo=UTC)
    assert request.end_utc == datetime(2026, 8, 27, 13, 40, tzinfo=UTC)
    assert request.duration_str == "300 S"


def test_next_poll_waits_after_next_boundary():
    now = datetime(2026, 8, 27, 13, 42, 18, tzinfo=UTC)
    assert next_poll_at(now) == datetime(2026, 8, 27, 13, 45, 7, tzinfo=UTC)


def test_poll_delay_must_protect_bar_finalization():
    now = datetime(2026, 8, 27, 13, 42, 18, tzinfo=UTC)
    with pytest.raises(ValueError, match="between 5 and 10"):
        next_poll_at(now, timedelta(seconds=1))
