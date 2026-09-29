import pytest
from src.config import Settings
from src.errors import ConfigurationError,provider_message

@pytest.mark.parametrize("settings", [Settings(),Settings(hindsight_url="https://example.com"),
    Settings(hindsight_url="http://remote.example.com",hindsight_key="test"),
    Settings(hindsight_url="https://key@example.com",hindsight_key="test"),
    Settings(hindsight_url="http://localhost:8888",allow_unauthenticated=True,bank_id="bad/bank")])
def test_invalid_memory_configuration(settings):
    with pytest.raises(ConfigurationError):
        settings.validate_memory()


def test_missing_llm_configuration():
    with pytest.raises(ConfigurationError):
        Settings().validate_llm()


def test_local_unauthenticated_opt_in(settings):
    settings.validate_memory()


def test_auth_error_is_safe():
    class AuthError(Exception): status=401
    assert "authentication" in provider_message("Hindsight",AuthError("secret"))
    assert "secret" not in provider_message("Hindsight",AuthError("secret"))


def test_invalid_timeout(monkeypatch):
    monkeypatch.setenv('REQUEST_TIMEOUT_SECONDS','not-a-number')
    with pytest.raises(ConfigurationError, match="number"):
        Settings.from_env()
