from __future__ import annotations

import threading
import tkinter as tk

from integration import asf_commands
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn, FlatScrollbar
from ui.components.dialogs import themed_message, themed_ask_string, themed_confirm
from ui.components.pickers import ThemedDropdown
from ui.mode_util import is_advanced, mode_banner
from integration.capabilities import get_cached, probe
from ui.components.controls import ThemedRadioGroup, themed_text


class InventoryScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        self._busy = False
        c = app.colors
        W.h1(self, "Inventário", c).pack(anchor="w", padx=24, pady=(20, 4))
        W.caption(
            self,
            "loot → Master · transfer → outro bot. Comandos oficiais ASF (Master).",
            c,
        ).pack(anchor="w", padx=24)

        bar = tk.Frame(self, bg=c["bg"])
        bar.pack(fill="x", padx=24, pady=10)
        self.mode = tk.StringVar(value="global")
        ThemedRadioGroup(
            bar, c,
            [("Global", "global"), ("Por bot", "bot"), ("API real", "real")],
            variable=self.mode, command=self.refresh, style="chip",
        ).pack(side="left")
        tk.Label(bar, text="Bot", bg=c["bg"], fg=c["muted"], font=T.FONT_SMALL).pack(side="left", padx=(8, 4))
        self.bot_dd = ThemedDropdown(bar, c, values=["ASF"], width=18)
        self.bot_dd.pack(side="left")
        HoverBtn(bar, "Atualizar", color=c["card"], fg=c["fg"], command=self.refresh, padx=10, pady=4).pack(side="right")

        wrap = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=24, pady=8)
        self.list = tk.Listbox(
            wrap, bg=c["card"], fg=c["fg_secondary"], relief="flat", font=T.FONT_MONO,
            highlightthickness=0, activestyle="none",
            selectbackground=c["card_hover"], selectforeground=c["fg"],
        )
        sb = FlatScrollbar(wrap, command=self.list.yview)
        self.list.configure(yscrollcommand=sb.set)
        self.list.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        sb.pack(side="right", fill="y", pady=4)

        actions = tk.Frame(self, bg=c["bg"])
        actions.pack(fill="x", padx=24, pady=(4, 14))
        tk.Label(actions, text="AÇÕES ASF (Master)", bg=c["bg"], fg=c["dim"], font=T.FONT_TINY).pack(anchor="w")
        row = tk.Frame(actions, bg=c["bg"])
        row.pack(fill="x", pady=6)
        HoverBtn(row, "Loot → Master", color=c["accent"], fg="#0d1117", command=self._loot).pack(side="left", padx=(0, 6))
        HoverBtn(row, "Loot@ AppIDs…", color=c["card"], fg=c["fg"], command=self._loot_apps).pack(side="left", padx=4)
        HoverBtn(row, "Transfer → bot…", color=c["card"], fg=c["fg"], command=self._transfer).pack(side="left", padx=4)
        HoverBtn(row, "Transfer@ AppIDs…", color=c["card"], fg=c["fg"], command=self._transfer_apps).pack(side="left", padx=4)

    def on_show(self, **kwargs) -> None:
        adv = is_advanced(self.app)
        try:
            self._mode_banner.config(
                text="Visão avançada — inclui modo API real (IPC Inventory)"
                if adv
                else "Visão simples — coletas nos logs (Global / Por bot)"
            )
        except Exception:
            pass
        # se simples e estava em API real, volta para global
        if not adv and self.mode.get() == "real":
            self.mode.set("global")
        try:
            cap = get_cached() or (probe(self.app.ipc) if self.app.process_mgr.is_running() else None)
            if cap is not None and not cap.has_inventory and self.mode.get() == "real":
                self.mode.set("global")
        except Exception:
            pass
        names = [b.name for b in self.app.ipc._bots_cache] or ["ASF"]
        self.bot_dd.set_values(names)
        self.list.delete(0, "end")
        self.list.insert("end", "  Carregando…")
        if not self.app.process_mgr.is_running():
            self.list.delete(0, "end")
            self.list.insert("end", "  ASF parado — inicie na Home para inventário via IPC.")
        self.refresh()

    def _bot(self) -> str:
        return self.bot_dd.get().strip() or "ASF"

    def refresh(self) -> None:
        if self._busy:
            return
        self._busy = True
        mode = self.mode.get()
        if not is_advanced(self.app) and mode == "real":
            mode = "global"
        bot = self._bot()

        def work():
            names = [b.name for b in self.app.ipc.bots_cached()] or ["ASF"]
            lines: list[str] = []
            if mode == "global":
                for line in self.app.process_mgr.get_recent_logs(150):
                    low = line.lower()
                    if any(k in low for k in ("carta", "card", "drop", "inventory", "loot", "trade", "transfer")):
                        lines.append(line)
                if not lines:
                    lines = ["(Nenhuma coleta/trade recente nos logs.)"]
            elif mode == "bot":
                for line in self.app.process_mgr.get_recent_logs(150):
                    if bot in line:
                        lines.append(line)
                if not lines:
                    lines = [f"(Sem linhas para {bot}.)"]
            else:
                r = self.app.ipc.get_inventory(bot)
                if not r.ok:
                    lines = [f"IPC Inventory: {r.error}", "Fallback: use Global/Por bot ou loot/transfer."]
                else:
                    text = str(r.data)
                    lines = [text[i : i + 120] for i in range(0, min(len(text), 3000), 120)]
            self.after(0, lambda: self._apply(names, lines))

        threading.Thread(target=work, daemon=True).start()

    def _apply(self, names: list[str], lines: list[str]) -> None:
        self._busy = False
        if self.app._current != "inventory":
            return
        self.bot_dd.set_values(names)
        self.list.delete(0, "end")
        for line in lines:
            self.list.insert("end", "  " + line)

    def _result(self, title: str, r) -> None:
        body = "OK — ver Console." if r.ok else (r.error or "Falha")
        if r.ok and r.data is not None:
            body = f"OK\n{str(r.data)[:300]}"
        themed_message(self, title, body, kind="info" if r.ok else "error")
        self.refresh()

    def _run_cmd(self, title: str, fn) -> None:
        def work():
            r = fn()
            self.after(0, lambda: self._result(title, r))
        threading.Thread(target=work, daemon=True).start()

    def _loot(self) -> None:
        bot = self._bot()
        if not themed_confirm(self, "Loot", f"loot {bot} → Master?"):
            return
        self._run_cmd("Loot", lambda: asf_commands.loot(self.app.ipc, bot))

    def _loot_apps(self) -> None:
        bot = self._bot()
        apps = themed_ask_string(self, "Loot@", "AppIDs (ex: 753):")
        if not apps:
            return
        self._run_cmd("Loot@", lambda: asf_commands.loot_appids(self.app.ipc, bot, apps.replace(",", " ")))

    def _transfer(self) -> None:
        bot = self._bot()
        target = themed_ask_string(self, "Transfer", "Bot de destino:")
        if not target:
            return
        if not themed_confirm(self, "Transfer", f"transfer {bot} → {target.strip()}?"):
            return
        self._run_cmd("Transfer", lambda: asf_commands.transfer(self.app.ipc, bot, target.strip()))

    def _transfer_apps(self) -> None:
        bot = self._bot()
        apps = themed_ask_string(self, "Transfer@", "AppIDs:")
        if not apps:
            return
        target = themed_ask_string(self, "Transfer@", "Bot destino:")
        if not target:
            return
        self._run_cmd(
            "Transfer@",
            lambda: asf_commands.transfer_appids(self.app.ipc, bot, apps.replace(",", " "), target.strip()),
        )
