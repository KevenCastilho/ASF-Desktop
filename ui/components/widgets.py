"""Reusable themed widgets."""
from __future__ import annotations

import tkinter as tk
from ui import theme as T


def spaced(parent, colors, pady=8, padx=16) -> tk.Frame:
    f = tk.Frame(parent, bg=colors["bg"])
    f.pack(fill="x", padx=padx, pady=pady)
    return f


def h1(parent, text, colors) -> tk.Label:
    return tk.Label(parent, text=text, bg=colors["bg"], fg=colors["fg"], font=T.FONT_TITLE)


def h2(parent, text, colors) -> tk.Label:
    return tk.Label(parent, text=text, bg=colors["bg"], fg=colors["fg"], font=T.FONT_SUB)


def caption(parent, text, colors) -> tk.Label:
    return tk.Label(
        parent, text=text, bg=colors["bg"], fg=colors["muted"],
        font=T.FONT_SMALL, justify="left", wraplength=720,
    )


def primary_btn(parent, text, command, colors, **kw) -> tk.Button:
    b = tk.Button(
        parent, text=text, command=command,
        bg=colors["accent"], fg=colors["accent_fg"],
        activebackground=colors["accent_dim"], activeforeground=colors["accent_fg"],
        relief="flat", cursor="hand2", font=T.FONT_UI_BOLD,
        padx=14, pady=6, bd=0, **kw,
    )
    return b


def secondary_btn(parent, text, command, colors, **kw) -> tk.Button:
    b = tk.Button(
        parent, text=text, command=command,
        bg=colors["card"], fg=colors["fg"],
        activebackground=colors["card_hover"], activeforeground=colors["fg"],
        relief="flat", cursor="hand2", font=T.FONT_UI,
        padx=12, pady=5, bd=0,
        highlightthickness=1, highlightbackground=colors["border"],
        **kw,
    )
    return b


def icon_btn(parent, text, command, colors, **kw) -> tk.Button:
    return tk.Button(
        parent, text=text, command=command,
        bg=colors["header"], fg=colors["fg"],
        activebackground=colors["card_hover"], activeforeground=colors["fg"],
        relief="flat", cursor="hand2", font=T.FONT_ICON,
        bd=0, padx=10, pady=4, **kw,
    )


def card_frame(parent, colors) -> tk.Frame:
    fr = tk.Frame(
        parent, bg=colors["card"],
        highlightbackground=colors["border"], highlightthickness=1,
        padx=12, pady=10,
    )
    return fr


def bind_card_hover(fr: tk.Frame, colors, children: list | None = None) -> None:
    targets = [fr] + (children or [])

    def enter(_):
        for w in targets:
            try:
                w.configure(bg=colors["card_hover"])
            except tk.TclError:
                pass

    def leave(_):
        for w in targets:
            try:
                w.configure(bg=colors["card"])
            except tk.TclError:
                pass

    for w in targets:
        w.bind("<Enter>", enter)
        w.bind("<Leave>", leave)


def status_dot(status: str) -> str:
    # legado textual — preferir LucideIcon + status_color
    return {"online": "Online", "paused": "Pausado", "stopped": "Parado", "error": "Erro"}.get(status, status)


def entry(parent, colors, textvariable=None, show="", **kw) -> tk.Entry:
    e = tk.Entry(
        parent, textvariable=textvariable, show=show,
        bg=colors["input"], fg=colors["fg"],
        insertbackground=colors["accent"],
        relief="flat", font=T.FONT_UI, bd=0,
        highlightthickness=1, highlightbackground=colors["border"],
        highlightcolor=colors["accent"], **kw,
    )
    # padding visual via insert + frame if needed by caller
    return e



def separator(parent, colors, orient="h") -> tk.Frame:
    if orient == "h":
        return tk.Frame(parent, bg=colors["border"], height=1)
    return tk.Frame(parent, bg=colors["border"], width=1)
