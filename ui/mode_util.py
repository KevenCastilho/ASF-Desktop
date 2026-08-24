"""Simple vs Advanced — D-02: mesma app, densidades diferentes."""
from __future__ import annotations

import tkinter as tk

from ui import theme as T


def is_advanced(app) -> bool:
    return (app.settings.get("mode") or "simple").strip().lower() == "advanced"


def mode_label(app) -> str:
    return "Avançado" if is_advanced(app) else "Simples"


def mode_banner(
    parent,
    app,
    *,
    simple: str,
    advanced: str,
    pack_opts: dict | None = None,
) -> tk.Label:
    c = app.colors
    lbl = tk.Label(
        parent,
        text=advanced if is_advanced(app) else simple,
        bg=c.get("bg", parent.cget("bg") if hasattr(parent, "cget") else c["bg"]),
        fg=c["accent"],
        font=T.FONT_TINY,
        anchor="w",
    )
    opts = {"fill": "x", "padx": 24, "pady": (0, 6)}
    if pack_opts:
        opts.update(pack_opts)
    lbl.pack(**opts)
    return lbl
