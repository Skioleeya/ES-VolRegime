"""Single source of truth for ES research-session boundaries."""

from dataclasses import dataclass
from datetime import time
from pathlib import Path
import tomllib
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class SessionConfig:
    timezone: ZoneInfo
    session_start: time
    overnight_end: time
    premarket_end: time
    session_end: time
    bar_minutes: int
    minimum_history_samples: int
    roll_quarterly_months: tuple[int, ...]
    roll_reference_weekday: int
    roll_reference_occurrence: int
    roll_weekday: int

    def __post_init__(self) -> None:
        if self.bar_minutes <= 0 or 60 % self.bar_minutes:
            raise ValueError("bar_minutes must be a positive divisor of 60")
        if self.session_start <= time(12):
            raise ValueError("session_start must be an evening time")
        if not (self.overnight_end < self.premarket_end < self.session_end):
            raise ValueError("session boundaries must be ordered")
        if self.minimum_history_samples < 1:
            raise ValueError("minimum_history_samples must be positive")
        if not self.roll_quarterly_months or any(month < 1 or month > 12 for month in self.roll_quarterly_months):
            raise ValueError("roll_quarterly_months must contain calendar months")
        if len(set(self.roll_quarterly_months)) != len(self.roll_quarterly_months):
            raise ValueError("roll_quarterly_months must not contain duplicates")
        if not 1 <= self.roll_reference_occurrence <= 5:
            raise ValueError("roll_reference_occurrence must be between 1 and 5")

    @property
    def bar_seconds(self) -> int:
        return self.bar_minutes * 60

    @property
    def bar_size(self) -> str:
        return f"{self.bar_minutes} mins"

def load_session_config(path: Path | None = None) -> SessionConfig:
    """Load the single authoritative session configuration file."""
    config_path = path or Path(__file__).resolve().parents[2] / "config" / "session.toml"
    with config_path.open("rb") as source:
        values = tomllib.load(source)
    required = {"timezone", "session_start", "overnight_end", "premarket_end", "session_end", "bar_minutes", "minimum_history_samples", "roll_policy"}
    missing = sorted(required - values.keys())
    if missing:
        raise ValueError(f"missing session configuration keys: {', '.join(missing)}")
    roll_policy = values["roll_policy"]
    if not isinstance(roll_policy, dict):
        raise ValueError("roll_policy must be a TOML table")
    roll_required = {"quarterly_months", "reference_weekday", "reference_occurrence", "roll_weekday"}
    roll_missing = sorted(roll_required - roll_policy.keys())
    if roll_missing:
        raise ValueError(f"missing roll policy keys: {', '.join(roll_missing)}")
    return SessionConfig(
        ZoneInfo(values["timezone"]), _time(values["session_start"]), _time(values["overnight_end"]),
        _time(values["premarket_end"]), _time(values["session_end"]), int(values["bar_minutes"]),
        int(values["minimum_history_samples"]), tuple(int(month) for month in roll_policy["quarterly_months"]),
        _weekday(roll_policy["reference_weekday"]), int(roll_policy["reference_occurrence"]),
        _weekday(roll_policy["roll_weekday"]),
    )


def _time(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid session time: {value}") from exc


def _weekday(value: str) -> int:
    weekdays = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
    try:
        return weekdays[value.lower()]
    except (AttributeError, KeyError) as exc:
        raise ValueError(f"invalid weekday: {value}") from exc


DEFAULT_SESSION_CONFIG = load_session_config()
