import textwrap

import pytest

from app.api.config_loader import load_db_config


@pytest.fixture
def settings_file(tmp_path):
    content = textwrap.dedent("""
        development:
          database:
            host: "dev-host"
            database: "dev_db"
        test:
          database:
            host: "test-host"
            database: "letter_ai_test"
    """)
    path = tmp_path / "settings.yml"
    path.write_text(content)
    return path


def test_defaults_to_development_without_app_env(monkeypatch, settings_file):
    monkeypatch.delenv("APP_ENV", raising=False)
    assert load_db_config(settings_path=settings_file) == {"host": "dev-host", "database": "dev_db"}


def test_uses_app_env_test(monkeypatch, settings_file):
    monkeypatch.setenv("APP_ENV", "test")
    assert load_db_config(settings_path=settings_file) == {"host": "test-host", "database": "letter_ai_test"}


def test_explicit_app_env_argument_overrides_environment_variable(monkeypatch, settings_file):
    monkeypatch.setenv("APP_ENV", "development")
    assert load_db_config(app_env="test", settings_path=settings_file) == {
        "host": "test-host",
        "database": "letter_ai_test",
    }


def test_unknown_app_env_raises(monkeypatch, settings_file):
    monkeypatch.setenv("APP_ENV", "staging")
    with pytest.raises(KeyError):
        load_db_config(settings_path=settings_file)
