from __future__ import annotations

import threading
import tkinter as tk

from ui import theme as T
from ui.components import widgets as W
from ui.components.dialogs import themed_message
from ui.icons.lucide import LucideIcon, icon_button, status_color


class HomeScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        self._busy = False
        c = app.colors

        head = tk.Frame(self, bg=c["bg"])
        head.pack(fill="x", padx=24, pady=(20, 8))
        self.lbl_account = tk.Label(
            head, text="ASF Desktop", bg=c["bg"], fg=c["fg"], font=T.FONT_TITLE,
        )
        self.lbl_account.pack(side="left")
        self.lbl_mode_hint = tk.Label(head, text="", bg=c["bg"], fg=c["muted"], font=T.FONT_TINY)
        self.lbl_mode_hint.pack(side="left", padx=12)

        actions = tk.Frame(head, bg=c["bg"])
        actions.pack(side="right")
        for name, cmd in [("play", self._start), ("pause", self._pause), ("stop", self._stop)]:
            icon_button(actions, name, c, command=cmd, size=16, bg=c["bg"], color=c["fg"]).pack(side="left", padx=3)

        self.lbl_metrics = tk.Label(
            self, text="", bg=c["bg"], fg=c["muted"], font=T.FONT_SMALL, anchor="w",
        )
        self.lbl_metrics.pack(fill="x", padx=24, pady=(4, 2))

        self.lbl_ipc = tk.Label(
            self, text="", bg=c["bg"], fg=c["dim"], font=T.FONT_TINY, anchor="w",
        )
        self.lbl_ipc.pack(fill="x", padx=24)

        row = tk.Frame(self, bg=c["bg"])
        row.pack(fill="x", padx=24, pady=(8, 4))
        self.lbl_counts = tk.Label(
            row, text="Bots | —", bg=c["bg"], fg=c["fg_secondary"], font=T.FONT_UI, anchor="w",
        )
        self.lbl_counts.pack(side="left")
        tk.Button(
            row, text="Ver todos  →", command=lambda: app.show("bots"),
            bg=c["bg"], fg=c["accent"], activebackground=c["bg"],
            activeforeground=c["accent_dim"], relief="flat", cursor="hand2",
            font=T.FONT_SMALL, bd=0,
        ).pack(side="right")

        self.cards = tk.Frame(self, bg=c["bg"])
        self.cards.pack(fill="both", expand=True, padx=16, pady=8)

        feed_hdr = tk.Frame(self, bg=c["bg"])
        feed_hdr.pack(fill="x", padx=24, pady=(4, 0))
        tk.Label(
            feed_hdr, text="Atividade recente", bg=c["bg"], fg=c["dim"], font=T.FONT_TINY,
        ).pack(anchor="w")
        self.feed = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        self.feed.pack(fill="x", padx=24, pady=(4, 16))
        self.feed_inner = tk.Frame(self.feed, bg=c["card"])
        self.feed_inner.pack(fill="x", padx=10, pady=8)

    def on_show(self, **kwargs) -> None:
        self.refresh()

    def refresh(self) -> None:
        if self._busy:
            return
        self._busy = True

        def work():
            bots = self.app.ipc.bots_cached()
            metrics = ""
            try:
                import psutil
                proc = self.app.process_mgr.proc
                if proc and proc.poll() is None:
                    p = psutil.Process(proc.pid)
                    cpu = p.cpu_percent(interval=0.05)
                    mem = p.memory_info().rss / (1024 * 1024)
                    metrics = f"CPU {cpu:.0f}%   ·   RAM {mem:.0f} MB   ·   PID {proc.pid}"
            except Exception:
                metrics = "Métricas indisponíveis"
            logs = self.app.process_mgr.get_recent_logs(12)
            self.after(0, lambda: self._apply(bots, metrics, logs))

        threading.Thread(target=work, daemon=True).start()

    def _apply(self, bots, metrics: str, logs: list) -> None:
        self._busy = False
        if self.app._current != "home":
            return
        c = self.app.colors
        mode = (self.app.settings.get("mode") or "simple").strip().lower()
        advanced = mode == "advanced"

        self.lbl_mode_hint.config(
            text="Visão avançada — métricas e detalhes técnicos"
            if advanced
            else "Visão simples — essencial operacional"
        )

        for w in self.cards.winfo_children():
            w.destroy()
        for w in self.feed_inner.winfo_children():
            w.destroy()

        online = sum(1 for b in bots if b.is_connected)
        paused = sum(1 for b in bots if not b.is_connected and b.keep_running)
        stopped = len(bots) - online - paused
        self.lbl_counts.config(
            text=f"Bots | Online {online}   Pausado {paused}   Parado {stopped}"
        )

        if advanced:
            self.lbl_metrics.config(text=metrics or "—")
            self.lbl_ipc.config(text=f"IPC {self.app.ipc.base_url}   ·   processo {'ativo' if self.app.process_mgr.is_running() else 'parado'}")
            self.lbl_metrics.pack(fill="x", padx=24, pady=(4, 2))
            self.lbl_ipc.pack(fill="x", padx=24)
        else:
            self.lbl_metrics.pack_forget()
            self.lbl_ipc.pack_forget()

        # Relevância: farming > online > keep_running > nome
        def _score(b):
            s = 0
            if b.is_farming:
                s += 100
            if b.is_connected:
                s += 50
            if b.keep_running:
                s += 10
            return s
        ranked = sorted(bots, key=lambda b: (-_score(b), b.name.lower()))
        limit = 4
        row = None
        for i, b in enumerate(ranked[:limit]):
            if i % 2 == 0:
                row = tk.Frame(self.cards, bg=c["bg"])
                row.pack(fill="x", pady=4)
            self._card(row, b, advanced)
        if not bots:
            tk.Label(
                self.cards, text="Nenhum bot ainda.  Vá em Bots → + Novo bot",
                bg=c["bg"], fg=c["muted"], font=T.FONT_UI,
            ).pack(pady=40)

        nlog = 8 if advanced else 3
        if not logs:
            tk.Label(
                self.feed_inner, text="Sem eventos recentes", bg=c["card"], fg=c["dim"], font=T.FONT_SMALL,
            ).pack(anchor="w")
        for line in logs[-nlog:]:
            tk.Label(
                self.feed_inner, text=line[-140:] if advanced else line[-90:],
                bg=c["card"], fg=c["muted"] if not advanced else c["fg_secondary"],
                font=T.FONT_MONO if advanced else T.FONT_SMALL, anchor="w",
            ).pack(fill="x", pady=1)

    def _card(self, parent, bot, advanced: bool) -> None:
        c = self.app.colors
        if bot.is_connected:
            st, sub = "online", ("Farming" if bot.is_farming else "Online")
        elif bot.keep_running:
            st, sub = "paused", "Pausado"
        else:
            st, sub = "stopped", "Parado"

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
        more = icon_button(top, "more", c, command=lambda n=bot.name: self.app.show("bot_details", bot_name=n), size=14, bg=c["card"], color=c["muted"])
        more.pack(side="right")
        sub_l = tk.Label(fr, text=sub, bg=c["card"], fg=c["muted"], font=T.FONT_SMALL)
        sub_l.pack(anchor="w", pady=(6, 0))
        if advanced:
            raw = bot.raw or {}
            extra = []
            if raw.get("s_SteamID") or raw.get("SteamID"):
                extra.append(f"SteamID {raw.get('s_SteamID') or raw.get('SteamID')}")
            cf = raw.get("CardsFarmer") or {}
            if isinstance(cf, dict) and cf.get("GamesToFarm") is not None:
                extra.append(f"fila {len(cf.get('GamesToFarm') or [])}")
            if extra:
                tk.Label(fr, text=" · ".join(extra), bg=c["card"], fg=c["dim"], font=T.FONT_TINY).pack(anchor="w")
        W.bind_card_hover(fr, c, [fr, top, title, sub_l])
        fr.bind("<Button-1>", lambda e, n=bot.name: self.app.show("bot_details", bot_name=n))
        title.bind("<Button-1>", lambda e, n=bot.name: self.app.show("bot_details", bot_name=n))

    def _act(self, fn, name: str) -> None:
        def work():
            fn(name)
            self.app.ipc.invalidate_bots_cache()
            self.after(0, self.refresh)
        threading.Thread(target=work, daemon=True).start()

    def _start(self) -> None:
        def work():
            ok, msg = self.app.process_mgr.start()
            if not ok:
                self.after(0, lambda: themed_message(self, "ASF Desktop", msg, kind="error"))
            self.after(0, self.refresh)
        threading.Thread(target=work, daemon=True).start()

    def _stop(self) -> None:
        def work():
            try:
                self.app.ipc.exit_asf()
            except Exception:
                pass
            self.app.process_mgr.stop()
            self.app.ipc.invalidate_bots_cache()
            self.after(0, self.refresh)
        threading.Thread(target=work, daemon=True).start()

    def _pause(self) -> None:
        def work():
            self.app.ipc.pause_bot("ASF")
            self.app.ipc.invalidate_bots_cache()
            self.after(0, self.refresh)
        threading.Thread(target=work, daemon=True).start()
