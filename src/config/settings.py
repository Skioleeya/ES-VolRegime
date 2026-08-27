"""Single source of truth for ES research-session boundaries."""

from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class SessionConfig:
    timezone: ZoneInfo = ZoneInfo("America/New_York")
    session_start: time = time(18, 0)
    overnight_end: time = time(4, 0)
    premarket_end: time = time(9, 30)
    session_end: time = time(12, 0)
    bar_minutes: int = 5
    minimum_history_samples: int = 20

    def __post_init__(self) -> None:
        if self.bar_minutes <= 0 or 60 % self.bar_minutes:
            raise ValueError("bar_minutes must be a positive divisor of 60")
        if self.session_start <= time(12):
            raise ValueError("session_start must be an evening time")
        if not (self.overnight_end < self.premarket_end < self.session_end):
            raise ValueError("session boundaries must be ordered")
        if self.minimum_history_samples < 1:
            raise ValueError("minimum_history_samples must be positive")

    @property
    def bar_seconds(self) -> int:
        return self.bar_minutes * 60

    @property
    def bar_size(self) -> str:
        return f"{self.bar_minutes} mins"


DEFAULT_SESSION_CONFIG = SessionConfig()
