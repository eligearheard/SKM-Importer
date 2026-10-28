import json
import os
from pathlib import Path


DEFAULT_UPDATE_INTERVAL_MINUTES = 5
MIN_UPDATE_INTERVAL_MINUTES = 1
MAX_UPDATE_INTERVAL_MINUTES = 1440


def _settings_path() -> Path:
    app_data = os.environ.get("APPDATA")
    base_path = Path(app_data) if app_data else Path.home() / ".config"
    return base_path / "SKM Importer" / "settings.json"


def load_update_interval() -> int:
    try:
        settings = json.loads(_settings_path().read_text(encoding="utf-8"))
        interval = int(settings["update_interval_minutes"])
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return DEFAULT_UPDATE_INTERVAL_MINUTES
    if MIN_UPDATE_INTERVAL_MINUTES <= interval <= MAX_UPDATE_INTERVAL_MINUTES:
        return interval
    return DEFAULT_UPDATE_INTERVAL_MINUTES


def save_update_interval(interval: int) -> None:
    if not MIN_UPDATE_INTERVAL_MINUTES <= interval <= MAX_UPDATE_INTERVAL_MINUTES:
        raise ValueError(
            f"Update interval must be between {MIN_UPDATE_INTERVAL_MINUTES} and {MAX_UPDATE_INTERVAL_MINUTES} minutes."
        )
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"update_interval_minutes": interval}, indent=2), encoding="utf-8")