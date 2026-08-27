from datetime import date
from pathlib import Path

from src.historical import QualifiedContract, build_request_plan
from src.historical.client import RawHistoricalBar
from src.historical.normalizer import normalize_completed_bar
from src.historical.repository import HistoricalRepository


CONTRACT = QualifiedContract(con_id=123, local_symbol="ESU6", contract_month="202609")


def test_repository_upserts_by_contract_and_utc_timestamp(tmp_path: Path):
    request = build_request_plan(CONTRACT, date(2026, 8, 24), date(2026, 8, 25))[0]
    raw = RawHistoricalBar(1, 1787515200, 6000, 6001, 5999, 6000, 12, 6000, 3)
    bar = normalize_completed_bar(raw, CONTRACT, request.end_utc)
    repository = HistoricalRepository(tmp_path / "history.sqlite")

    assert repository.save_bars((bar, bar)) == 2
    assert repository.count() == 1
    repository.close()


def test_repository_records_request_audit(tmp_path: Path):
    request = build_request_plan(CONTRACT, date(2026, 8, 24), date(2026, 8, 25))[0]
    repository = HistoricalRepository(tmp_path / "history.sqlite")

    repository.record_request(10001, CONTRACT.con_id, request.start_utc, request.end_utc, (), 0, "EMPTY")

    assert repository.request_count() == 1
    repository.close()


def test_repository_loads_bars_for_explicit_contract(tmp_path: Path):
    request = build_request_plan(CONTRACT, date(2026, 8, 24), date(2026, 8, 25))[0]
    raw = RawHistoricalBar(1, 1787515200, 6000, 6001, 5999, 6000, 12, 6000, 3)
    bar = normalize_completed_bar(raw, CONTRACT, request.end_utc)
    repository = HistoricalRepository(tmp_path / "history.sqlite")
    repository.save_bars((bar,))

    loaded = repository.load_bars(CONTRACT)

    assert loaded == (bar,)
    repository.close()
