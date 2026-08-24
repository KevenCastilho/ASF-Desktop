from __future__ import annotations

import shutil
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from ui.components.dialogs import themed_message
from ui.mode_util import is_advanced, mode_banner

from integration.asf_config import config_dir, asf_root_from_path
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn


class ImportExportScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        W.h1(self, "Importar / Exportar", c).pack(anchor="w", padx=24, pady=(20, 4))
        W.caption(
            self,
            "Exporta configs JSON do ASF. Arquivos podem conter senhas — trate com cuidado.",
            c,
        ).pack(anchor="w", padx=24, pady=(0, 16))

        for title, desc, cmd, primary in [
            ("Exportar config", "Gera um ZIP com os JSON da pasta config/", self._export, True),
            ("Importar config", "ZIP ou JSON único para a pasta config/", self._import, False),
        ]:
            card = tk.Frame(
                self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1,
                padx=18, pady=14,
            )
            card.pack(fill="x", padx=24, pady=6)
            tk.Label(card, text=title, bg=c["card"], fg=c["fg"], font=T.FONT_UI_BOLD).pack(anchor="w")
            tk.Label(card, text=desc, bg=c["card"], fg=c["muted"], font=T.FONT_SMALL).pack(anchor="w", pady=(4, 10))
            if primary:
                HoverBtn(card, "Exportar…", color=c["accent"], fg="#0d1117", command=cmd).pack(anchor="w")
            else:
                HoverBtn(card, "Importar…", color=c["bg"], fg=c["fg"], command=cmd).pack(anchor="w")

    def on_show(self, **kwargs) -> None:
        # path hint
        try:
            from integration.asf_config import asf_root_from_path
            root = asf_root_from_path(self.app.settings.get("asf_path") or "")
            if hasattr(self, "_path_lbl"):
                self._path_lbl.config(text=(str(root) if root and is_advanced(self.app) else ""))
        except Exception:
            pass
        pass

    def _export(self) -> None:
        d = config_dir(self.app.settings.get("asf_path") or "")
        if not d or not d.is_dir():
            themed_message(self, "Exportar", "Config do ASF não encontrada.", kind="error")
            return
        dest = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP", "*.zip")])
        if not dest:
            return
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in d.glob("*.json"):
                zf.write(p, arcname=p.name)
        themed_message(self, "Exportar", f"Exportado:\n{dest}")

    def _import(self) -> None:
        d = config_dir(self.app.settings.get("asf_path") or "")
        if not d:
            root = asf_root_from_path(self.app.settings.get("asf_path") or "")
            if not root:
                themed_message(self, "Importar", "ASF não configurado.", kind="error")
                return
            d = root / "config"
            d.mkdir(parents=True, exist_ok=True)
        path = filedialog.askopenfilename(filetypes=[("ZIP", "*.zip"), ("JSON", "*.json")])
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p, "r") as zf:
                zf.extractall(d)
        else:
            shutil.copy2(p, d / p.name)
        themed_message(self, "Importar", "Arquivos copiados para config do ASF.")
