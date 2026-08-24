from __future__ import annotations

import tkinter as tk

from ui.components.console_widget import ConsoleWidget
from ui.mode_util import is_advanced, mode_banner


class ConsoleScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        mode_banner(
            self, app,
            simple="Visão simples — foco em INFO / WARN / ERROR (DEBUG oculto por padrão se o widget permitir)",
            advanced="Visão avançada — buffer maior e densidade técnica completa do stdout",
        )
        self.console = ConsoleWidget(
            self, app.colors, on_command=self._cmd,
        )
        self.console.pack(fill="both", expand=True, padx=12, pady=12)
        app.process_mgr.add_log_listener(self._on_line)

    def on_show(self, **kwargs) -> None:
        n = 800 if is_advanced(self.app) else 150
        self.console.load_lines(self.app.process_mgr.get_recent_logs(n))
        # tentativa de filtrar DEBUG/TRACE no simples se o widget tiver API
        if hasattr(self.console, "set_level_enabled"):
            adv = is_advanced(self.app)
            for lv in ("DEBUG", "TRACE"):
                try:
                    self.console.set_level_enabled(lv, adv)
                except Exception:
                    pass

    def _on_line(self, line: str) -> None:
        if getattr(self.app, "_current", None) != "console":
            return
        lv = "INFO"
        up = line.upper()
        for cand in ("FATAL", "ERROR", "WARN", "WARNING", "DEBUG", "TRACE", "INFO"):
            if f"|{cand}|" in up:
                lv = "WARN" if cand == "WARNING" else cand
                break
        if not is_advanced(self.app) and lv in ("DEBUG", "TRACE"):
            return
        try:
            self.after(0, lambda l=line, v=lv: self.console.append_line(l, v))
        except Exception:
            pass

    def _cmd(self, cmd: str) -> None:
        r = self.app.ipc.command(cmd)
        msg = "OK" if r.ok else (r.error or "falha")
        self.console.append_line(f"→ {msg}", "INFO", "Desktop")
