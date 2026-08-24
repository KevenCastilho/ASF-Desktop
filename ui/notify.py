"""Notificações leves do Desktop (sem credenciais)."""
from __future__ import annotations

import sys
import tkinter as tk
from typing import Any


def _enabled(settings, key: str) -> bool:
    n = settings.get("notifications") or {}
    if not isinstance(n, dict):
        return True
    return bool(n.get(key, True))


def notify(settings, kind: str, title: str, body: str = "") -> None:
    """
    kind: bot_connect | farming | card_drop | error | update | tray | input_ok
    """
    map_kind = {
        "input_ok": "bot_connect",
        "error": "error",
        "update": "update",
        "farming": "farming",
        "bot_connect": "bot_connect",
        "card_drop": "card_drop",
        "tray": "tray",
    }
    flag = map_kind.get(kind, "error")
    if not _enabled(settings, flag):
        return
    # Windows toast via powershell (best-effort)
    if sys.platform == "win32":
        try:
            import subprocess
            # mensagem simples — sem segredos
            msg = (title + (": " + body if body else ""))[:180].replace("'", " ")
            subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
                    f"Write-Output '{msg}'",
                ],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception:
            pass
    # Sempre: título da janela principal se existir
    try:
        root = tk._default_root
        if root is not None:
            root.title(f"ASF Desktop — {title}")
    except Exception:
        pass
