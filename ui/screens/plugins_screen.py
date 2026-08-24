from __future__ import annotations

import tkinter as tk

from integration.asf_config import asf_root_from_path
from ui import theme as T
from ui.components import widgets as W
from ui.icons.lucide import LucideIcon
from ui.mode_util import is_advanced, mode_banner


class PluginsScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        W.h1(self, "Plugins", c).pack(anchor="w", padx=24, pady=(20, 4))
        W.caption(
            self,
            "Carregados pelo ASF a partir de plugins/. Inclui oficiais (MobileAuthenticator, ItemsMatcher, …).\nO Desktop lista o disco; ativação é responsabilidade do ASF.",
            c,
        ).pack(anchor="w", padx=24, pady=(0, 12))

        self.wrap = tk.Frame(self, bg=c["bg"])
        self.wrap.pack(fill="both", expand=True, padx=24, pady=8)

    def on_show(self, **kwargs) -> None:
        for w in self.wrap.winfo_children():
            w.destroy()
        c = self.app.colors
        root = asf_root_from_path(self.app.settings.get("asf_path") or "")
        if not root:
            tk.Label(self.wrap, text="ASF não configurado", bg=c["bg"], fg=c["muted"], font=T.FONT_UI).pack(anchor="w")
            return
        plug = root / "plugins"
        if not plug.is_dir():
            tk.Label(self.wrap, text="Pasta plugins/ não encontrada", bg=c["bg"], fg=c["muted"], font=T.FONT_UI).pack(anchor="w")
            return
        found = False
        for d in sorted(plug.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                dlls = list(d.glob("*.dll"))
                card = tk.Frame(
                    self.wrap, bg=c["card"], highlightbackground=c["border"], highlightthickness=1,
                    padx=14, pady=10,
                )
                card.pack(fill="x", pady=4)
                color = c["online"] if dlls else c["muted"]
                rowp = tk.Frame(card, bg=c["card"])
                rowp.pack(anchor="w", fill="x")
                if dlls:
                    LucideIcon(rowp, "check", c, size=14, color=c["online"]).pack(side="left", padx=(0, 8))
                tk.Label(rowp, text=d.name, bg=c["card"], fg=c["fg"], font=T.FONT_UI_BOLD).pack(side="left")
                tk.Label(
                    card, text=f"{len(dlls)} DLL(s)" if dlls else "sem binários",
                    bg=c["card"], fg=color, font=T.FONT_SMALL,
                ).pack(anchor="w")
                if is_advanced(self.app):
                    tk.Label(card, text=str(d), bg=c["card"], fg=c["dim"], font=T.FONT_TINY).pack(anchor="w")
                    for dll in dlls[:8]:
                        tk.Label(card, text=f"  · {dll.name}", bg=c["card"], fg=c["muted"], font=T.FONT_TINY).pack(anchor="w")
                found = True
        if not found:
            tk.Label(self.wrap, text="Nenhum plugin encontrado", bg=c["bg"], fg=c["muted"]).pack(anchor="w")
