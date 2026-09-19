import os
from pathlib import Path

import yaml

_DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "settings.yml"


def load_db_config(app_env: str | None = None, settings_path=None) -> dict:
    """
    Loads the database section for the active environment from config/settings.yml.

    Environment is `app_env` if given, else the APP_ENV env var, else "development" —
    matching the default in app/core/config.py. `settings_path` overrides the file
    location (used by tests); production callers rely on the default, which is
    resolved relative to this file instead of the process working directory.
    """
    resolved_env = app_env or os.environ.get("APP_ENV", "development")
    path = Path(settings_path) if settings_path else _DEFAULT_SETTINGS_PATH

    with open(path, "r") as f:
        config = yaml.safe_load(f) or {}

    if resolved_env not in config:
        raise KeyError(f"No configuration section for APP_ENV={resolved_env!r} in {path}")

    return config[resolved_env]["database"]
