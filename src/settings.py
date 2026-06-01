import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "MurmurAI"
SETTINGS_PATH = APPDATA_DIR / "settings.json"


@dataclass
class Settings:
    hotkey: str = "ctrl+shift+space"
    language: str = "auto"
    start_on_login: bool = False
    recording_mode: str = "toggle"


def load() -> Settings:
    if not SETTINGS_PATH.exists():
        return Settings()
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        valid = {f for f in Settings.__dataclass_fields__}
        return Settings(**{k: v for k, v in data.items() if k in valid})
    except (json.JSONDecodeError, OSError, TypeError):
        return Settings()


def save(s: Settings) -> None:
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(asdict(s), indent=2), encoding="utf-8")
