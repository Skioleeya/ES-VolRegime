from datetime import datetime, timezone
from decimal import Decimal

from src.historical import QualifiedContract
from src.historical.models import HistoricalBar
from src.historical.report import build_quality_report, research_phase


CONTRACT = QualifiedContract(123, "ESU6", "202609")


def bar(timestamp: datetime, contract=CONTRACT) -> HistoricalBar:
    return HistoricalBar(contract, timestamp, timestamp.astimezone(timezone.utc), Decimal("1"), Decimal("2"), Decimal("1"), Decimal("2"), Decimal("1"), Decimal("1"), 1)


def test_report_counts_duplicates_contracts_phases_and_gaps():
    first = datetime(2026, 8, 25, 1, 0, tzinfo=timezone.utc)
    second = datetime(2026, 8, 25, 1, 10, tzinfo=timezone.utc)
    other = QualifiedContract(456, "ESZ6", "202612")
    report = build_quality_report((bar(first), bar(first), bar(second, other)), 123)

    assert report.status == "FAIL"
    assert report.total_bars == 3
    assert report.duplicate_timestamps == 1
    assert report.invalid_contract_bars == 1
    assert report.gaps == ((first, second),)


def test_research_phase_uses_et_boundaries():
    assert research_phase(datetime(2026, 8, 25, 0, 15, tzinfo=timezone.utc)) == "OVERNIGHT"
    assert research_phase(datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)) == "PRE-MARKET"
    assert research_phase(datetime(2026, 8, 25, 14, 30, tzinfo=timezone.utc)) == "CASH"
    assert research_phase(datetime(2026, 8, 25, 17, 0, tzinfo=timezone.utc)) is None

