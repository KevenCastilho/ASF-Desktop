from __future__ import annotations

import threading
import tkinter as tk

from integration.asf_config import list_bot_names, write_bot, read_bot
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn, FlatScrollbar
from ui.components.dialogs import themed_message
from ui.components.controls import themed_entry
from ui.mode_util import is_advanced, mode_banner

_BLOCKED = {"SteamLogin", "SteamPassword", "SteamParentalCode", "Name", "BotName", "s_SteamID", "SteamID", "Login", "Password"}


class MassEditorScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        self._busy = False
        c = app.colors
        W.h1(self, "Mass Editor", c).pack(anchor="w", padx=24, pady=(20, 4))
        W.caption(
            self,
            "Aplica a mesma propriedade aos bots selecionados. Nome, login e senha não em massa.",
            c,
        ).pack(anchor="w", padx=24, pady=(0, 4))
        mode_banner(
            self, app,
            simple="Visão simples — edite propriedades comuns (Enabled, etc.)",
            advanced="Visão avançada — qualquer chave do JSON (exceto bloqueadas)",
        )

        list_wrap = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        list_wrap.pack(fill="x", padx=24, pady=8)
        self.list = tk.Listbox(
            list_wrap, selectmode="extended", bg=c["card"], fg=c["fg"], relief="flat",
            height=10, font=T.FONT_UI, highlightthickness=0, activestyle="none",
            selectbackground=c["card_hover"], selectforeground=c["fg"],
        )
        sb = FlatScrollbar(list_wrap, command=self.list.yview)
        self.list.configure(yscrollcommand=sb.set)
        self.list.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        sb.pack(side="right", fill="y", pady=4)

        form = tk.Frame(self, bg=c["bg"])
        form.pack(fill="x", padx=24, pady=12)
        tk.Label(form, text="Propriedade", bg=c["bg"], fg=c["muted"], font=T.FONT_SMALL).grid(row=0, column=0, sticky="w")
        self.prop = tk.StringVar(value="Enabled")
        themed_entry(form, c, textvariable=self.prop).grid(row=1, column=0, sticky="ew", padx=(0, 12), ipady=6)
        tk.Label(form, text="Valor", bg=c["bg"], fg=c["muted"], font=T.FONT_SMALL).grid(row=0, column=1, sticky="w")
        self.val = tk.StringVar(value="true")
        themed_entry(form, c, textvariable=self.val).grid(row=1, column=1, sticky="ew", ipady=6)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        bar = tk.Frame(self, bg=c["bg"])
        bar.pack(fill="x", padx=24, pady=8)
        HoverBtn(bar, "Aplicar aos selecionados", color=c["accent"], fg="#0d1117", command=self._apply).pack(side="right")

    def on_show(self, **kwargs) -> None:
        # imediato: cache + disco local (sem esperar IPC)
        names = [b.name for b in self.app.ipc._bots_cache]
        self.list.delete(0, "end")
        for n in names:
            self.list.insert("end", n)
        if not names:
            self.list.insert("end", "  Carregando…")

        def work():
            from_ipc = [b.name for b in self.app.ipc.bots_cached()]
            from_disk = list_bot_names(self.app.settings.get("asf_path") or "")
            merged = list(dict.fromkeys(from_ipc + from_disk))
            self.after(0, lambda: self._fill(merged))

        threading.Thread(target=work, daemon=True).start()

    def _fill(self, names: list[str]) -> None:
        if self.app._current != "mass_editor":
            return
        self.list.delete(0, "end")
        for n in names:
            self.list.insert("end", n)
        if not names:
            self.list.insert("end", "  (nenhum bot)")

    def _apply(self) -> None:
        prop = self.prop.get().strip()
        if prop in _BLOCKED or prop.lower() in {x.lower() for x in _BLOCKED}:
            themed_message(self, "Mass Editor", f"'{prop}' não pode ser editado em massa.", kind="error")
            return
        sel = [self.list.get(i) for i in self.list.curselection()]
        if not sel or (len(sel) == 1 and sel[0].startswith("  (")):
            themed_message(self, "Mass Editor", "Selecione ao menos um bot.", kind="warn")
            return
        raw = self.val.get().strip()
        if raw.lower() in ("true", "false"):
            value: object = raw.lower() == "true"
        else:
            try:
                value = int(raw)
            except ValueError:
                value = raw
        path = self.app.settings.get("asf_path") or ""

        def work():
            ok_n = 0
            for name in sel:
                if name.startswith("  "):
                    continue
                data = read_bot(path, name)
                data[prop] = value
                write_bot(path, name, data)
                self.app.ipc.update_bot_config(name, {prop: value})
                ok_n += 1
            self.after(0, lambda: themed_message(self, "Mass Editor", f"Atualizado em {ok_n} bot(s)."))

        threading.Thread(target=work, daemon=True).start()
