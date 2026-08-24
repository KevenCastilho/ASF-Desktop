from __future__ import annotations

import threading
import tkinter as tk

from integration import asf_commands
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn
from ui.components.dialogs import themed_message
from ui.components.pickers import ThemedDropdown
from ui.components.controls import themed_text
from ui.mode_util import is_advanced, mode_banner


class RedeemScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        W.h1(self, "Redeem", c).pack(anchor="w", padx=24, pady=(20, 4))
        W.caption(self, "Ativar CD-Keys no bot selecionado.", c).pack(anchor="w", padx=24)
        mode_banner(self, app, simple="Visão simples — redeem de CD-Keys", advanced="Visão avançada — resposta IPC no diálogo")

        row = tk.Frame(self, bg=c["bg"])
        row.pack(fill="x", padx=24, pady=12)
        tk.Label(row, text="Bot", bg=c["bg"], fg=c["muted"], font=T.FONT_SMALL).pack(side="left")
        self.bot_dd = ThemedDropdown(row, c, values=["ASF"], width=18)
        self.bot_dd.pack(side="left", padx=10)

        wrap = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=24, pady=8)
        self.keys = tk.Text(
            wrap, height=8, bg=c["input"], fg=c["fg"], relief="flat", font=T.FONT_MONO,
            insertbackground=c["accent"], padx=10, pady=8,
            highlightthickness=1, highlightbackground=c["border"], highlightcolor=c["accent"],
        )
        self.keys.pack(fill="both", expand=True)

        bar = tk.Frame(self, bg=c["bg"])
        bar.pack(fill="x", padx=24, pady=12)
        HoverBtn(bar, "Redeem", color=c["accent"], fg="#0d1117", command=self._go).pack(side="right")

    def on_show(self, **kwargs) -> None:
        names = [b.name for b in self.app.ipc._bots_cache] or ["ASF"]
        self.bot_dd.set_values(names)

        def work():
            names2 = [b.name for b in self.app.ipc.bots_cached()] or ["ASF"]
            self.after(0, lambda: self.bot_dd.set_values(names2) if self.app._current == "redeem" else None)

        threading.Thread(target=work, daemon=True).start()

    def _go(self) -> None:
        bot = self.bot_dd.get().strip()
        keys = [ln.strip() for ln in self.keys.get("1.0", "end").splitlines() if ln.strip()]
        if not bot or not keys:
            themed_message(self, "Redeem", "Bot e chaves são obrigatórios.", kind="warn")
            return

        def work():
            r = asf_commands.redeem_keys(self.app.ipc, bot, keys)
            msg = "Enviado." if r.ok else (r.error or "Falha")
            self.after(0, lambda: themed_message(self, "Redeem", msg, kind="info" if r.ok else "error"))

        threading.Thread(target=work, daemon=True).start()
