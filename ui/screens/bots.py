from __future__ import annotations

import threading
import tkinter as tk

from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn, FlatScrollbar
from ui.components.controls import SegmentedControl, ThemedEntry
from ui.icons.lucide import LucideIcon, icon_button, status_color
from ui.mode_util import is_advanced, mode_banner


class BotsScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        self._shown = 8

        bar = tk.Frame(self, bg=c["bg"])
        bar.pack(fill="x", padx=24, pady=(16, 8))
        self.search_var = tk.StringVar()
        self._search = ThemedEntry(bar, c, textvariable=self.search_var, placeholder="Buscar bot…")
        self._search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._search.entry.bind("<KeyRelease>", lambda e: self.refresh())
        HoverBtn(bar, "+  Novo bot", color=c["accent"], fg="#0d1117", command=self._new_bot).pack(side="right")

        filt = tk.Frame(self, bg=c["bg"])
        filt.pack(fill="x", padx=24, pady=(0, 8))
        self.filter_var = tk.StringVar(value="all")
        SegmentedControl(
            filt, c,
            [("Todos", "all"), ("Online", "online"), ("Pausado", "paused"), ("Parado", "stopped")],
            self.filter_var, command=self.refresh,
        ).pack(side="left")

        # scrollable cards
        outer = tk.Frame(self, bg=c["bg"])
        outer.pack(fill="both", expand=True, padx=16)
        self.canvas = tk.Canvas(outer, bg=c["bg"], highlightthickness=0)
        sb = FlatScrollbar(outer, command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=c["bg"])
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.load_more = W.secondary_btn(self, "Carregar mais bots", self._load_more, c)

    def _wheel(self, e) -> None:
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def on_show(self, **kwargs) -> None:
        self._shown = 12 if is_advanced(self.app) else 8
        if not getattr(self, "_banner", None):
            self._banner = mode_banner(
                self, self.app,
                simple="Visão simples — status e ações essenciais",
                advanced="Visão avançada — cards com metadados técnicos da API",
                pack_opts={"fill": "x", "padx": 24, "pady": (0, 4)},
            )
            self._banner.pack(fill="x", padx=24, pady=(0, 4), before=self.winfo_children()[1] if len(self.winfo_children())>1 else None)
        else:
            self._banner.config(
                text="Visão avançada — cards com metadados técnicos da API"
                if is_advanced(self.app)
                else "Visão simples — status e ações essenciais"
            )
        self.refresh()

    def refresh(self) -> None:
        q = self._search.get().strip().lower() if hasattr(self, "_search") else self.search_var.get().strip().lower()
        if q == "buscar bot…":
            q = ""
        f = self.filter_var.get()
        shown = self._shown

        def work():
            bots = self.app.ipc.bots_cached()
            self.after(0, lambda: self._apply(bots, q, f, shown))

        threading.Thread(target=work, daemon=True).start()

    def _apply(self, bots, q, f, shown) -> None:
        if self.app._current != "bots":
            return
        for w in self.inner.winfo_children():
            w.destroy()
        c = self.app.colors
        if q:
            bots = [b for b in bots if q in b.name.lower()]
        filtered = []
        for b in bots:
            if b.is_connected:
                st = "online"
            elif b.keep_running:
                st = "paused"
            else:
                st = "stopped"
            if f != "all" and f != st:
                continue
            filtered.append((b, st))
        row = None
        for i, (b, st) in enumerate(filtered[: shown]):
            if i % 2 == 0:
                row = tk.Frame(self.inner, bg=c["bg"])
                row.pack(fill="x", pady=4)
            self._card(row, b, st)
        if not filtered:
            tk.Label(
                self.inner, text="Nenhum bot neste filtro.", bg=c["bg"], fg=c["muted"], font=T.FONT_UI,
            ).pack(pady=30)
        if len(filtered) > shown:
            self.load_more.pack(pady=12)
        else:
            self.load_more.pack_forget()

    def _card(self, parent, bot, st: str) -> None:
        c = self.app.colors
        sub = {"online": "Online" + (" · Farming" if bot.is_farming else ""), "paused": "Pausado", "stopped": "Parado"}.get(st, st)
        fr = W.card_frame(parent, c)
        fr.pack(side="left", fill="both", expand=True, padx=8, pady=4)
        top = tk.Frame(fr, bg=c["card"])
        top.pack(fill="x")
        LucideIcon(top, "circle_dot" if st == "online" else "circle", c, size=12, color=status_color(st, c)).pack(side="left", padx=(0, 6))
        LucideIcon(top, "bot", c, size=16, color=c["fg"]).pack(side="left", padx=(0, 6))
        title = tk.Label(top, text=bot.name, bg=c["card"], fg=c["fg"], font=T.FONT_UI_BOLD)
        title.pack(side="left")
        for iname, fn in [("play", self.app.ipc.start_bot), ("pause", self.app.ipc.pause_bot), ("stop", self.app.ipc.stop_bot)]:
            icon_button(top, iname, c, command=lambda n=bot.name, f=fn: self._act(f, n), size=14, bg=c["card"], color=c["fg_secondary"]).pack(side="left", padx=1)
        icon_button(top, "more", c, command=lambda n=bot.name: self.app.show("bot_details", bot_name=n), size=14, bg=c["card"], color=c["muted"]).pack(side="right")
        sub_l = tk.Label(fr, text=sub, bg=c["card"], fg=c["muted"], font=T.FONT_SMALL)
        sub_l.pack(anchor="w", pady=(6, 0))
        if is_advanced(self.app):
            raw = bot.raw or {}
            bits = []
            sid = raw.get("s_SteamID") or raw.get("SteamID")
            if sid:
                bits.append(f"ID {sid}")
            bits.append("KeepRunning" if bot.keep_running else "Stopped")
            if bot.is_farming:
                bits.append("Farming")
            tk.Label(fr, text=" · ".join(bits), bg=c["card"], fg=c["dim"], font=T.FONT_TINY).pack(anchor="w")
        W.bind_card_hover(fr, c, [fr, top, title, sub_l])
        fr.bind("<Button-1>", lambda e, n=bot.name: self.app.show("bot_details", bot_name=n))

    
    def _act(self, fn, name: str) -> None:
        def work():
            fn(name)
            self.app.ipc.invalidate_bots_cache()
            self.after(0, self.refresh)
        threading.Thread(target=work, daemon=True).start()

    def _load_more(self) -> None:
        self._shown += 8
        self.refresh()

    def _new_bot(self) -> None:
        self.app.show("new_bot")
