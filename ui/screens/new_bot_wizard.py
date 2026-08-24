from __future__ import annotations

import re
import tkinter as tk

from integration.asf_config import list_bot_names, write_bot
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn
from ui.components.dialogs import themed_message
from ui.components.controls import themed_entry, ThemedCheck
from ui.mode_util import mode_banner


class NewBotWizard(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        self.step = 1
        self.name_var = tk.StringVar()
        self.login_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.start_var = tk.BooleanVar(value=True)
        c = app.colors
        self.hdr = tk.Label(self, text="Novo bot", bg=c["bg"], fg=c["fg"], font=T.FONT_TITLE)
        self.hdr.pack(anchor="w", padx=24, pady=(20, 4))
        self.steps_lbl = tk.Label(self, text="", bg=c["bg"], fg=c["dim"], font=T.FONT_TINY)
        self.steps_lbl.pack(anchor="w", padx=24)
        # progress dots
        self.dots = tk.Frame(self, bg=c["bg"])
        self.dots.pack(anchor="w", padx=24, pady=10)
        self.body = tk.Frame(self, bg=c["bg"])
        self.body.pack(fill="both", expand=True, padx=24, pady=8)
        self.footer = tk.Frame(self, bg=c["bg"])
        self.footer.pack(fill="x", padx=24, pady=16)

    def on_show(self, **kwargs) -> None:
        self.step = 1
        self._render()

    def _draw_dots(self) -> None:
        for w in self.dots.winfo_children():
            w.destroy()
        c = self.app.colors
        for i in range(1, 4):
            col = c["accent"] if i <= self.step else c["border"]
            tk.Frame(self.dots, bg=col, width=40, height=4).pack(side="left", padx=3)

    def _clear_body(self) -> None:
        for w in self.body.winfo_children():
            w.destroy()
        for w in self.footer.winfo_children():
            w.destroy()

    def _render(self) -> None:
        self._clear_body()
        self._draw_dots()
        c = self.app.colors
        self.steps_lbl.config(text=f"PASSO {self.step} DE 3")
        if self.step == 1:
            self.hdr.config(text="Novo bot")
            tk.Label(self.body, text="Como este bot vai se chamar?", bg=c["bg"], fg=c["fg"],
                     font=T.FONT_SUB).pack(anchor="w")
            e = themed_entry(self.body, c, textvariable=self.name_var)
            e.pack(fill="x", ipady=10, pady=12)
            e.focus_set()
            tk.Label(self.body, text="Apenas letras, números e underscore.",
                     bg=c["bg"], fg=c["muted"], font=T.FONT_SMALL).pack(anchor="w")
            HoverBtn(self.footer, "Continuar", color=c["accent"], fg="#0d1117",
                     command=self._next).pack(side="right")
        elif self.step == 2:
            tk.Label(self.body, text="Dados da conta Steam", bg=c["bg"], fg=c["fg"],
                     font=T.FONT_SUB).pack(anchor="w")
            tk.Label(self.body, text="Usuário Steam", bg=c["bg"], fg=c["muted"],
                     font=T.FONT_SMALL).pack(anchor="w", pady=(16, 4))
            themed_entry(self.body, c, textvariable=self.login_var).pack(fill="x", ipady=10)
            tk.Label(self.body, text="Senha", bg=c["bg"], fg=c["muted"],
                     font=T.FONT_SMALL).pack(anchor="w", pady=(12, 4))
            themed_entry(self.body, c, textvariable=self.pass_var, show="*").pack(fill="x", ipady=10)
            tk.Label(
                self.body, text="Gravado só no config do ASF. O Desktop não guarda cópia.",
                bg=c["bg"], fg=c["dim"], font=T.FONT_SMALL,
            ).pack(anchor="w", pady=12)
            HoverBtn(self.footer, "Voltar", color=c["card"], fg=c["fg"],
                     command=self._back).pack(side="left")
            HoverBtn(self.footer, "Continuar", color=c["accent"], fg="#0d1117",
                     command=self._next).pack(side="right")
        else:
            card = tk.Frame(
                self.body, bg=c["card"], highlightbackground=c["border"], highlightthickness=1,
                padx=20, pady=16,
            )
            card.pack(fill="x", pady=8)
            tk.Label(card, text="Bot criado", bg=c["card"], fg=c["accent"],
                     font=T.FONT_SUB).pack(anchor="w")
            tk.Label(card, text=self.name_var.get().strip(),
                     bg=c["card"], fg=c["fg"], font=T.FONT_TITLE).pack(anchor="w", pady=8)
            ThemedCheck(card, c, text="Iniciar o bot agora", variable=self.start_var).pack(anchor="w")
            HoverBtn(self.footer, "Ir para a Home", color=c["card"], fg=c["fg"],
                     command=lambda: self.app.show("home", push=False)).pack(side="right", padx=8)
            HoverBtn(self.footer, "Ir para o bot", color=c["accent"], fg="#0d1117",
                     command=self._finish).pack(side="right")

    def _back(self) -> None:
        if self.step > 1:
            self.step -= 1
            self._render()

    def _next(self) -> None:
        if self.step == 1:
            name = self.name_var.get().strip()
            if not re.fullmatch(r"[A-Za-z0-9_]+", name or ""):
                themed_message(self, "Novo bot", "Nome inválido.", kind="error")
                return
            path = self.app.settings.get("asf_path") or ""
            if name in list_bot_names(path):
                themed_message(self, "Novo bot", "Já existe um bot com este nome.", kind="error")
                return
            self.step = 2
            self._render()
        elif self.step == 2:
            if not self.login_var.get().strip():
                themed_message(self, "Novo bot", "Informe o usuário Steam.", kind="error")
                return
            name = self.name_var.get().strip()
            data = {
                "Enabled": True,
                "SteamLogin": self.login_var.get().strip(),
                "SteamPassword": self.pass_var.get(),
            }
            write_bot(self.app.settings.get("asf_path") or "", name, data)
            self.step = 3
            self._render()

    def _finish(self) -> None:
        name = self.name_var.get().strip()
        if self.start_var.get():
            self.app.ipc.start_bot(name)
        self.app.show("bot_details", bot_name=name, push=False)
