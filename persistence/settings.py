"""Desktop preferences only — never Steam secrets."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def default_config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "ASFDesktop"
    return Path.home() / ".config" / "ASFDesktop"


def default_asf_download_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "ASFDesktop" / "ASF"
    return Path.home() / ".local" / "share" / "ASFDesktop" / "ASF"


class SettingsStore:
    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or default_config_dir()
        self.path = self.config_dir / "settings.json"
        self.data: dict[str, Any] = {}

    def load(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if self.path.is_file():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self.data = {}
        self._apply_defaults()

    def _apply_defaults(self) -> None:
        d = self.data
        d.setdefault("theme", "system")  # light | dark | system
        d.setdefault("language", "pt-BR")
        d.setdefault("close_behavior", "tray")  # tray | exit
        d.setdefault("start_with_system", False)
        d.setdefault("remember_geometry", True)
        d.setdefault("geometry", "1100x700")
        d.setdefault("mode", "simple")  # simple | advanced
        d.setdefault("asf_path", "")  # path to ArchiSteamFarm.exe or binary
        d.setdefault("asf_download_dir", str(default_asf_download_dir()))
        d.setdefault("ipc_host", "127.0.0.1")
        d.setdefault("ipc_port", 1242)
        d.setdefault("ipc_password", "")  # only if user set; prefer reading ASF config
        d.setdefault(
            "notifications",
            {
                "bot_connect": True,
                "farming": True,
                "card_drop": True,
                "error": True,
                "update": True,
                "tray": True,
            },
        )
        d.setdefault("activity_retention", 500)

    def save(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
