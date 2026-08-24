from __future__ import annotations

import json
import tkinter as tk

from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import FlatScrollbar
from ui.components.dialogs import themed_message
from ui.icons.lucide import icon_button


class BotDetailsScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        self.bot_name = ""
        c = app.colors

        self.hero = tk.Frame(self, bg=c["bg"])
        self.hero.pack(fill="x", padx=24, pady=(20, 8))
        self.title = tk.Label(self.hero, text="Bot", bg=c["bg"], fg=c["fg"], font=T.FONT_TITLE)
        self.title.pack(side="left")
        self.badge = tk.Label(self.hero, text="", bg=c["bg"], fg=c["muted"], font=T.FONT_SMALL)
        self.badge.pack(side="left", padx=12)
        self.mode_lbl = tk.Label(self.hero, text="", bg=c["bg"], fg=c["accent"], font=T.FONT_TINY)
        self.mode_lbl.pack(side="right")

        self.body = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        self.body.pack(fill="x", padx=24, pady=8)
        self.body_lbl = tk.Label(
            self.body, text="", bg=c["card"], fg=c["fg_secondary"],
            justify="left", font=T.FONT_UI, anchor="w",
        )
        self.body_lbl.pack(anchor="w", padx=16, pady=16)

        self.tech_wrap = tk.Frame(self, bg=c["bg"])
        self.tech_hdr = tk.Label(
            self.tech_wrap, text="Detalhes técnicos (API)", bg=c["bg"], fg=c["dim"], font=T.FONT_TINY, anchor="w",
        )
        self.tech_hdr.pack(fill="x", padx=24, pady=(8, 4))
        self.tech_box = tk.Frame(self.tech_wrap, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        self.tech_box.pack(fill="both", expand=True, padx=24, pady=(0, 8))
        self.tech = tk.Text(
            self.tech_box, height=12, bg=c["input"], fg=c["fg_secondary"], relief="flat",
            font=T.FONT_MONO, wrap="word", highlightthickness=0, padx=10, pady=8,
        )
        sb = FlatScrollbar(self.tech_box, command=self.tech.yview, colors=c)
        self.tech.configure(yscrollcommand=sb.set)
        self.tech.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tech.configure(state="disabled")

        actions = tk.Frame(self, bg=c["bg"])
        actions.pack(anchor="w", padx=24, pady=12)
        for name, cmd, label in [
            ("play", self._start, "Executar"),
            ("pause", self._pause, "Pausar"),
            ("stop", self._stop, "Parar"),
        ]:
            frb = tk.Frame(actions, bg=c["bg"])
            frb.pack(side="left", padx=4)
            icon_button(frb, name, c, command=cmd, size=14, bg=c["card"], color=c["fg"]).pack(side="left")
            W.secondary_btn(frb, label, cmd, c).pack(side="left", padx=(4, 0))
        W.secondary_btn(actions, "Retomar", self._resume, c).pack(side="left", padx=4)
        W.secondary_btn(actions, "Configurar", self._cfg, c).pack(side="left", padx=4)
        W.secondary_btn(actions, "Excluir", self._delete, c).pack(side="left", padx=4)

        self.inv_wrap = tk.Frame(self, bg=c["bg"])
        self.inv_hdr = tk.Label(
            self.inv_wrap, text="Inventário (resumo)", bg=c["bg"], fg=c["dim"], font=T.FONT_TINY, anchor="w",
        )
        self.inv_hdr.pack(fill="x", padx=24, pady=(4, 2))
        self.inv_lbl = tk.Label(
            self.inv_wrap, text="", bg=c["card"], fg=c["fg_secondary"], font=T.FONT_SMALL,
            justify="left", anchor="w", padx=12, pady=10,
            highlightbackground=c["border"], highlightthickness=1,
        )
        self.inv_lbl.pack(fill="x", padx=24, pady=(0, 8))

    def open(self, bot_name: str) -> None:
        self.bot_name = bot_name
        self.on_show()

    def on_show(self, **kwargs) -> None:
        if kwargs.get("bot_name"):
            self.bot_name = kwargs["bot_name"]
        self.title.config(text=self.bot_name or "Bot")
        mode = (self.app.settings.get("mode") or "simple").strip().lower()
        advanced = mode == "advanced"
        self.mode_lbl.config(text="Visão avançada" if advanced else "Visão simples")

        bots = [b for b in self.app.ipc.bots_cached() if b.name == self.bot_name]
        if not bots:
            bots = self.app.ipc.parse_bots(self.app.ipc.get_bots(self.bot_name or "ASF"))
        c = self.app.colors
        if not bots:
            self.badge.config(text="—", fg=c["muted"])
            self.body_lbl.config(
                text="Bot não encontrado na IPC.\n"
                "Inicie o ASF na Home e aguarde a autenticação."
            )
            self.tech_wrap.pack_forget()
            return
        b = bots[0]
        if b.is_connected:
            self.badge.config(text="Online", fg=c["online"])
            status = "Conectado e autenticado na Steam."
        elif b.keep_running:
            self.badge.config(text="Pausado / aguardando", fg=c["paused"])
            status = "Bot ativo no ASF, sem sessão Steam no momento."
        else:
            self.badge.config(text="Parado", fg=c["stopped"])
            status = "Bot parado."

        lines = [status]
        raw = b.raw or {}
        if b.is_farming:
            lines.append("Farming de cartas em andamento.")
        cf = raw.get("CardsFarmer") or {}
        if isinstance(cf, dict):
            games = cf.get("CurrentGamesFarming") or cf.get("GamesToFarm") or []
            if isinstance(games, list) and games:
                names = []
                for g in games[:5]:
                    if isinstance(g, dict):
                        names.append(str(g.get("GameName") or g.get("AppID") or g))
                    else:
                        names.append(str(g))
                if names:
                    lines.append("Jogos: " + ", ".join(names))
            if cf.get("TimeRemaining"):
                lines.append(f"Tempo restante (API): {cf.get('TimeRemaining')}")
        sid = raw.get("s_SteamID") or raw.get("SteamID")
        if sid and advanced:
            lines.append(f"SteamID: {sid}")
        if not advanced:
            lines.append("")
            lines.append("Use Configurar para opções essenciais.")
            lines.append("Modo Avançado na gaveta mostra o JSON da API.")
        self.body_lbl.config(text="\n".join(lines))

        # inventário resumido (UI-012)
        self.inv_wrap.pack(fill="x")
        self.inv_lbl.config(text="Carregando inventário…")
        self.after(50, lambda: self._load_inv(self.bot_name))

        if advanced and b.raw:

            self.tech_wrap.pack(fill="both", expand=True)
            self.tech.configure(state="normal")
            self.tech.delete("1.0", "end")
            try:
                self.tech.insert("1.0", json.dumps(b.raw, indent=2, ensure_ascii=False)[:12000])
            except Exception:
                self.tech.insert("1.0", str(b.raw)[:12000])
            self.tech.configure(state="disabled")
        else:
            self.tech_wrap.pack_forget()

    def _start(self) -> None:
        r = self.app.ipc.start_bot(self.bot_name)
        themed_message(self, "Bot", "Iniciado." if r.ok else (r.error or "Falha"))
        self.app.ipc.invalidate_bots_cache()
        self.on_show()

    def _pause(self) -> None:
        r = self.app.ipc.pause_bot(self.bot_name)
        themed_message(self, "Bot", "Pausado." if r.ok else (r.error or "Falha"))
        self.app.ipc.invalidate_bots_cache()
        self.on_show()

    def _resume(self) -> None:
        r = self.app.ipc.resume_bot(self.bot_name)
        themed_message(self, "Bot", "Retomado." if r.ok else (r.error or "Falha"))
        self.app.ipc.invalidate_bots_cache()
        self.on_show()

    def _stop(self) -> None:
        r = self.app.ipc.stop_bot(self.bot_name)
        themed_message(self, "Bot", "Parado." if r.ok else (r.error or "Falha"))
        self.app.ipc.invalidate_bots_cache()
        self.on_show()

    def _cfg(self) -> None:
        self.app.show("configure_bot", bot_name=self.bot_name)

    def _delete(self) -> None:
        from ui.components.dialogs import themed_confirm
        if not themed_confirm(self, "Excluir bot", f"Remover «{self.bot_name}»?"):
            return
        r = self.app.ipc.delete_bot(self.bot_name)
        from integration.asf_config import delete_bot_file
        delete_bot_file(self.app.settings.get("asf_path") or "", self.bot_name)
        self.app.ipc.invalidate_bots_cache()
        themed_message(self, "Excluir", "OK" if r.ok else (r.error or "Arquivo local removido se existia"))
        self.app.show("bots", push=False)

    def _load_inv(self, name: str) -> None:
        if not name or self.app._current != "bot_details":
            return
        def work():
            r = self.app.ipc.get_inventory(name)
            if not r.ok:
                text = f"Inventário indisponível: {r.error or r.status}"
            else:
                data = r.data
                payload = data.get("Result", data) if isinstance(data, dict) else data
                n = 0
                if isinstance(payload, list):
                    n = len(payload)
                elif isinstance(payload, dict):
                    n = len(payload)
                text = f"{n} item(ns) reportados pela API.\nAbra Inventário para ações (loot/transfer)."
            self.after(0, lambda: self.inv_lbl.config(text=text) if self.app._current == "bot_details" else None)
        import threading
        threading.Thread(target=work, daemon=True).start()
