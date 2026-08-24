from __future__ import annotations

import tkinter as tk

from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import FlatScrollbar
from ui.mode_util import is_advanced, mode_banner


class ActivityScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        W.h1(self, "Atividade", c).pack(anchor="w", padx=24, pady=(20, 4))
        mode_banner(
            self, app,
            simple="Visão simples — eventos recentes resumidos",
            advanced="Visão avançada — mais linhas, texto monoespaçado (stdout)",
        )
        wrap = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=24, pady=8)
        self.list = tk.Listbox(
            wrap, bg=c["card"], fg=c["fg_secondary"], relief="flat", font=T.FONT_SMALL,
            highlightthickness=0, activestyle="none",
            selectbackground=c["card_hover"], selectforeground=c["fg"],
        )
        sb = FlatScrollbar(wrap, command=self.list.yview, colors=c)
        self.list.configure(yscrollcommand=sb.set)
        self.list.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        sb.pack(side="right", fill="y", pady=4)

    def on_show(self, **kwargs) -> None:
        self.list.delete(0, "end")
        n = 400 if is_advanced(self.app) else 80
        logs = self.app.process_mgr.get_recent_logs(n)
        c = self.app.colors
        font = T.FONT_MONO if is_advanced(self.app) else T.FONT_SMALL
        self.list.configure(font=font, fg=c["fg_secondary"] if is_advanced(self.app) else c["muted"])
        if not logs:
            self.list.insert("end", "  Sem atividade recente.")
            return
        for line in logs:
            self.list.insert("end", "  " + (line if is_advanced(self.app) else line[-100:]))
