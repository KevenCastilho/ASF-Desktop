from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog

from integration import asf_commands
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn
from ui.components.dialogs import themed_message
from ui.components.pickers import ThemedDropdown
from ui.components.controls import themed_text
from ui.mode_util import is_advanced, mode_banner
from ui.icons.lucide import icon_button


class BgrScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        W.h1(self, "BGR", c).pack(anchor="w", padx=24, pady=(20, 4))
        W.caption(self, "Background Game Redeemer — uma chave por linha.", c).pack(anchor="w", padx=24)
        mode_banner(self, app, simple="Visão simples — colar chaves e enviar", advanced="Visão avançada — controles do bot + detalhe no envio")

        row = tk.Frame(self, bg=c["bg"])
        row.pack(fill="x", padx=24, pady=12)
        tk.Label(row, text="Bot", bg=c["bg"], fg=c["muted"], font=T.FONT_SMALL).pack(side="left")
        self.bot_dd = ThemedDropdown(row, c, values=["ASF"], width=18)
        self.bot_dd.pack(side="left", padx=10)
        for name, fn in [("play", self._start), ("pause", self._pause), ("stop", self._stop)]:
            icon_button(row, name, c, command=fn, size=14, bg=c["bg"], color=c["fg"]).pack(side="left", padx=2)

        keys_wrap = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        keys_wrap.pack(fill="both", expand=True, padx=24, pady=8)
        self.keys = tk.Text(
            keys_wrap, height=12, bg=c["input"], fg=c["fg"], insertbackground=c["accent"],
            relief="flat", font=T.FONT_MONO, padx=10, pady=8,
            highlightthickness=1, highlightbackground=c["border"], highlightcolor=c["accent"],
        )
        self.keys.pack(fill="both", expand=True)

        bar = tk.Frame(self, bg=c["bg"])
        bar.pack(fill="x", padx=24, pady=12)
        HoverBtn(bar, "Importar .txt", color=c["card"], fg=c["fg"], command=self._import).pack(side="left")
        HoverBtn(bar, "Enviar chaves", color=c["accent"], fg="#0d1117", command=self._submit).pack(side="right")

    def on_show(self, **kwargs) -> None:
        names = [b.name for b in self.app.ipc._bots_cache] or ["ASF"]
        self.bot_dd.set_values(names)

        def work():
            names2 = [b.name for b in self.app.ipc.bots_cached()] or ["ASF"]
            self.after(0, lambda: self.bot_dd.set_values(names2) if self.app._current == "bgr" else None)

        threading.Thread(target=work, daemon=True).start()

    def _import(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if not path:
            return
        text = open(path, encoding="utf-8", errors="replace").read()
        self.keys.insert("end", text if text.endswith("\n") else text + "\n")

    def _submit(self) -> None:
        bot = self.bot_dd.get().strip()
        keys = [ln.strip() for ln in self.keys.get("1.0", "end").splitlines() if ln.strip() and not ln.startswith("#")]
        if not bot or not keys:
            themed_message(self, "BGR", "Informe o bot e ao menos uma chave.", kind="warn")
            return

        def work():
            r = asf_commands.redeem_keys(self.app.ipc, bot, keys)
            if r.ok:
                detail = ("\n" + str(r.data)[:800]) if is_advanced(self.app) and r.data is not None else ""
                msg = f"{len(keys)} chave(s) enviadas." + detail
            else:
                msg = r.error or "Falha"
            self.after(0, lambda: themed_message(self, "BGR", msg, kind="info" if r.ok else "error"))

        threading.Thread(target=work, daemon=True).start()

    def _act(self, fn) -> None:
        bot = self.bot_dd.get()

        def work():
            fn(bot)
            self.app.ipc.invalidate_bots_cache()

        threading.Thread(target=work, daemon=True).start()

    def _start(self) -> None:
        self._act(self.app.ipc.start_bot)

    def _pause(self) -> None:
        self._act(self.app.ipc.pause_bot)

    def _stop(self) -> None:
        self._act(self.app.ipc.stop_bot)
