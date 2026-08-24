from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
import webbrowser

from domain.version import __version__, APP_NAME
from process.desktop_updater import check_latest, download_release, GITHUB_URL, extract_hint
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn
from ui.components.dialogs import themed_message, themed_confirm
from ui.mode_util import is_advanced, mode_banner


class DesktopUpdateScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        W.h1(self, "Atualização do Desktop", c).pack(anchor="w", padx=24, pady=(20, 4))
        W.caption(
            self,
            f"{APP_NAME} {__version__} · releases em {GITHUB_URL}",
            c,
        ).pack(anchor="w", padx=24, pady=(0, 4))
        mode_banner(
            self, app,
            simple="Verifica o GitHub Releases do ASF Desktop",
            advanced=f"Repo: {GITHUB_URL}/releases",
        )

        card = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1, padx=18, pady=14)
        card.pack(fill="x", padx=24, pady=8)
        self.status = tk.Label(card, text="Clique em Verificar.", bg=c["card"], fg=c["fg"], font=T.FONT_UI, justify="left")
        self.status.pack(anchor="w")
        self.notes = tk.Label(card, text="", bg=c["card"], fg=c["muted"], font=T.FONT_SMALL, wraplength=700, justify="left")
        self.notes.pack(anchor="w", pady=8)

        bar = tk.Frame(self, bg=c["bg"])
        bar.pack(fill="x", padx=24, pady=12)
        HoverBtn(bar, "Verificar atualização", color=c["accent"], fg="#0d1117", command=self._check).pack(side="left")
        HoverBtn(bar, "Abrir no GitHub", color=c["card"], fg=c["fg"], command=self._open_repo).pack(side="left", padx=8)
        self.btn_dl = HoverBtn(bar, "Baixar release", color=c["card"], fg=c["fg"], command=self._download)
        self._info = None

    def on_show(self, **kwargs) -> None:
        pass

    def _open_repo(self) -> None:
        url = (self._info or {}).get("html_url") or f"{GITHUB_URL}/releases"
        try:
            webbrowser.open(url)
        except Exception as e:
            themed_message(self, "GitHub", str(e), kind="error")

    def _check(self) -> None:
        self.status.config(text="Consultando GitHub…")

        def work():
            try:
                info = check_latest()
                self.after(0, lambda: self._show(info))
            except Exception as e:
                self.after(
                    0,
                    lambda: themed_message(
                        self, "Update",
                        f"Não foi possível verificar:\n{e}\n\nRepo: {GITHUB_URL}",
                        kind="error",
                    ),
                )

        threading.Thread(target=work, daemon=True).start()

    def _show(self, info: dict) -> None:
        self._info = info
        if info.get("newer"):
            self.status.config(
                text=f"Nova versão disponível: {info['tag']}  (atual: {info['current']})",
                fg=self.app.colors["accent"],
            )
            self.btn_dl.pack(side="left", padx=8)
        else:
            self.status.config(
                text=f"Você está em dia ({info['current']}). Remoto: {info['tag'] or '—'}",
                fg=self.app.colors["fg"],
            )
            self.btn_dl.pack_forget()
        note = (info.get("notes") or "")[:500]
        if is_advanced(self.app):
            note = f"{note}\n\n{info.get('repo_url') or GITHUB_URL}".strip()
        self.notes.config(text=note)

    def _download(self) -> None:
        if not self._info or not self._info.get("url"):
            themed_message(
                self, "Update",
                f"Nenhum asset de download.\nPublique um Release .zip em:\n{GITHUB_URL}/releases",
                kind="warn",
            )
            return
        if not themed_confirm(self, "Update", "Baixar o ZIP do release para a pasta de updates do Desktop?"):
            return
        dest = Path(self.app.settings.get("asf_download_dir") or ".").parent / "DesktopUpdates"

        def work():
            try:
                path = download_release(self._info["url"], dest)
                hint = extract_hint(path)
                msg = f"Baixado:\n{path}\n\nExtraia e substitua a pasta do ASF Desktop manualmente."
                if hint:
                    msg += f"\n\nConteúdo (topo):\n{hint}"
                self.after(0, lambda: themed_message(self, "Update", msg))
            except Exception as e:
                self.after(0, lambda: themed_message(self, "Update", str(e), kind="error"))

        threading.Thread(target=work, daemon=True).start()
