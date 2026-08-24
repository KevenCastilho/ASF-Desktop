"""Design tokens — ASF Desktop visual system."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

DARK = {
    "bg": "#0d1117",
    "bg_elevated": "#12171f",
    "card": "#161b22",
    "card_hover": "#1c2330",
    "input": "#0d1117",
    "fg": "#e6edf3",
    "fg_secondary": "#c9d1d9",
    "muted": "#8b949e",
    "dim": "#6e7681",
    "accent": "#3fb950",
    "accent_dim": "#238636",
    "accent_fg": "#0d1117",
    "warn": "#d29922",
    "error": "#f85149",
    "info": "#58a6ff",
    "border": "#30363d",
    "border_soft": "#21262d",
    "header": "#161b22",
    "status_bar": "#010409",
    "online": "#3fb950",
    "paused": "#d29922",
    "stopped": "#f85149",
    "drawer_w": 300,
    "scroll_track": "#0d1117",
    "scroll_thumb": "#30363d",
    "scroll_hover": "#484f58",
    "chip_off": "#21262d",
    "chip_on": "#238636",
    "check_off": "#30363d",
}

LIGHT = {
    "bg": "#f6f8fa",
    "bg_elevated": "#ffffff",
    "card": "#ffffff",
    "card_hover": "#f3f4f6",
    "input": "#ffffff",
    "fg": "#1f2328",
    "fg_secondary": "#424a53",
    "muted": "#656d76",
    "dim": "#8c959f",
    "accent": "#1a7f37",
    "accent_dim": "#2da44e",
    "accent_fg": "#ffffff",
    "warn": "#9a6700",
    "error": "#cf222e",
    "info": "#0969da",
    "border": "#d0d7de",
    "border_soft": "#eaeef2",
    "header": "#ffffff",
    "status_bar": "#eaeef2",
    "online": "#1a7f37",
    "paused": "#9a6700",
    "stopped": "#cf222e",
    "drawer_w": 300,
    "scroll_track": "#eaeef2",
    "scroll_thumb": "#afb8c1",
    "scroll_hover": "#8c959f",
    "chip_off": "#eaeef2",
    "chip_on": "#1a7f37",
    "check_off": "#d0d7de",
}

FONT_UI = ("Segoe UI", 10)
FONT_UI_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SUB = ("Segoe UI", 11, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_TINY = ("Segoe UI", 8)
FONT_MONO = ("Consolas", 9)
FONT_ICON = ("Segoe UI", 12)


def palette(theme: str) -> dict:
    if theme == "light":
        return dict(LIGHT)
    if theme == "dark":
        return dict(DARK)
    # system
    try:
        import sys
        if sys.platform == "win32":
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return dict(LIGHT) if val == 1 else dict(DARK)
    except Exception:
        pass
    return dict(DARK)


def apply_ttk(root: tk.Tk, colors: dict) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "ASF.Horizontal.TProgressbar",
        troughcolor=colors["border_soft"],
        background=colors["accent"],
        bordercolor=colors["border"],
        lightcolor=colors["accent"],
        darkcolor=colors["accent_dim"],
        thickness=6,
    )
    style.configure(
        "ASF.TScrollbar",
        background=colors["card"],
        troughcolor=colors["bg"],
        bordercolor=colors["bg"],
        arrowcolor=colors["muted"],
    )


def apply_widget_tree(widget: tk.Misc, colors: dict) -> None:
    """Repinta recursivamente widgets comuns (melhor esforço)."""
    try:
        cls = widget.winfo_class()
    except tk.TclError:
        return
    try:
        if cls in ("Frame", "Labelframe", "TFrame"):
            widget.configure(bg=colors["bg"])
        elif cls == "Label":
            # não força fg de labels que usam accent/status
            cur = str(widget.cget("bg"))
            if cur in ("", colors.get("bg"), "#0d1117", "#f6f8fa", "#161b22", "#ffffff", "#12171f"):
                widget.configure(bg=colors["bg"], fg=colors["fg"])
        elif cls == "Button":
            pass  # HoverBtn tem cor própria
        elif cls == "Entry":
            widget.configure(
                bg=colors["input"], fg=colors["fg"],
                insertbackground=colors["accent"],
                highlightbackground=colors["border"],
                highlightcolor=colors["accent"],
            )
        elif cls == "Text":
            widget.configure(
                bg=colors["input"], fg=colors["fg"],
                insertbackground=colors["accent"],
            )
        elif cls == "Listbox":
            widget.configure(
                bg=colors["card"], fg=colors["fg_secondary"],
                selectbackground=colors["card_hover"], selectforeground=colors["fg"],
            )
        elif cls == "Canvas":
            widget.configure(bg=colors["bg"], highlightbackground=colors["bg"])
    except tk.TclError:
        pass
    try:
        for child in widget.winfo_children():
            apply_widget_tree(child, colors)
    except tk.TclError:
        pass
