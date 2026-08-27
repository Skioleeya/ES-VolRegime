from pathlib import Path

import pytest

from src.config import load_session_config


def test_repository_config_is_loaded():
    config = load_session_config()
    assert config.session_start.hour == 18
    assert config.bar_minutes == 5
    assert config.roll_quarterly_months == (3, 6, 9, 12)
    assert config.roll_reference_occurrence == 3


def test_missing_config_key_fails_explicitly(tmp_path):
    path = tmp_path / "session.toml"
    path.write_text('timezone = "America/New_York"\n')
    with pytest.raises(ValueError, match="missing session configuration keys"):
        load_session_config(path)


def test_roll_policy_must_be_a_toml_table(tmp_path):
    path = tmp_path / "session.toml"
    path.write_text(
        'timezone = "America/New_York"\n'
        'session_start = "18:00"\n'
        'overnight_end = "04:00"\n'
        'premarket_end = "09:30"\n'
        'session_end = "12:00"\n'
        'bar_minutes = 5\n'
        'minimum_history_samples = 20\n'
        'roll_policy = "third_friday"\n'
    )
    with pytest.raises(ValueError, match="roll_policy must be a TOML table"):
        load_session_config(path)
