"""Popup de input — janela separada, visual alinhado ao app."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from ui.theme import FONT_UI, FONT_UI_BOLD, FONT_SMALL, FONT_TITLE


def show_input_popup(
    parent: tk.Tk | None,
    title: str,
    message: str,
    bot_name: str = "",
    on_submit: Callable[[str], None] | None = None,
    password: bool = False,
) -> None:
    bg, card, fg, muted, accent, border = (
        "#0d1117", "#161b22", "#e6edf3", "#8b949e", "#3fb950", "#30363d",
    )
    win = tk.Toplevel(parent)
    win.title(title or "Entrada solicitada")
    win.configure(bg=bg)
    win.attributes("-topmost", True)
    win.geometry("440x280")
    win.resizable(False, False)
    try:
        win.grab_set()
    except tk.TclError:
        pass

    outer = tk.Frame(win, bg=border)
    outer.pack(fill="both", expand=True, padx=0, pady=0)
    box = tk.Frame(outer, bg=bg)
    box.pack(fill="both", expand=True, padx=1, pady=1)

    tk.Label(box, text="Entrada solicitada", bg=bg, fg=fg, font=FONT_TITLE).pack(
        anchor="w", padx=20, pady=(20, 4),
    )
    if bot_name:
        tk.Label(box, text=f"Bot: {bot_name}", bg=bg, fg=accent, font=FONT_SMALL).pack(
            anchor="w", padx=20,
        )
    tk.Label(
        box, text=message or "O ASF precisa de uma informação para continuar.",
        bg=bg, fg=muted, wraplength=400, justify="left", font=FONT_UI,
    ).pack(anchor="w", padx=20, pady=12)

    var = tk.StringVar()
    ent = tk.Entry(
        box, textvariable=var, bg=card, fg=fg, insertbackground=accent,
        relief="flat", font=FONT_UI, show="*" if password else "",
        highlightthickness=1, highlightbackground=border, highlightcolor=accent,
    )
    ent.pack(fill="x", padx=20, ipady=10)
    ent.focus_set()

    def submit() -> None:
        val = var.get()
        win.destroy()
        if on_submit:
            on_submit(val)

    def cancel() -> None:
        win.destroy()
        if on_submit:
            pass

    btns = tk.Frame(box, bg=bg)
    btns.pack(fill="x", padx=20, pady=18)
    tk.Button(
        btns, text="Cancelar", command=cancel, bg=card, fg=fg, relief="flat",
        padx=14, pady=6, cursor="hand2", font=FONT_UI,
    ).pack(side="left")
    tk.Button(
        btns, text="Enviar", command=submit, bg=accent, fg="#0d1117", relief="flat",
        padx=18, pady=6, cursor="hand2", font=FONT_UI_BOLD,
    ).pack(side="right")
    ent.bind("<Return>", lambda e: submit())
    tk.Label(
        box, text="Enviado ao ASF · o Desktop não armazena este valor",
        bg=bg, fg=muted, font=FONT_SMALL,
    ).pack(anchor="w", padx=20, pady=(0, 12))
