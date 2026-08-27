from datetime import datetime, timezone

from src.historical.gap_classifier import GapCategory, classify_gaps


def test_gap_classifier_identifies_weekend_gap():
    gaps = ((datetime(2026, 8, 28, 21, 0, tzinfo=timezone.utc), datetime(2026, 8, 31, 22, 0, tzinfo=timezone.utc)),)

    result = classify_gaps(gaps)

    assert result[0].category == GapCategory.WEEKEND_OR_HOLIDAY


def test_gap_classifier_does_not_hide_unknown_gap():
    gaps = ((datetime(2026, 8, 25, 14, 0, tzinfo=timezone.utc), datetime(2026, 8, 25, 14, 20, tzinfo=timezone.utc)),)

    result = classify_gaps(gaps)

    assert result[0].category in {GapCategory.UNCLASSIFIED, GapCategory.OUTSIDE_RESEARCH_WINDOW}

