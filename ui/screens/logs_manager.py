"""Gerenciar / exportar logs, erros e crash reports."""
from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from integration.asf_config import asf_root_from_path
from security.redaction import redact
from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import HoverBtn, FlatScrollbar
from ui.components.dialogs import themed_message
from ui.components.controls import ThemedRadioGroup
from ui.mode_util import is_advanced, mode_banner


class LogsManagerScreen(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        W.h1(self, "Logs e diagnósticos", c).pack(anchor="w", padx=24, pady=(20, 4))
        W.caption(
            self,
            "Logs do processo (Desktop), arquivos em logs/ do ASF e crash reports. Exportação com redaction.",
            c,
        ).pack(anchor="w", padx=24, pady=(0, 12))

        bar = tk.Frame(self, bg=c["bg"])
        bar.pack(fill="x", padx=24, pady=4)
        self.source = tk.StringVar(value="process")
        ThemedRadioGroup(
            bar, c,
            [
                ("Processo", "process"),
                ("Arquivos ASF", "files"),
                ("Crashes", "crash"),
                ("Erros", "errors"),
            ],
            variable=self.source, command=self.refresh, style="chip",
        ).pack(side="left")
        HoverBtn(bar, "Atualizar", color=c["card"], fg=c["fg"], command=self.refresh, padx=10, pady=4).pack(side="right", padx=4)
        HoverBtn(bar, "Exportar ZIP", color=c["accent"], fg="#0d1117", command=self._export, padx=12, pady=4).pack(side="right")

        wrap = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=24, pady=12)
        self.list = tk.Listbox(
            wrap, bg=c["card"], fg=c["fg_secondary"], relief="flat", font=T.FONT_MONO,
            highlightthickness=0, activestyle="none",
            selectbackground=c["card_hover"], selectforeground=c["fg"],
        )
        sb = FlatScrollbar(wrap, command=self.list.yview)
        self.list.configure(yscrollcommand=sb.set)
        self.list.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        sb.pack(side="right", fill="y", pady=4)

    def on_show(self, **kwargs) -> None:
        self.refresh()

    def refresh(self) -> None:
        self.list.delete(0, "end")
        src = self.source.get()
        if src == "process":
            for line in self.app.process_mgr.get_recent_logs(500):
                self.list.insert("end", "  " + redact(line))
            if self.list.size() == 0:
                self.list.insert("end", "  (sem linhas do processo ainda)")
        elif src == "errors":
            for line in self.app.process_mgr.get_recent_logs(800):
                up = line.upper()
                if "|ERROR|" in up or "|FATAL|" in up or "|WARN|" in up:
                    self.list.insert("end", "  " + redact(line))
            if self.list.size() == 0:
                self.list.insert("end", "  (nenhum WARN/ERROR/FATAL na sessão)")
        elif src == "files":
            root = asf_root_from_path(self.app.settings.get("asf_path") or "")
            if not root:
                self.list.insert("end", "  ASF não configurado")
                return
            logs_dir = root / "logs"
            if not logs_dir.is_dir():
                self.list.insert("end", "  Pasta logs/ não encontrada")
                return
            for p in sorted(logs_dir.glob("*"), reverse=True)[:40]:
                if p.is_file():
                    size = p.stat().st_size
                    self.list.insert("end", f"  {p.name}  ({size} bytes)")
            log_txt = root / "log.txt"
            if log_txt.is_file():
                self.list.insert(0, f"  log.txt  ({log_txt.stat().st_size} bytes)")
        else:  # crash
            root = asf_root_from_path(self.app.settings.get("asf_path") or "")
            if not root:
                self.list.insert("end", "  ASF não configurado")
                return
            cfg = root / "config"
            found = False
            for p in (cfg.glob("*.crash") if cfg.is_dir() else []):
                found = True
                try:
                    body = redact(p.read_text(encoding="utf-8", errors="replace")[:500])
                except OSError:
                    body = "(não legível)"
                self.list.insert("end", f"  {p.name}")
                self.list.insert("end", f"    {body[:200]}")
            if not found:
                self.list.insert("end", "  Nenhum crash report em config/")

    def _export(self) -> None:
        dest = filedialog.asksaveasfilename(
            defaultextension=".zip",
            initialfile=f"asf-desktop-logs-{datetime.now().strftime('%Y%m%d-%H%M')}.zip",
            filetypes=[("ZIP", "*.zip")],
        )
        if not dest:
            return
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
            # process buffer
            buf = "\n".join(redact(l) for l in self.app.process_mgr.get_recent_logs(2000))
            zf.writestr("desktop-process.log", buf)
            root = asf_root_from_path(self.app.settings.get("asf_path") or "")
            if root:
                for p in (root / "logs").glob("*") if (root / "logs").is_dir() else []:
                    if p.is_file() and p.stat().st_size < 5_000_000:
                        try:
                            zf.writestr(f"asf-logs/{p.name}", redact(p.read_text(encoding="utf-8", errors="replace")))
                        except OSError:
                            pass
                crash = root / "config"
                if crash.is_dir():
                    for p in crash.glob("*.crash"):
                        try:
                            zf.writestr(f"crashes/{p.name}", redact(p.read_text(encoding="utf-8", errors="replace")))
                        except OSError:
                            pass
        themed_message(self, "Exportar logs", f"Exportado com redaction:\n{dest}")
