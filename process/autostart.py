"""Iniciar com o sistema — Windows (HKCU Run) e Linux (.desktop)."""
from __future__ import annotations

import os
import sys
from pathlib import Path


APP_RUN_VALUE = "ASFDesktop"


def _launch_command() -> str:
    # Preferir main.py do diretório atual do projeto
    main = Path(sys.argv[0]).resolve() if sys.argv else Path("main.py").resolve()
    py = sys.executable
    return f'"{py}" "{main}"'


def set_start_with_system(enabled: bool) -> tuple[bool, str]:
    if os.name == "nt":
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as k:
                if enabled:
                    winreg.SetValueEx(k, APP_RUN_VALUE, 0, winreg.REG_SZ, _launch_command())
                else:
                    try:
                        winreg.DeleteValue(k, APP_RUN_VALUE)
                    except FileNotFoundError:
                        pass
            return True, "OK"
        except Exception as e:
            return False, str(e)
    # Linux XDG autostart
    try:
        autostart = Path.home() / ".config" / "autostart"
        autostart.mkdir(parents=True, exist_ok=True)
        desk = autostart / "asf-desktop.desktop"
        if enabled:
            desk.write_text(
                "\n".join(
                    [
                        "[Desktop Entry]",
                        "Type=Application",
                        "Name=ASF Desktop",
                        f"Exec={_launch_command()}",
                        "X-GNOME-Autostart-enabled=true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
        elif desk.is_file():
            desk.unlink()
        return True, "OK"
    except Exception as e:
        return False, str(e)


def is_enabled() -> bool:
    if os.name == "nt":
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as k:
                winreg.QueryValueEx(k, APP_RUN_VALUE)
                return True
        except Exception:
            return False
    desk = Path.home() / ".config" / "autostart" / "asf-desktop.desktop"
    return desk.is_file()
