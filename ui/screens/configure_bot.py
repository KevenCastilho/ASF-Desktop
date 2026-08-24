from __future__ import annotations

import json
import tkinter as tk

from integration.asf_config import read_bot, write_bot
from integration.schema import bot_schema
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn, FlatScrollbar
from ui.components.controls import themed_entry, ThemedCheck
from ui.components.dialogs import themed_message, themed_confirm


class ConfigureBotScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        self.bot_name = ""
        self.vars: dict = {}
        c = app.colors
        W.h1(self, "Configurar bot", c).pack(anchor="w", padx=24, pady=(20, 4))
        self.title = tk.Label(self, text="", bg=c["bg"], fg=c["fg"], font=T.FONT_SUB, anchor="w")
        self.title.pack(fill="x", padx=24)
        self.sub = tk.Label(self, text="", bg=c["bg"], fg=c["accent"], font=T.FONT_TINY, anchor="w")
        self.sub.pack(fill="x", padx=24, pady=(0, 8))
        wrap = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=24, pady=8)
        self.canvas = tk.Canvas(wrap, bg=c["card"], highlightthickness=0)
        sb = FlatScrollbar(wrap, command=self.canvas.yview, colors=c)
        self.form = tk.Frame(self.canvas, bg=c["card"])
        self.form.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.form, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(1, width=e.width))
        bar = tk.Frame(self, bg=c["bg"])
        bar.pack(fill="x", padx=24, pady=12)
        HoverBtn(bar, "Salvar", color=c["accent"], fg="#0d1117", command=self._save).pack(side="right")
        HoverBtn(bar, "Excluir bot", color=c["stopped"], fg="#fff", command=self._delete).pack(side="left")

    def on_show(self, **kwargs) -> None:
        self.bot_name = kwargs.get("bot_name") or self.bot_name
        self.title.config(text=f"Configurar · {self.bot_name}")
        mode = self.app.settings.get("mode", "simple")
        self.sub.config(
            text=(
                "Visão avançada — schema API ou JSON completo"
                if mode == "advanced"
                else "Visão simples — campos essenciais"
            )
        )
        for w in self.form.winfo_children():
            w.destroy()
        self.vars.clear()
        data = read_bot(self.app.settings.get("asf_path") or "", self.bot_name)
        fields = bot_schema(self.app.ipc, mode, data)
        for f in fields:
            val = data.get(f.name)
            self._row(f.name, f.kind, val)

    def _row(self, key: str, typ: str, val) -> None:
        c = self.app.colors
        row = tk.Frame(self.form, bg=c["card"])
        row.pack(fill="x", pady=4, padx=12)
        tk.Label(
            row, text=key, width=24, anchor="w", bg=c["card"], fg=c["fg_secondary"], font=T.FONT_SMALL,
        ).pack(side="left")
        if typ == "bool":
            var = tk.BooleanVar(value=bool(val) if val is not None else False)
            ThemedCheck(row, c, text="", variable=var).pack(side="left")
        elif typ == "json":
            var = tk.StringVar(value="" if val is None else json.dumps(val, ensure_ascii=False))
            themed_entry(row, c, textvariable=var).pack(side="left", fill="x", expand=True, ipady=8)
        else:
            var = tk.StringVar(value="" if val is None else str(val))
            show = "*" if "assword" in key else ""
            themed_entry(row, c, textvariable=var, show=show).pack(side="left", fill="x", expand=True, ipady=8)
        self.vars[key] = (var, typ)

    def _parse(self, key: str, var, typ: str, data: dict) -> None:
        if typ == "bool":
            data[key] = bool(var.get())
            return
        s = str(var.get())
        if key == "SteamPassword" and s == "":
            return
        if typ == "json":
            try:
                data[key] = json.loads(s) if s.strip() else []
            except json.JSONDecodeError:
                data[key] = s
            return
        if typ == "int":
            try:
                data[key] = int(s)
            except ValueError:
                data[key] = s
            return
        if s.isdigit():
            data[key] = int(s)
        else:
            data[key] = s

    def _save(self) -> None:
        data = read_bot(self.app.settings.get("asf_path") or "", self.bot_name)
        for key, (var, typ) in self.vars.items():
            self._parse(key, var, typ, data)
        write_bot(self.app.settings.get("asf_path") or "", self.bot_name, data)
        self.app.ipc.update_bot_config(self.bot_name, {k: data[k] for k in self.vars if k in data})
        if themed_confirm(self, "Configurar bot", "Salvo. Reiniciar o bot agora?"):
            self.app.ipc.stop_bot(self.bot_name)
            self.app.ipc.start_bot(self.bot_name)
        self.app.go_back()

    def _delete(self) -> None:
        if not themed_confirm(
            self, "Excluir bot",
            f"Remover o bot «{self.bot_name}»?\n"
            "Tenta DELETE na IPC e apaga o JSON em config/.",
        ):
            return
        path = self.app.settings.get("asf_path") or ""
        r = self.app.ipc.delete_bot(self.bot_name)
        from integration.asf_config import delete_bot_file
        disk_ok = delete_bot_file(path, self.bot_name)
        self.app.ipc.invalidate_bots_cache()
        msg = []
        msg.append("IPC: " + ("OK" if r.ok else (r.error or "falha")))
        msg.append("Arquivo: " + ("removido" if disk_ok else "não encontrado"))
        themed_message(self, "Excluir bot", "\n".join(msg))
        self.app.show("bots", push=False)
