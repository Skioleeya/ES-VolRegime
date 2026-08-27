from datetime import date, datetime, timezone
from decimal import Decimal

from src.historical.models import HistoricalBar, QualifiedContract
from src.volatility.engine import _compression
from src.volatility.models import BenchmarkResult, PhaseMetric, ResearchPhase

UTC = timezone.utc


def test_compression_confirmation_resets_after_a_missing_bar():
    contract = QualifiedContract(1, "ESU6", "202609")
    metrics = tuple(
        PhaseMetric(ResearchPhase.OVERNIGHT, date(2026, 8, 27), elapsed, datetime(2026, 8, 27, tzinfo=UTC), Decimal("0"), Decimal("1"), Decimal("1"), Decimal("1"))
        for elapsed in (0, 5, 15)
    )
    benchmarks = {
        metric.bar_start_utc: BenchmarkResult(ResearchPhase.OVERNIGHT, metric.elapsed_minutes, Decimal("10"), Decimal("20"), 20)
        for metric in metrics
    }
    states = _compression(metrics, benchmarks)
    assert states[metrics[-1].bar_start_utc].value == "NORMAL"
