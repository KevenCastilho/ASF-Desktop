from __future__ import annotations

import tkinter as tk

from integration.asf_config import read_global, write_global
from integration.schema import asf_schema
import json
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn
from ui.components.dialogs import themed_message
from ui.components.controls import themed_entry, ThemedCheck

_SIMPLE_KEYS = [
    ("IPC", "bool", True),
    ("IPCPassword", "str", ""),
    ("AutoRestart", "bool", True),
    ("UpdatePeriod", "int", 24),
    ("Headless", "bool", False),
    ("SteamOwnerID", "str", "0"),
]


class AsfGlobalConfigScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        self.vars: dict[str, tk.Variable] = {}
        c = app.colors
        W.h1(self, "Configuração global ASF", c).pack(anchor="w", padx=24, pady=(20, 4))
        W.caption(
            self, "Edita ASF.json no padrão do ASF. Simple mostra o essencial.", c,
        ).pack(anchor="w", padx=24, pady=(0, 12))

        wrap = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=24, pady=8)
        self.form = tk.Frame(wrap, bg=c["card"])
        self.form.pack(fill="both", expand=True, padx=16, pady=12)

        HoverBtn(
            self, "Salvar ASF.json", color=c["accent"], fg="#0d1117", command=self._save,
        ).pack(anchor="e", padx=24, pady=16)

    def on_show(self, **kwargs) -> None:
        for w in self.form.winfo_children():
            w.destroy()
        self.vars.clear()
        data = read_global(self.app.settings.get("asf_path") or "")
        mode = self.app.settings.get("mode", "simple")
        c = self.app.colors
        try:
            self.mode_hint.config(text="Visão avançada — ASF.json completo" if mode == "advanced" else "Visão simples — chaves principais do ASF.json")
        except Exception:
            pass
        fields = asf_schema(self.app.ipc, mode, data)
        if not fields and not data:
            tk.Label(
                self.form, text="(ASF.json ausente — campos simples padrão)",
                bg=c["card"], fg=c["muted"], font=T.FONT_SMALL,
            ).pack(anchor="w")
        for f in fields:
            val = data.get(f.name)
            if val is None and mode == "simple":
                for k, typ, default in _SIMPLE_KEYS:
                    if k == f.name:
                        val = default
                        break
            self._row(f.name, f.kind, val)

    def _row(self, key: str, typ: str, val) -> None:
        c = self.app.colors
        row = tk.Frame(self.form, bg=c["card"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text=key, width=20, anchor="w", bg=c["card"], fg=c["fg_secondary"],
                 font=T.FONT_SMALL).pack(side="left")
        if typ == "bool":
            var = tk.BooleanVar(value=bool(val) if val is not None else False)
            ThemedCheck(row, c, text="", variable=var).pack(side="left")
        else:
            var = tk.StringVar(value="" if val is None else str(val))
            show = "*" if "assword" in key else ""
            themed_entry(row, c, textvariable=var, show=show).pack(side="left", fill="x", expand=True, ipady=8)
        self.vars[key] = var

    def _save(self) -> None:
        data = read_global(self.app.settings.get("asf_path") or "")
        for key, var in self.vars.items():
            val = var.get()
            if isinstance(var, tk.BooleanVar):
                data[key] = bool(val)
            else:
                s = str(val)
                if s.isdigit():
                    data[key] = int(s)
                elif s.lower() in ("true", "false"):
                    data[key] = s.lower() == "true"
                else:
                    data[key] = s
        write_global(self.app.settings.get("asf_path") or "", data)
        if data.get("IPCPassword"):
            self.app.settings.set("ipc_password", str(data["IPCPassword"]))
            self.app.settings.save()
        themed_message(self, "ASF.json", "Salvo. Reinicie o ASF se necessário.")
