"""Ícones oficiais Lucide (lucide-static v0.468.0, ISC) — PNG + tint por tema."""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from typing import Callable

from PIL import Image, ImageTk

_PNG_DIR = Path(__file__).resolve().parent / "png"

ICON_FILES = {
    "home": "house",
    "bot": "bot",
    "activity": "activity",
    "package": "package",
    "ticket": "ticket",
    "key": "key",
    "pencil": "pencil",
    "wrench": "wrench",
    "terminal": "terminal",
    "puzzle": "puzzle",
    "file": "file-text",
    "refresh": "refresh-cw",
    "settings": "settings",
    "help": "circle-help",
    "book": "book-open",
    "sliders": "sliders-horizontal",
    "inbox": "inbox",
    "play": "play",
    "pause": "pause",
    "stop": "square",
    "menu": "menu",
    "more": "ellipsis-vertical",
    "back": "arrow-left",
    "circle": "circle",
    "circle_dot": "circle-dot",
    "search": "search",
    "download": "download",
    "check": "check",
    "chevron_right": "chevron-right",
    "power": "power",
    "circle_play": "circle-play",
    "circle_pause": "circle-pause",
    "circle_stop": "circle-stop",
}

_CACHE: dict[tuple, ImageTk.PhotoImage] = {}


def _parse_hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def photo(name: str, size: int, color: str) -> ImageTk.PhotoImage:
    stem = ICON_FILES.get(name, name)
    if stem not in ICON_FILES.values() and not (_PNG_DIR / f"{stem}.png").is_file():
        stem = "circle-help"
    key = (stem, size, color.lower())
    if key in _CACHE:
        return _CACHE[key]
    path = _PNG_DIR / f"{stem}.png"
    if not path.is_file():
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    else:
        img = Image.open(path).convert("RGBA")
        if img.size != (size, size):
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        r, g, b = _parse_hex(color)
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                pr, pg, pb, pa = px[x, y]
                if pa > 0:
                    px[x, y] = (r, g, b, pa)
    ph = ImageTk.PhotoImage(img)
    _CACHE[key] = ph
    return ph


class LucideIcon(tk.Label):
    def __init__(self, parent, name: str, colors: dict, size: int = 18, color: str | None = None, **kw):
        bg = colors.get("card", "#161b22")
        try:
            bg = parent.cget("bg")
        except tk.TclError:
            pass
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0, **kw)
        self._name = name
        self._colors = colors
        self._size = size
        self._color = color
        self._photo = None
        self.redraw(color)

    def redraw(self, color: str | None = None) -> None:
        col = color or self._color or self._colors.get("fg_secondary", "#c9d1d9")
        self._color = col
        self._photo = photo(self._name, self._size, col)
        self.configure(image=self._photo)

    def set_bg(self, bg: str) -> None:
        self.configure(bg=bg)


def icon_button(
    parent,
    name: str,
    colors: dict,
    command: Callable | None = None,
    size: int = 16,
    color: str | None = None,
    bg: str | None = None,
    padx: int = 6,
    pady: int = 4,
) -> tk.Button:
    """Botão só com ícone Lucide (mantém ref da imagem no botão)."""
    bg = bg or colors.get("header", colors.get("card", "#161b22"))
    col = color or colors.get("fg", "#e6edf3")
    img = photo(name, size, col)
    btn = tk.Button(
        parent,
        image=img,
        command=command,
        bg=bg,
        activebackground=colors.get("card_hover", bg),
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=padx,
        pady=pady,
        highlightthickness=0,
    )
    btn._lucide_img = img  # noqa: prevent GC
    return btn


def status_icon_name(status: str) -> str:
    return {
        "online": "circle_dot",
        "paused": "circle",
        "stopped": "circle",
        "error": "circle",
    }.get(status, "circle")


def status_color(status: str, colors: dict) -> str:
    return {
        "online": colors.get("online", "#3fb950"),
        "paused": colors.get("paused", "#d29922"),
        "stopped": colors.get("stopped", "#f85149"),
        "error": colors.get("error", "#f85149"),
    }.get(status, colors.get("muted", "#8b949e"))
