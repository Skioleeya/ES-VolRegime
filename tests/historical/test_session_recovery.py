from datetime import date, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from src.historical.client import RawHistoricalBar
from src.historical.collector import CollectedHistory
from src.historical.coverage import expected_bar_starts
from src.historical.models import HistoricalBar, QualifiedContract
from src.historical.repository import HistoricalRepository
from src.historical.session_recovery import recover_session


CONTRACT = QualifiedContract(1, "ESU6", "202609")
SESSION_DATE = date(2026, 8, 27)
ET = ZoneInfo("America/New_York")


class FakeCollector:
    def collect(self, request):
        raw = RawHistoricalBar(1, int(request.start_utc.timestamp()), 6000, 6001, 5999, 6000, 1, 6000, 1)
        return CollectedHistory(request, (raw,))


def test_recovery_fills_missing_bar_and_marks_coverage_complete(tmp_path):
    repository = HistoricalRepository(tmp_path / "history.sqlite")
    expected = expected_bar_starts(SESSION_DATE)
    missing = expected[10]
    repository.save_bars(tuple(_bar(start) for start in expected if start != missing))

    result = recover_session(SESSION_DATE, CONTRACT, repository, FakeCollector(), expected[-1] + timedelta(minutes=5))

    assert result.requested_bars == 1
    assert result.recovered_bars == 1
    assert result.remaining_bars == 0
    assert repository.count() == len(expected)
    assert repository._connection.execute("SELECT status FROM session_coverage").fetchone()[0] == "COMPLETE"
    repository.close()


def test_coverage_is_partitioned_by_contract(tmp_path):
    repository = HistoricalRepository(tmp_path / "history.sqlite")
    other = QualifiedContract(2, "ESZ6", "202612")
    repository.save_coverage(CONTRACT, SESSION_DATE.isoformat(), 216, 216, 0, "COMPLETE")
    repository.save_coverage(other, SESSION_DATE.isoformat(), 216, 100, 116, "DEGRADED")
    assert repository._connection.execute("SELECT COUNT(*) FROM session_coverage").fetchone()[0] == 2
    repository.close()


def _bar(start):
    return HistoricalBar(
        CONTRACT, start, start.astimezone(ET), Decimal("6000"), Decimal("6001"),
        Decimal("5999"), Decimal("6000"), Decimal("1"), Decimal("6000"), 1,
    )
