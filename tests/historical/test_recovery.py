from datetime import datetime, timezone

from src.historical import QualifiedContract, build_gap_requests


CONTRACT = QualifiedContract(1, "ESU6", "202609")
UTC = timezone.utc


def test_gap_requests_merge_adjacent_bars():
    missing = tuple(datetime(2026, 8, 27, 13, minute, tzinfo=UTC) for minute in (0, 5, 15))
    requests = build_gap_requests(CONTRACT, missing)
    assert len(requests) == 2
    assert requests[0].start_utc.minute == 0
    assert requests[0].end_utc.minute == 10
    assert requests[1].start_utc.minute == 15


def test_empty_gap_requires_no_requests():
    assert build_gap_requests(CONTRACT, ()) == ()
