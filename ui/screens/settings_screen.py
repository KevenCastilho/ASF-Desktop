from __future__ import annotations

import tkinter as tk

from domain.version import __version__, APP_NAME
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn
from ui.components.controls import themed_entry, ThemedRadioGroup, ThemedCheck
from ui.components.dialogs import themed_message
from ui.components.pickers import PathPicker
from ui.mode_util import is_advanced, mode_banner


class SettingsScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        W.h1(self, "Configurações", c).pack(anchor="w", padx=24, pady=(20, 12))

        sec = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1, padx=16, pady=14)
        sec.pack(fill="x", padx=24, pady=6)
        tk.Label(sec, text="Tema", bg=c["card"], fg=c["fg"], font=T.FONT_UI_BOLD).pack(anchor="w")
        self.theme = tk.StringVar(value=app.settings.get("theme", "system"))
        ThemedRadioGroup(
            sec, c,
            [("Sistema", "system"), ("Escuro", "dark"), ("Claro", "light")],
            variable=self.theme, style="chip",
            command=self._preview_theme,
        ).pack(anchor="w", pady=(8, 12))
        tk.Label(
            sec, text="Clique em Claro/Escuro para aplicar na hora (reconstrói a interface).",
            bg=c["card"], fg=c["muted"], font=T.FONT_TINY,
        ).pack(anchor="w")

        tk.Label(sec, text="Ao fechar a janela", bg=c["card"], fg=c["fg"], font=T.FONT_UI_BOLD).pack(anchor="w")
        self.close_var = tk.StringVar(value=app.settings.get("close_behavior", "tray"))
        ThemedRadioGroup(
            sec, c,
            [("Minimizar para a bandeja", "tray"), ("Encerrar ASF Desktop", "exit")],
            variable=self.close_var, style="row",
        ).pack(anchor="w", pady=(6, 4))

        self.start_var = tk.BooleanVar(value=bool(app.settings.get("start_with_system")))
        ThemedCheck(sec, c, text="Iniciar com o sistema", variable=self.start_var).pack(anchor="w", pady=(10, 4))

        tk.Label(sec, text="Notificações", bg=c["card"], fg=c["fg"], font=T.FONT_UI_BOLD).pack(anchor="w", pady=(12, 4))
        notif = app.settings.get("notifications") or {}
        self.notif_vars = {}
        for key, label in [
            ("bot_connect", "Conexão de bot / input"),
            ("error", "Erros"),
            ("update", "Atualizações"),
            ("farming", "Farming"),
            ("tray", "Bandeja"),
        ]:
            v = tk.BooleanVar(value=bool(notif.get(key, True)))
            self.notif_vars[key] = v
            ThemedCheck(sec, c, text=label, variable=v).pack(anchor="w")

        sec2 = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1, padx=16, pady=14)
        sec2.pack(fill="x", padx=24, pady=6)
        tk.Label(sec2, text="Instalação ASF", bg=c["card"], fg=c["fg"], font=T.FONT_UI_BOLD).pack(anchor="w")
        self.path_var = tk.StringVar(value=app.settings.get("asf_path") or "")
        PathPicker(
            sec2, c, mode="file", title="ArchiSteamFarm.exe",
            filetypes=[("ASF", "ArchiSteamFarm.exe"), ("All", "*.*")],
            variable=self.path_var,
        ).pack(fill="x", pady=8)
        tk.Label(sec2, text="IPC Password", bg=c["card"], fg=c["muted"], font=T.FONT_SMALL).pack(anchor="w", pady=(8, 4))
        self.ipc_var = tk.StringVar(value=app.settings.get("ipc_password") or "")
        themed_entry(sec2, c, textvariable=self.ipc_var, show="*").pack(fill="x", ipady=9)

        self.adv_sec = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1, padx=16, pady=14)
        self.adv_sec.pack(fill="x", padx=24, pady=6)
        tk.Label(self.adv_sec, text="IPC (avançado)", bg=c["card"], fg=c["fg"], font=T.FONT_UI_BOLD).pack(anchor="w")
        row = tk.Frame(self.adv_sec, bg=c["card"])
        row.pack(fill="x", pady=6)
        tk.Label(row, text="Host", bg=c["card"], fg=c["muted"], font=T.FONT_SMALL).pack(side="left")
        self.ipc_host = tk.StringVar(value=str(app.settings.get("ipc_host") or "127.0.0.1"))
        themed_entry(row, c, textvariable=self.ipc_host).pack(side="left", fill="x", expand=True, padx=8, ipady=6)
        tk.Label(row, text="Porta", bg=c["card"], fg=c["muted"], font=T.FONT_SMALL).pack(side="left")
        self.ipc_port = tk.StringVar(value=str(app.settings.get("ipc_port") or 1242))
        themed_entry(row, c, textvariable=self.ipc_port).pack(side="left", padx=8, ipady=6, ipadx=4)
        tk.Label(self.adv_sec, text="Retenção Activity (linhas)", bg=c["card"], fg=c["muted"], font=T.FONT_SMALL).pack(anchor="w", pady=(8, 4))
        self.ret_var = tk.StringVar(value=str(app.settings.get("activity_retention") or 500))
        themed_entry(self.adv_sec, c, textvariable=self.ret_var).pack(fill="x", ipady=6)

        sec3 = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1, padx=16, pady=14)
        sec3.pack(fill="x", padx=24, pady=6)
        tk.Label(sec3, text="Sobre", bg=c["card"], fg=c["fg"], font=T.FONT_UI_BOLD).pack(anchor="w")
        about = (
            f"{APP_NAME} {__version__}\n"
            "Camada gráfica para ArchiSteamFarm.\n"
            "Créditos Desktop: (placeholder)\n"
            "ASF: projeto JustArchiNET"
        )
        tk.Label(sec3, text=about, bg=c["card"], fg=c["muted"], justify="left", font=T.FONT_SMALL).pack(anchor="w", pady=6)

        HoverBtn(self, "Salvar", color=c["accent"], fg="#0d1117", command=self._save).pack(anchor="e", padx=24, pady=16)

    def _preview_theme(self) -> None:
        """Aplica na hora ao clicar no chip (não espera Salvar)."""
        theme = (self.theme.get() or "system").strip().lower()
        if theme not in ("light", "dark", "system"):
            return
        app = self.app
        root = app.root
        app.settings.set("theme", theme)
        app.settings.save()
        root.after(10, lambda: app.apply_theme(theme))

    def on_show(self, **kwargs) -> None:
        self.path_var.set(self.app.settings.get("asf_path") or "")
        if is_advanced(self.app):
            self.adv_sec.pack(fill="x", padx=24, pady=6)
        else:
            self.adv_sec.pack_forget()

    def _save(self) -> None:
        path = self.path_var.get().strip()
        if path:
            self.app.settings.set("asf_path", path)
        self.app.settings.set("close_behavior", self.close_var.get())
        self.app.settings.set("start_with_system", bool(self.start_var.get()))
        try:
            from process.autostart import set_start_with_system
            ok, msg = set_start_with_system(bool(self.start_var.get()))
            if not ok:
                themed_message(self, "Autostart", f"Não foi possível aplicar: {msg}", kind="warn")
        except Exception as e:
            themed_message(self, "Autostart", str(e), kind="warn")
        if hasattr(self, "notif_vars"):
            self.app.settings.set(
                "notifications",
                {k: bool(v.get()) for k, v in self.notif_vars.items()},
            )

        self.app.settings.set("ipc_password", self.ipc_var.get())
        if is_advanced(self.app):
            self.app.settings.set("ipc_host", self.ipc_host.get().strip() or "127.0.0.1")
            try:
                self.app.settings.set("ipc_port", int(self.ipc_port.get().strip() or "1242"))
            except ValueError:
                pass
            try:
                self.app.settings.set("activity_retention", int(self.ret_var.get().strip() or "500"))
            except ValueError:
                pass
        theme = (self.theme.get() or "system").strip().lower()
        if theme not in ("light", "dark", "system"):
            theme = "system"
        self.app.settings.set("theme", theme)
        self.app.settings.save()
        try:
            ret = int(self.app.settings.get("activity_retention") or 500)
            self.app.process_mgr.log_lines = __import__("collections").deque(
                self.app.process_mgr.log_lines, maxlen=max(100, ret * 2)
            )
        except Exception:
            pass
        self.app._sync_ipc_password()
        # captura app/root ANTES de destruir a tela
        app = self.app
        root = app.root
        # aplica tema de forma adiada (fora deste callback)
        def _do():
            try:
                app.apply_theme(theme)
            except Exception as e:
                try:
                    themed_message(root, "Tema", f"Falha ao aplicar tema: {e}", kind="error")
                except Exception:
                    pass
        root.after(10, _do)
