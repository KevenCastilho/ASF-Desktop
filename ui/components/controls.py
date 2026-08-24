"""Controles realmente desenhados no tema (não só fg/bg em widget nativo)."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from ui.theme import FONT_UI, FONT_SMALL, FONT_MONO
from ui.components.chrome import FlatScrollbar


def themed_entry(parent, colors: dict, textvariable: tk.Variable | None = None, show: str = "", **kw) -> tk.Entry:
    return tk.Entry(
        parent,
        textvariable=textvariable,
        show=show,
        bg=colors["input"],
        fg=colors["fg"],
        insertbackground=colors["accent"],
        relief="flat",
        font=FONT_UI,
        highlightthickness=1,
        highlightbackground=colors["border"],
        highlightcolor=colors["accent"],
        bd=0,
        **kw,
    )


def themed_text(parent, colors: dict, height: int = 8, **kw) -> tk.Text:
    return tk.Text(
        parent,
        height=height,
        bg=colors["input"],
        fg=colors["fg"],
        insertbackground=colors["accent"],
        relief="flat",
        font=FONT_MONO,
        padx=10,
        pady=8,
        highlightthickness=1,
        highlightbackground=colors["border"],
        highlightcolor=colors["accent"],
        bd=0,
        selectbackground=colors.get("info", "#58a6ff"),
        selectforeground=colors["fg"],
        **kw,
    )


class ThemedEntry(tk.Frame):
    def __init__(self, parent, colors: dict, textvariable=None, placeholder: str = "", show: str = "", **kw):
        bg = colors["bg"]
        try:
            bg = parent.cget("bg")
        except tk.TclError:
            pass
        super().__init__(parent, bg=bg, highlightthickness=0, **kw)
        self.colors = colors
        self._placeholder = placeholder
        self._var = textvariable or tk.StringVar()
        self._ph = False
        # borda externa
        self.border = tk.Frame(self, bg=colors["border"], padx=1, pady=1)
        self.border.pack(fill="x")
        self.entry = tk.Entry(
            self.border,
            textvariable=self._var,
            show=show,
            bg=colors["input"],
            fg=colors["fg"],
            insertbackground=colors["accent"],
            relief="flat",
            font=FONT_UI,
            bd=0,
            highlightthickness=0,
        )
        self.entry.pack(fill="x", ipady=9, padx=8)
        self.entry.bind("<FocusIn>", self._fin)
        self.entry.bind("<FocusOut>", self._fout)
        if placeholder and not self._var.get():
            self._show_ph()

    def _show_ph(self):
        self._ph = True
        self._var.set(self._placeholder)
        self.entry.config(fg=self.colors["muted"])

    def _fin(self, _=None):
        self.border.config(bg=self.colors["accent"])
        if self._ph:
            self._var.set("")
            self.entry.config(fg=self.colors["fg"])
            self._ph = False

    def _fout(self, _=None):
        self.border.config(bg=self.colors["border"])
        if not self._var.get() and self._placeholder:
            self._show_ph()

    def get(self) -> str:
        return "" if self._ph else self._var.get()

    def apply_colors(self, colors: dict) -> None:
        self.colors = colors
        self.border.config(bg=colors["border"])
        self.entry.config(bg=colors["input"], fg=colors["muted"] if self._ph else colors["fg"], insertbackground=colors["accent"])


class ThemedCheck(tk.Frame):
    """Checkbox desenhado (canvas), não o nativo do SO."""

    SIZE = 18

    def __init__(self, parent, colors: dict, text: str = "", variable: tk.BooleanVar | None = None, command=None, **kw):
        bg = colors.get("card", colors["bg"])
        try:
            bg = parent.cget("bg")
        except tk.TclError:
            pass
        super().__init__(parent, bg=bg, **kw)
        self.colors = colors
        self._var = variable or tk.BooleanVar(value=False)
        self._command = command
        self._canvas = tk.Canvas(self, width=self.SIZE, height=self.SIZE, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self._canvas.pack(side="left")
        self._lbl = tk.Label(self, text=text, bg=bg, fg=colors["fg_secondary"], font=FONT_UI, cursor="hand2")
        if text:
            self._lbl.pack(side="left", padx=(8, 0))
        for w in (self._canvas, self._lbl, self):
            w.bind("<Button-1>", self._toggle)
        self._var.trace_add("write", lambda *_: self._draw())
        self._draw()

    def _draw(self) -> None:
        c = self.colors
        cv = self._canvas
        cv.delete("all")
        on = bool(self._var.get())
        s = self.SIZE - 1
        fill = c["accent"] if on else c.get("check_off", c["border"])
        outline = c["accent"] if on else c["border"]
        cv.create_rectangle(1, 1, s, s, fill=fill, outline=outline, width=1)
        if on:
            # check mark
            cv.create_line(4, 9, 8, 13, 14, 5, fill=c["accent_fg"], width=2, capstyle=tk.ROUND, joinstyle=tk.ROUND)

    def _toggle(self, _=None) -> None:
        self._var.set(not self._var.get())
        if self._command:
            self._command()

    @property
    def variable(self) -> tk.BooleanVar:
        return self._var

    def apply_colors(self, colors: dict) -> None:
        self.colors = colors
        bg = colors.get("card", colors["bg"])
        self.config(bg=bg)
        self._canvas.config(bg=bg)
        self._lbl.config(bg=bg, fg=colors["fg_secondary"])
        self._draw()


class ThemedRadioGroup(tk.Frame):
    """Segmented control / chips desenhados."""

    def __init__(
        self,
        parent,
        colors: dict,
        options: list[tuple[str, str]],
        variable: tk.StringVar | None = None,
        command: Callable | None = None,
        style: str = "chip",
        **kw,
    ):
        bg = colors["bg"]
        try:
            bg = parent.cget("bg")
        except tk.TclError:
            pass
        super().__init__(parent, bg=bg, **kw)
        self.colors = colors
        self._var = variable or tk.StringVar(value=options[0][1] if options else "")
        self._command = command
        self._style = style
        self._opts = options
        self._labels: dict[str, tk.Label] = {}
        if style == "chip":
            shell = tk.Frame(self, bg=colors["border"], padx=1, pady=1)
            shell.pack(anchor="w")
            self._inner = tk.Frame(shell, bg=colors.get("chip_off", colors["border_soft"]))
            self._inner.pack()
            for i, (label, val) in enumerate(options):
                lbl = tk.Label(
                    self._inner,
                    text=f"  {label}  ",
                    font=FONT_SMALL,
                    cursor="hand2",
                    padx=10,
                    pady=6,
                )
                lbl.pack(side="left")
                lbl.bind("<Button-1>", lambda e, v=val: self._pick(v))
                self._labels[val] = lbl
        else:
            self._inner = self
            for label, val in options:
                row = tk.Frame(self, bg=bg)
                row.pack(fill="x", pady=3)
                canvas = tk.Canvas(row, width=18, height=18, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
                canvas.pack(side="left")
                lbl = tk.Label(row, text=label, bg=bg, fg=colors["fg_secondary"], font=FONT_UI, cursor="hand2")
                lbl.pack(side="left", padx=(8, 0))
                for w in (canvas, lbl, row):
                    w.bind("<Button-1>", lambda e, v=val: self._pick(v))
                self._labels[val] = (canvas, lbl, row)
        self._var.trace_add("write", lambda *_: self._sync())
        self._sync()

    def _pick(self, val: str) -> None:
        self._var.set(val)
        if self._command:
            self._command()

    def _sync(self) -> None:
        c = self.colors
        cur = self._var.get()
        if self._style == "chip":
            for val, lbl in self._labels.items():
                on = val == cur
                lbl.config(
                    bg=c.get("chip_on", c["accent"]) if on else c.get("chip_off", c["border_soft"]),
                    fg=c["accent_fg"] if on else c["muted"],
                    font=("Segoe UI", 9, "bold") if on else FONT_SMALL,
                )
        else:
            for val, (canvas, lbl, row) in self._labels.items():
                on = val == cur
                canvas.delete("all")
                canvas.create_oval(2, 2, 16, 16, outline=c["accent"] if on else c["border"], width=2)
                if on:
                    canvas.create_oval(6, 6, 12, 12, fill=c["accent"], outline="")
                lbl.config(fg=c["fg"] if on else c["fg_secondary"])

    def apply_colors(self, colors: dict) -> None:
        self.colors = colors
        self._sync()


class SegmentedControl(ThemedRadioGroup):
    def __init__(self, parent, colors, options, variable=None, command=None, **kw):
        super().__init__(parent, colors, options, variable=variable, command=command, style="chip", **kw)


def attach_flat_scroll(parent, widget, colors: dict):
    sb = FlatScrollbar(parent, command=widget.yview)
    # sync FlatScrollbar colors if supported
    if hasattr(sb, "TRACK"):
        sb.TRACK = colors.get("scroll_track", colors["bg"])
        sb.THUMB = colors.get("scroll_thumb", colors["border"])
        sb.HOVER = colors.get("scroll_hover", colors["muted"])
    widget.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y", pady=2, padx=(0, 2))
    return sb


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, colors: dict, **kw):
        super().__init__(parent, bg=colors["bg"], **kw)
        self.canvas = tk.Canvas(self, bg=colors["bg"], highlightthickness=0, bd=0)
        self.inner = tk.Frame(self.canvas, bg=colors["bg"])
        self.sb = FlatScrollbar(self, command=self.canvas.yview)
        FlatScrollbar.TRACK = colors.get("scroll_track", colors["bg"])
        FlatScrollbar.THUMB = colors.get("scroll_thumb", colors["border"])
        FlatScrollbar.HOVER = colors.get("scroll_hover", colors["muted"])
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _wheel(self, e):
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
