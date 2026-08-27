from pathlib import Path

import pytest

from src.config import load_session_config


def test_repository_config_is_loaded():
    config = load_session_config()
    assert config.session_start.hour == 18
    assert config.bar_minutes == 5


def test_missing_config_key_fails_explicitly(tmp_path):
    path = tmp_path / "session.toml"
    path.write_text('timezone = "America/New_York"\n')
    with pytest.raises(ValueError, match="missing session configuration keys"):
        load_session_config(path)
