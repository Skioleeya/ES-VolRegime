import pytest

from src.connectivity.config import IbkrConfig


def test_config_requires_connection_values(monkeypatch):
    for name in ("IBKR_HOST", "IBKR_PORT", "IBKR_CLIENT_ID"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValueError, match="IBKR_CLIENT_ID"):
        IbkrConfig.from_environment()


def test_config_reads_explicit_values(monkeypatch):
    monkeypatch.setenv("IBKR_HOST", "127.0.0.1")
    monkeypatch.setenv("IBKR_PORT", "4002")
    monkeypatch.setenv("IBKR_CLIENT_ID", "901")
    monkeypatch.setenv("ES_LAST_TRADE_DATE", "202609")
    config = IbkrConfig.from_environment()
    assert (config.host, config.port, config.client_id) == ("127.0.0.1", 4002, 901)


def test_config_rejects_contract_placeholder(monkeypatch):
    monkeypatch.setenv("IBKR_HOST", "127.0.0.1")
    monkeypatch.setenv("IBKR_PORT", "4002")
    monkeypatch.setenv("IBKR_CLIENT_ID", "901")
    monkeypatch.setenv("ES_LAST_TRADE_DATE", "REPLACE_WITH_ACTIVE_CONTRACT_MONTH")
    with pytest.raises(ValueError, match="must not contain a placeholder"):
        IbkrConfig.from_environment()


def test_config_allows_automatic_contract_selection(monkeypatch):
    monkeypatch.setenv("IBKR_HOST", "127.0.0.1")
    monkeypatch.setenv("IBKR_PORT", "4002")
    monkeypatch.setenv("IBKR_CLIENT_ID", "901")
    monkeypatch.delenv("ES_LAST_TRADE_DATE", raising=False)
    assert IbkrConfig.from_environment().last_trade_date is None


def test_config_rejects_obsolete_roll_mode(monkeypatch):
    monkeypatch.setenv("IBKR_HOST", "127.0.0.1")
    monkeypatch.setenv("IBKR_PORT", "4002")
    monkeypatch.setenv("IBKR_CLIENT_ID", "901")
    monkeypatch.setenv("ES_ROLL_MODE", "days_before_expiry")
    with pytest.raises(ValueError, match="ES_ROLL_MODE is obsolete"):
        IbkrConfig.from_environment()
