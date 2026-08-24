"""Themed dialogs — replace stock messagebox where possible."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from ui.theme import FONT_TITLE, FONT_UI, FONT_SMALL, FONT_UI_BOLD
from ui.components.chrome import HoverBtn


def _center(win: tk.Toplevel, w: int, h: int) -> None:
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")


def themed_message(
    parent: tk.Misc | None,
    title: str,
    message: str,
    kind: str = "info",
) -> None:
    colors = {
        "bg": "#0d1117", "card": "#161b22", "fg": "#e6edf3",
        "muted": "#8b949e", "accent": "#3fb950", "border": "#30363d",
        "error": "#f85149", "warn": "#d29922",
    }
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=colors["border"])
    win.resizable(False, False)
    win.attributes("-topmost", True)
    try:
        win.grab_set()
    except tk.TclError:
        pass
    _center(win, 420, 200)
    box = tk.Frame(win, bg=colors["bg"])
    box.pack(fill="both", expand=True, padx=1, pady=1)
    accent = {"error": colors["error"], "warn": colors["warn"]}.get(kind, colors["accent"])
    tk.Label(box, text=title, bg=colors["bg"], fg=accent, font=FONT_UI_BOLD).pack(
        anchor="w", padx=20, pady=(18, 6),
    )
    tk.Label(
        box, text=message, bg=colors["bg"], fg=colors["fg"], font=FONT_UI,
        wraplength=380, justify="left",
    ).pack(anchor="w", padx=20, pady=4)
    HoverBtn(
        box, "OK", color=colors["accent"], fg="#0d1117",
        command=win.destroy, padx=20, pady=6,
    ).pack(anchor="e", padx=20, pady=16)
    win.wait_window()


def themed_confirm(
    parent: tk.Misc | None,
    title: str,
    message: str,
) -> bool:
    colors = {
        "bg": "#0d1117", "fg": "#e6edf3", "muted": "#8b949e",
        "accent": "#3fb950", "border": "#30363d", "card": "#161b22",
    }
    result = {"ok": False}
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=colors["border"])
    win.resizable(False, False)
    win.attributes("-topmost", True)
    try:
        win.grab_set()
    except tk.TclError:
        pass
    _center(win, 420, 200)
    box = tk.Frame(win, bg=colors["bg"])
    box.pack(fill="both", expand=True, padx=1, pady=1)
    tk.Label(box, text=title, bg=colors["bg"], fg=colors["fg"], font=FONT_UI_BOLD).pack(
        anchor="w", padx=20, pady=(18, 6),
    )
    tk.Label(
        box, text=message, bg=colors["bg"], fg=colors["muted"], font=FONT_UI,
        wraplength=380, justify="left",
    ).pack(anchor="w", padx=20, pady=4)

    def yes() -> None:
        result["ok"] = True
        win.destroy()

    def no() -> None:
        win.destroy()

    bar = tk.Frame(box, bg=colors["bg"])
    bar.pack(fill="x", padx=20, pady=16)
    HoverBtn(bar, "Cancelar", color=colors["card"], fg=colors["fg"], command=no).pack(side="left")
    HoverBtn(bar, "Confirmar", color=colors["accent"], fg="#0d1117", command=yes).pack(side="right")
    win.wait_window()
    return result["ok"]


def themed_ask_string(
    parent: tk.Misc | None,
    title: str,
    prompt: str,
    password: bool = False,
) -> str | None:
    colors = {
        "bg": "#0d1117", "card": "#161b22", "fg": "#e6edf3",
        "muted": "#8b949e", "accent": "#3fb950", "border": "#30363d", "input": "#0d1117",
    }
    result: dict[str, str | None] = {"value": None}
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=colors["border"])
    win.resizable(False, False)
    win.attributes("-topmost", True)
    try:
        win.grab_set()
    except tk.TclError:
        pass
    _center(win, 420, 220)
    box = tk.Frame(win, bg=colors["bg"])
    box.pack(fill="both", expand=True, padx=1, pady=1)
    tk.Label(box, text=title, bg=colors["bg"], fg=colors["fg"], font=FONT_UI_BOLD).pack(
        anchor="w", padx=20, pady=(18, 6),
    )
    tk.Label(box, text=prompt, bg=colors["bg"], fg=colors["muted"], font=FONT_UI).pack(
        anchor="w", padx=20,
    )
    var = tk.StringVar()
    ent = tk.Entry(
        box, textvariable=var, bg=colors["input"], fg=colors["fg"],
        insertbackground=colors["accent"], relief="flat", show="*" if password else "",
        highlightthickness=1, highlightbackground=colors["border"], highlightcolor=colors["accent"],
    )
    ent.pack(fill="x", padx=20, pady=12, ipady=8)
    ent.focus_set()

    def ok() -> None:
        result["value"] = var.get()
        win.destroy()

    def cancel() -> None:
        win.destroy()

    bar = tk.Frame(box, bg=colors["bg"])
    bar.pack(fill="x", padx=20, pady=8)
    HoverBtn(bar, "Cancelar", color=colors["card"], fg=colors["fg"], command=cancel).pack(side="left")
    HoverBtn(bar, "OK", color=colors["accent"], fg="#0d1117", command=ok).pack(side="right")
    ent.bind("<Return>", lambda e: ok())
    win.wait_window()
    return result["value"]
