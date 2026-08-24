from __future__ import annotations

from ui.mode_util import mode_banner

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from ui.components.dialogs import themed_message

from ui import theme as T
from ui.components import widgets as W


class SetupScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        mode_banner(self, app, simple="Fluxo guiado — selecionar ASF ou baixar do GitHub", advanced="Mesmo fluxo; densidade avançada nas configs após o setup")
        c = app.colors

        box = tk.Frame(self, bg=c["bg"])
        box.place(relx=0.5, rely=0.42, anchor="center")

        tk.Label(box, text="ASF Desktop", bg=c["bg"], fg=c["fg"], font=("Segoe UI", 22, "bold")).pack()
        tk.Label(
            box, text="Interface gráfica para o ArchiSteamFarm",
            bg=c["bg"], fg=c["muted"], font=T.FONT_UI,
        ).pack(pady=(6, 28))

        for title, desc, btn, cmd, primary in [
            (
                "Já tenho o ASF instalado",
                "Selecionar a pasta ou o executável existente",
                "Selecionar ASF",
                self._pick,
                True,
            ),
            (
                "Ainda não tenho o ASF",
                "Baixar a versão oficial stable direto do GitHub",
                "Continuar com o Desktop",
                self._download,
                False,
            ),
        ]:
            card = tk.Frame(
                box, bg=c["card"], highlightbackground=c["border"], highlightthickness=1,
                padx=22, pady=18,
            )
            card.pack(fill="x", pady=8)
            tk.Label(card, text=title, bg=c["card"], fg=c["fg"], font=T.FONT_SUB).pack(anchor="w")
            tk.Label(card, text=desc, bg=c["card"], fg=c["muted"], font=T.FONT_SMALL).pack(anchor="w", pady=(4, 12))
            if primary:
                W.primary_btn(card, btn, cmd, c).pack(anchor="w")
            else:
                W.secondary_btn(card, btn, cmd, c).pack(anchor="w")

        self.dl_status = tk.Label(box, text="", bg=c["bg"], fg=c["muted"], font=T.FONT_SMALL)
        self.dl_status.pack(anchor="w", pady=(12, 4))
        self.pb = ttk.Progressbar(box, length=420, mode="determinate", style="ASF.Horizontal.TProgressbar")
        self.pb.pack(anchor="w")

    def on_show(self, **kwargs) -> None:
        pass

    def _finish(self, path: str) -> None:
        self.app.settings.set("asf_path", path)
        self.app.settings.save()
        self.app._sync_ipc_password()
        ok, msg = self.app.process_mgr.validate_install()
        if not ok:
            themed_message(self, "ASF Desktop", msg, kind="error")
            return
        cfg = Path(path)
        cfg = cfg.parent / "config" if cfg.is_file() else cfg / "config"
        bots = [b for b in cfg.glob("*.json")] if cfg.is_dir() else []
        bots = [b for b in bots if b.name.upper() != "ASF.JSON"]
        themed_message(self, "ASF Desktop", f"ASF configurado:\n{msg}")
        if not bots:
            themed_message(self, "ASF Desktop", "Nenhum bot encontrado.\nUse Bots → + Novo bot.")
        self.app.show("home", push=False)

    def _pick(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione o executável do ASF",
            filetypes=[
                ("ASF Windows", "ArchiSteamFarm.exe"),
                ("ASF", "ArchiSteamFarm*"),
                ("All", "*.*"),
            ],
        )
        if not path:
            path = filedialog.askdirectory(title="Ou selecione a pasta do ASF")
        if path:
            self._finish(path)

    def _download(self) -> None:
        dest = Path(self.app.settings.get("asf_download_dir"))

        def work() -> None:
            try:
                from process.asf_downloader import download_and_extract

                def prog(msg: str, frac: float) -> None:
                    self.after(0, lambda: self._set_prog(msg, frac))

                exe = download_and_extract(dest, on_progress=prog)
                self.after(0, lambda: self._finish(str(exe)))
            except Exception as e:
                self.after(0, lambda: themed_message(self, "Download ASF", str(e), kind="error"))

        threading.Thread(target=work, daemon=True).start()

    def _set_prog(self, msg: str, frac: float) -> None:
        self.dl_status.config(text=msg)
        self.pb["value"] = max(0, min(100, frac * 100))
