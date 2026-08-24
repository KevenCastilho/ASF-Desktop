"""Themed dropdown + file path picker."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog
from typing import Callable

from ui.theme import FONT_UI
from ui.components.chrome import HoverBtn


class ThemedDropdown(tk.Frame):
    """Lista suspensa custom no tema do app."""

    def __init__(
        self,
        parent,
        colors: dict,
        values: list[str] | None = None,
        variable: tk.StringVar | None = None,
        width: int = 22,
        on_change: Callable[[str], None] | None = None,
        **kw,
    ):
        bg = colors["bg"]
        try:
            bg = parent.cget("bg")
        except tk.TclError:
            pass
        super().__init__(parent, bg=bg, **kw)
        self.colors = colors
        self._values = list(values or [])
        self._var = variable or tk.StringVar()
        self._on_change = on_change
        self._popup: tk.Toplevel | None = None
        self._display = tk.StringVar()

        self.btn = tk.Button(
            self,
            textvariable=self._display,
            anchor="w",
            bg=colors["card"],
            fg=colors["fg"],
            activebackground=colors["card_hover"],
            activeforeground=colors["fg"],
            relief="flat",
            font=FONT_UI,
            cursor="hand2",
            bd=0,
            highlightthickness=1,
            highlightbackground=colors["border"],
            padx=10,
            pady=6,
            command=self._toggle,
            width=width,
        )
        self.btn.pack(fill="x")

        if not self._var.get() and self._values:
            self._var.set(self._values[0])
        self._sync_display()
        self._var.trace_add("write", lambda *_: self._sync_display())

    def _sync_display(self) -> None:
        v = self._var.get() or "—"
        self._display.set(f"  {v}    ▾")

    def set_values(self, values: list[str]) -> None:
        self._values = list(values)
        if self._values and self._var.get() not in self._values:
            self._var.set(self._values[0])
        self._sync_display()

    def get(self) -> str:
        return self._var.get()

    def set(self, value: str) -> None:
        self._var.set(value)
        self._sync_display()

    def _toggle(self) -> None:
        if self._popup is not None:
            try:
                if self._popup.winfo_exists():
                    self._close()
                    return
            except tk.TclError:
                self._popup = None
        if not self._values:
            return
        c = self.colors
        pop = tk.Toplevel(self)
        pop.overrideredirect(True)
        pop.configure(bg=c["border"])
        try:
            pop.attributes("-topmost", True)
        except tk.TclError:
            pass
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = max(self.winfo_width(), 160)
        inner = tk.Frame(pop, bg=c["card"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        max_h = min(280, 28 * max(len(self._values), 1) + 8)
        canvas = tk.Canvas(inner, bg=c["card"], highlightthickness=0, height=max_h, width=w - 4)
        fr = tk.Frame(canvas, bg=c["card"])
        canvas.create_window((0, 0), window=fr, anchor="nw")
        canvas.pack(fill="both", expand=True)

        for val in self._values:
            b = tk.Button(
                fr,
                text=val,
                anchor="w",
                bg=c["card"],
                fg=c["fg"],
                activebackground=c["card_hover"],
                activeforeground=c["fg"],
                relief="flat",
                font=FONT_UI,
                bd=0,
                padx=12,
                pady=6,
                cursor="hand2",
                command=lambda v=val: self._pick(v),
            )
            b.pack(fill="x")

        fr.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        pop.geometry(f"{w}x{max_h}+{x}+{y}")
        self._popup = pop
        pop.bind("<FocusOut>", lambda e: self.after(150, self._close))
        pop.focus_set()

    def _pick(self, value: str) -> None:
        self._var.set(value)
        self._sync_display()
        self._close()
        if self._on_change:
            self._on_change(value)

    def _close(self) -> None:
        if self._popup is not None:
            try:
                if self._popup.winfo_exists():
                    self._popup.destroy()
            except tk.TclError:
                pass
        self._popup = None


class PathPicker(tk.Frame):
    """Campo de caminho + botão themed (file dialog nativo só no clique)."""

    def __init__(
        self,
        parent,
        colors: dict,
        mode: str = "file",
        filetypes: list | None = None,
        variable: tk.StringVar | None = None,
        title: str = "Selecionar",
        **kw,
    ):
        bg = colors["bg"]
        try:
            bg = parent.cget("bg")
        except tk.TclError:
            pass
        super().__init__(parent, bg=bg, **kw)
        self.colors = colors
        self.mode = mode
        self.filetypes = filetypes or [("All", "*.*")]
        self.title = title
        self._var = variable or tk.StringVar()

        self.entry = tk.Entry(
            self,
            textvariable=self._var,
            bg=colors["input"],
            fg=colors["fg"],
            insertbackground=colors["accent"],
            relief="flat",
            font=FONT_UI,
            highlightthickness=1,
            highlightbackground=colors["border"],
            highlightcolor=colors["accent"],
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=7)
        HoverBtn(
            self,
            "…",
            color=colors["card"],
            fg=colors["fg"],
            command=self._browse,
            padx=12,
            pady=6,
        ).pack(side="left", padx=(6, 0))

    @property
    def variable(self) -> tk.StringVar:
        return self._var

    def get(self) -> str:
        return self._var.get().strip()

    def set(self, path: str) -> None:
        self._var.set(path)

    def _browse(self) -> None:
        if self.mode == "dir":
            path = filedialog.askdirectory(title=self.title)
        elif self.mode == "save":
            path = filedialog.asksaveasfilename(title=self.title, filetypes=self.filetypes)
        else:
            path = filedialog.askopenfilename(title=self.title, filetypes=self.filetypes)
        if path:
            self._var.set(path)
