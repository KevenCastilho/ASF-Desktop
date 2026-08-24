"""MineRun-level chrome: hover buttons, filter pills, flat scrollbar."""
from __future__ import annotations

import tkinter as tk
from typing import Callable


def _lighten(hex_color: str, factor: float = 0.12) -> str:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return hex_color
    rgb = [int(h[i : i + 2], 16) for i in (0, 2, 4)]
    rgb = [min(255, int(c + (255 - c) * factor)) for c in rgb]
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _darken(hex_color: str, factor: float = 0.85) -> str:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return hex_color
    rgb = [int(h[i : i + 2], 16) for i in (0, 2, 4)]
    rgb = [max(0, int(c * factor)) for c in rgb]
    return "#{:02x}{:02x}{:02x}".format(*rgb)


class HoverBtn(tk.Button):
    def __init__(self, parent, text="", color="#161b22", fg="#e6edf3", font=("Segoe UI", 9, "bold"),
                 padx=14, pady=7, command=None, **kw):
        self._color = color
        self._hover = _lighten(color, 0.14)
        self._press = _darken(color, 0.82)
        super().__init__(
            parent, text=text, fg=fg, bg=color, activeforeground=fg,
            activebackground=self._hover, font=font, relief="flat", bd=0,
            cursor="hand2", padx=padx, pady=pady, command=command, **kw,
        )
        self.bind("<Enter>", lambda e: self._safe(self._hover))
        self.bind("<Leave>", lambda e: self._safe(self._color))
        self.bind("<ButtonPress-1>", lambda e: self._safe(self._press))
        self.bind("<ButtonRelease-1>", lambda e: self._safe(self._hover))

    def _safe(self, bg: str) -> None:
        if str(self["state"]) != "disabled":
            self.configure(bg=bg)


class FilterBtn(tk.Label):
    """Pill toggle for log levels."""

    def __init__(self, parent, text: str, color: str, on_toggle: Callable | None = None, **kw):
        self._on_bg = color
        self._off_bg = "#21262d"
        self._on_fg = "#0d1117"
        self._off_fg = "#8b949e"
        self._active = True
        self._on_toggle = on_toggle
        super().__init__(
            parent, text=f" {text} ", bg=self._on_bg, fg=self._on_fg,
            font=("Segoe UI", 8, "bold"), cursor="hand2", **kw,
        )
        self.bind("<Button-1>", self._click)

    @property
    def active(self) -> bool:
        return self._active

    def _click(self, _=None) -> None:
        self._active = not self._active
        if self._active:
            self.configure(bg=self._on_bg, fg=self._on_fg)
        else:
            self.configure(bg=self._off_bg, fg=self._off_fg)
        if self._on_toggle:
            self._on_toggle(self._active)


class FlatScrollbar(tk.Canvas):
    def __init__(self, parent, width=10, command=None, colors: dict | None = None, **kw):
        self.TRACK = (colors or {}).get("scroll_track", "#0d1117")
        self.THUMB = (colors or {}).get("scroll_thumb", "#30363d")
        self.HOVER = (colors or {}).get("scroll_hover", "#484f58")
        self.PRESS = (colors or {}).get("muted", "#6e7681")
        super().__init__(
            parent, width=width, bg=self.TRACK, highlightthickness=0, relief="flat", **kw,
        )
        self._cmd = command
        self._top = 0.0
        self._bot = 1.0
        self._drag = False
        self._dy0 = 0
        self._dt0 = 0.0
        self._hov = False
        self.bind("<Configure>", self._draw)
        self.bind("<ButtonPress-1>", self._click)
        self.bind("<B1-Motion>", self._drag_move)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<MouseWheel>", self._wheel)
        self.bind("<Enter>", lambda _: self._set_hov(True))
        self.bind("<Leave>", lambda _: self._set_hov(False))

    def set(self, lo, hi):
        self._top = float(lo)
        self._bot = float(hi)
        self._draw()

    def _draw(self, *_):
        self.delete("all")
        h, w = self.winfo_height(), self.winfo_width()
        if h < 2:
            return
        self.create_rectangle(0, 0, w, h, fill=self.TRACK, outline="")
        ty = max(4, int(self._top * h))
        by = max(min(h - 4, int(self._bot * h)), ty + 16)
        col = self.PRESS if self._drag else self.HOVER if self._hov else self.THUMB
        self.create_rectangle(2, ty, w - 2, by, fill=col, outline="")

    def _thumb_bounds(self):
        h = self.winfo_height()
        ty = max(4, int(self._top * h))
        return ty, max(min(h - 4, int(self._bot * h)), ty + 16)

    def _goto(self, top: float):
        vis = max(0.05, self._bot - self._top)
        top = max(0.0, min(1.0 - vis, top))
        if self._cmd:
            self._cmd("moveto", top)

    def _click(self, e):
        ty, by = self._thumb_bounds()
        if ty <= e.y <= by:
            self._drag = True
            self._dy0 = e.y
            self._dt0 = self._top
        else:
            vis = self._bot - self._top
            self._goto(self._top - vis if e.y < ty else self._top + vis)
        self._draw()

    def _drag_move(self, e):
        if not self._drag:
            return
        h = max(1, self.winfo_height())
        delta = (e.y - self._dy0) / h
        self._goto(self._dt0 + delta)
        self._draw()

    def _release(self, _):
        self._drag = False
        self._draw()

    def _wheel(self, e):
        if self._cmd:
            self._cmd("scroll", int(-1 * (e.delta / 120)), "units")

    def _set_hov(self, v: bool):
        self._hov = v
        self._draw()
