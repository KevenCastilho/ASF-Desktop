from __future__ import annotations

import tkinter as tk
from pathlib import Path

from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn
from ui.components.dialogs import themed_message
from ui.icons.lucide import LucideIcon


class ToolsScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        W.h1(self, "Ferramentas", c).pack(anchor="w", padx=24, pady=(20, 4))
        W.caption(self, "Utilitários de operação e diagnóstico.", c).pack(anchor="w", padx=24, pady=(0, 4))

    def on_show(self, **kwargs) -> None:
        for w in list(self.winfo_children())[2:]:
            try:
                w.destroy()
            except Exception:
                pass
        c = self.app.colors
        mode = self.app.settings.get("mode", "simple")
        hint = tk.Label(
            self,
            text=(
                "Modo avançado — atalhos técnicos disponíveis abaixo"
                if mode == "advanced"
                else "Modo simples — mesmos atalhos; telas abrem na densidade simples"
            ),
            bg=c["bg"], fg=c["muted"], font=T.FONT_TINY, anchor="w",
        )
        hint.pack(fill="x", padx=24, pady=(0, 8))
        items = [
            ("Diagnóstico", "Processo, IPC, caminho do ASF", self._diag, "search"),
            ("Console", "Saída do processo ASF", lambda: self.app.show("console"), "terminal"),
            ("Logs / Atividade", "Linhas recentes", lambda: self.app.show("activity"), "activity"),
            ("BGR", "Background Game Redeemer", lambda: self.app.show("bgr"), "ticket"),
            ("Redeem", "Ativar CD-Keys", lambda: self.app.show("redeem"), "key"),
            ("Mass Editor", "Editar vários bots", lambda: self.app.show("mass_editor"), "pencil"),
            ("Inventário", "Coletas e inventário", lambda: self.app.show("inventory"), "package"),
            ("Importar / Exportar", "Backup de configs", lambda: self.app.show("import_export"), "inbox"),
            ("Plugins", "Plugins na pasta do ASF", lambda: self.app.show("plugins"), "puzzle"),
            ("Logs e diagnósticos", "Exportar logs / crashes", lambda: self.app.show("logs"), "file"),
            ("Update Desktop", "Release do ASF Desktop no GitHub", lambda: self.app.show("desktop_update"), "refresh"),
            ("Atualizar ASF", "Update oficial via IPC", self._update_asf, "download"),
        ]
        for title, desc, cmd, icon in items:
            fr = tk.Frame(
                self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1,
                padx=16, pady=12,
            )
            fr.pack(fill="x", padx=24, pady=4)
            LucideIcon(fr, icon, c, size=18, color=c["fg_secondary"]).pack(side="left", padx=(0, 12))
            left = tk.Frame(fr, bg=c["card"])
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text=title, bg=c["card"], fg=c["fg"], font=T.FONT_UI_BOLD).pack(anchor="w")
            tk.Label(left, text=desc, bg=c["card"], fg=c["muted"], font=T.FONT_SMALL).pack(anchor="w", pady=(2, 0))
            HoverBtn(fr, "Abrir", color=c["bg"], fg=c["fg"], command=cmd, padx=12, pady=5).pack(side="right")

    def _diag(self) -> None:
        ok, msg = self.app.process_mgr.validate_install()
        running = self.app.process_mgr.is_running()
        pid = ""
        try:
            if self.app.process_mgr.proc and self.app.process_mgr.proc.poll() is None:
                pid = str(self.app.process_mgr.proc.pid)
        except Exception:
            pass
        ipc = self.app.ipc.get_asf()
        bots = self.app.ipc.bots_cached()
        if not bots and running:
            bots = self.app.ipc.parse_bots(self.app.ipc.get_bots("ASF"))
        path = self.app.settings.get("asf_path") or "(não definido)"
        text = (
            f"Instalação: {'OK' if ok else 'FALHA'}\n{msg}\n\n"
            f"Caminho: {path}\n"
            f"Processo: {'Running' if running else 'Stopped'}"
            + (f"  PID {pid}" if pid else "") + "\n"
            f"IPC: {'OK' if ipc.ok else 'FALHA'}\n"
            f"Erro IPC: {self.app.ipc.last_error or '—'}\n"
            f"URL: {self.app.ipc.base_url}\n"
            f"Bots visíveis: {len(bots)}\n"
            f"Modo UI: {self.app.settings.get('mode', 'simple')}\n"
        )
        themed_message(self, "Diagnóstico", text)

    def _update_asf(self) -> None:
        if not self.app.process_mgr.is_running():
            themed_message(self, "Update ASF", "Inicie o ASF antes de solicitar update.", kind="error")
            return
        r = self.app.ipc.update_asf()
        themed_message(
            self, "Update ASF",
            "Solicitado ao ASF. Acompanhe o Console; o processo pode reiniciar."
            if r.ok else (r.error or "Falha"),
        )
