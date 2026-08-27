from datetime import date

import pytest

from src.historical import QualifiedContract, build_request_plan


CONTRACT = QualifiedContract(con_id=123, local_symbol="ESU6", contract_month="202609")


def test_plan_uses_cme_sessions_and_splits_by_trading_days():
    plan = build_request_plan(CONTRACT, date(2026, 8, 24), date(2026, 9, 8), 5)

    assert [request.start_et.date() for request in plan] == [
        date(2026, 8, 23),
        date(2026, 8, 30),
        date(2026, 9, 6),
    ]
    assert plan[0].start_et.hour == 20
    assert plan[0].end_et.hour == 12
    assert plan[0].start_utc.tzinfo is not None
    assert plan[0].use_rth == 0
    assert plan[0].bar_size == "5 mins"
    assert plan[-1].end_et.date() == date(2026, 9, 7)


def test_plan_handles_dst_with_timezone_database():
    plan = build_request_plan(CONTRACT, date(2026, 10, 30), date(2026, 11, 10), 30)

    assert plan[0].start_et.tzname() == "EDT"
    assert plan[0].end_et.tzname() == "EST"
    assert plan[0].start_utc < plan[0].end_utc


def test_plan_rejects_empty_or_invalid_ranges():
    with pytest.raises(ValueError, match="start date"):
        build_request_plan(CONTRACT, date(2026, 8, 24), date(2026, 8, 24))

    with pytest.raises(ValueError, match="no CME"):
        build_request_plan(CONTRACT, date(2026, 8, 22), date(2026, 8, 24))


def test_plan_rejects_non_positive_chunk_size():
    with pytest.raises(ValueError, match="positive"):
        build_request_plan(CONTRACT, date(2026, 8, 24), date(2026, 8, 25), 0)
