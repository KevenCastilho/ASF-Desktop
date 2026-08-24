"""Console widget — MineRun-grade abstraction over tk.Text."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from ui.components.chrome import FilterBtn, FlatScrollbar, HoverBtn
from ui.theme import FONT_MONO, FONT_SMALL, FONT_UI_BOLD


_LEVELS = [
    ("INFO", "#58a6ff"),
    ("WARN", "#d29922"),
    ("ERROR", "#f85149"),
    ("FATAL", "#f85149"),
    ("DEBUG", "#8b949e"),
    ("TRACE", "#6e7681"),
]


class ConsoleWidget(tk.Frame):
    def __init__(self, parent, colors: dict, on_command: Callable[[str], None] | None = None, **kw):
        super().__init__(parent, bg=colors["bg"], **kw)
        self.colors = colors
        self.on_command = on_command
        self._lines: list[dict] = []
        self._filters: dict[str, FilterBtn] = {}
        self._search = ""
        self._search_hits: list[str] = []
        self._search_idx = -1
        self._autoscroll = tk.BooleanVar(value=True)
        self._build()

    def _build(self) -> None:
        c = self.colors
        # Header
        hdr = tk.Frame(self, bg=c["card"])
        hdr.pack(fill="x")
        row = tk.Frame(hdr, bg=c["card"])
        row.pack(fill="x", padx=10, pady=6)
        tk.Label(row, text="Console", bg=c["card"], fg=c["fg"], font=FONT_UI_BOLD).pack(side="left")
        tk.Checkbutton(
            row, text="Auto-scroll", variable=self._autoscroll,
            bg=c["card"], fg=c["muted"], selectcolor=c["card"],
            activebackground=c["card"], font=FONT_SMALL, bd=0, cursor="hand2",
        ).pack(side="right")
        # search nav
        HoverBtn(row, "▼", color=c["card"], fg=c["muted"], padx=5, pady=1,
                 font=FONT_SMALL, command=lambda: self._search_nav(1)).pack(side="right", padx=1)
        HoverBtn(row, "▲", color=c["card"], fg=c["muted"], padx=5, pady=1,
                 font=FONT_SMALL, command=lambda: self._search_nav(-1)).pack(side="right", padx=1)
        self._sv = tk.StringVar()
        self._sv.trace_add("write", lambda *_: self._on_search())
        e = tk.Entry(
            row, textvariable=self._sv, width=18, bg=c["input"], fg=c["fg"],
            insertbackground=c["accent"], relief="flat", font=FONT_SMALL,
            highlightthickness=1, highlightbackground=c["border"], highlightcolor=c["accent"],
        )
        e.pack(side="right", padx=6, ipady=3)
        tk.Label(row, text="Filtrar:", bg=c["card"], fg=c["muted"], font=FONT_SMALL).pack(side="left", padx=(16, 6))
        for name, color in _LEVELS:
            fb = FilterBtn(row, name, color, on_toggle=lambda *_: self._rerender())
            fb.pack(side="left", padx=2)
            self._filters[name] = fb

        tk.Frame(self, bg=c["border"], height=1).pack(fill="x")

        # Text + flat scrollbar
        tw = tk.Frame(self, bg=c["input"])
        tw.pack(fill="both", expand=True)
        self._text = tk.Text(
            tw, state="disabled", bg=c["input"], fg=c["fg"], font=FONT_MONO,
            relief="flat", bd=0, wrap="word", insertbackground=c["accent"],
            highlightthickness=0, padx=12, pady=8,
            selectbackground="#1e3a5f", selectforeground=c["fg"],
        )
        self._text.pack(side="left", fill="both", expand=True)
        sb = FlatScrollbar(tw, command=self._text.yview)
        sb.pack(side="right", fill="y", padx=(2, 4), pady=4)
        self._text.configure(yscrollcommand=sb.set)

        for name, color in _LEVELS:
            self._text.tag_config(name, foreground=color)
        self._text.tag_config("src", foreground="#3d4470")
        self._text.tag_config("search_hit", background="#854d0e", foreground="#fef9c3")
        self._text.tag_config("search_current", background="#f59e0b", foreground="#0d0f18")
        self._text.tag_config("CMD", foreground=c["accent"], font=("Consolas", 9, "bold"))

        self._text.bind("<Button-3>", self._ctx)
        self._text.bind("<Button-2>", self._ctx)

        # Command bar glued
        tk.Frame(self, bg=c["border"], height=1).pack(fill="x")
        bar = tk.Frame(self, bg=c["header"], pady=8)
        bar.pack(fill="x")
        tk.Label(bar, text=">", bg=c["header"], fg=c["accent"],
                 font=("Consolas", 12, "bold")).pack(side="left", padx=(14, 8))
        self.cmd = tk.Entry(
            bar, bg=c["input"], fg=c["fg"], insertbackground=c["accent"],
            relief="flat", font=FONT_MONO,
            highlightthickness=1, highlightbackground=c["border"], highlightcolor=c["accent"],
        )
        self.cmd.pack(side="left", fill="x", expand=True, ipady=6)
        self.cmd.bind("<Return>", lambda e: self._send())
        HoverBtn(bar, "Enviar", color=c["accent"], fg="#0d1117", command=self._send).pack(
            side="right", padx=(8, 10),
        )
        HoverBtn(bar, "Limpar", color=c["card"], fg=c["fg"], command=self.clear).pack(
            side="right",
        )

    def append_line(self, text: str, level: str = "INFO", source: str = "") -> None:
        entry = {"text": text, "level": level.upper(), "source": source}
        if entry["level"] == "WARNING":
            entry["level"] = "WARN"
        self._lines.append(entry)
        if len(self._lines) > 8000:
            self._lines = self._lines[-6000:]
        if self._visible(entry):
            self._append(entry)

    def clear(self) -> None:
        self._lines.clear()
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")

    def load_lines(self, lines: list[str]) -> None:
        self.clear()
        for line in lines:
            lv = "INFO"
            for cand in ("FATAL", "ERROR", "WARN", "WARNING", "DEBUG", "TRACE", "INFO"):
                if f"|{cand}|" in line.upper() or f"|{cand}|" in line:
                    lv = "WARN" if cand == "WARNING" else cand
                    break
            self.append_line(line, lv)

    def _visible(self, entry: dict) -> bool:
        lv = entry["level"]
        fb = self._filters.get(lv)
        if fb and not fb.active:
            return False
        if self._search and self._search.lower() not in entry["text"].lower():
            return False
        return True

    def _append(self, entry: dict) -> None:
        t = self._text
        t.configure(state="normal")
        if entry["source"]:
            t.insert("end", f"[{entry['source']}] ", "src")
        lv = entry["level"] if entry["level"] in dict(_LEVELS) else "INFO"
        t.insert("end", entry["text"] + "\n", lv)
        t.configure(state="disabled")
        if self._autoscroll.get():
            t.see("end")
        if self._search:
            self._hl_in_last(entry["text"])

    def _rerender(self) -> None:
        t = self._text
        t.configure(state="normal")
        t.delete("1.0", "end")
        for e in self._lines:
            if self._visible(e):
                if e["source"]:
                    t.insert("end", f"[{e['source']}] ", "src")
                lv = e["level"] if e["level"] in dict(_LEVELS) else "INFO"
                t.insert("end", e["text"] + "\n", lv)
        t.configure(state="disabled")
        if self._search:
            self._hl_all()
        if self._autoscroll.get():
            t.see("end")

    def _on_search(self) -> None:
        self._search = self._sv.get().strip()
        self._rerender()

    def _hl_all(self) -> None:
        t = self._text
        t.tag_remove("search_hit", "1.0", "end")
        t.tag_remove("search_current", "1.0", "end")
        self._search_hits = []
        self._search_idx = -1
        if not self._search:
            return
        start = "1.0"
        while True:
            pos = t.search(self._search, start, stopindex="end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(self._search)}c"
            t.tag_add("search_hit", pos, end)
            self._search_hits.append(pos)
            start = end

    def _hl_in_last(self, text: str) -> None:
        if self._search.lower() not in text.lower():
            return
        t = self._text
        ln = int(t.index("end-1c").split(".")[0])
        st = f"{ln}.0"
        while True:
            pos = t.search(self._search, st, stopindex=f"{ln}.end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(self._search)}c"
            t.tag_add("search_hit", pos, end)
            st = end

    def _search_nav(self, delta: int) -> None:
        if not self._search_hits:
            return
        n = len(self._search_hits)
        t = self._text
        if 0 <= self._search_idx < n:
            cur = self._search_hits[self._search_idx]
            t.tag_remove("search_current", cur, f"{cur}+{len(self._search)}c")
            t.tag_add("search_hit", cur, f"{cur}+{len(self._search)}c")
        self._search_idx = (self._search_idx + delta) % n
        pos = self._search_hits[self._search_idx]
        t.tag_remove("search_hit", pos, f"{pos}+{len(self._search)}c")
        t.tag_add("search_current", pos, f"{pos}+{len(self._search)}c")
        t.see(pos)

    def _ctx(self, e) -> None:
        try:
            sel = self._text.get("sel.first", "sel.last")
        except tk.TclError:
            sel = ""
        menu = tk.Menu(self, tearoff=0, bg=self.colors["card"], fg=self.colors["fg"],
                       activebackground=self.colors["card_hover"], bd=0)
        if sel:
            menu.add_command(label="Copiar", command=lambda: self.clipboard_clear() or self.clipboard_append(sel))
        menu.add_command(label="Limpar console", command=self.clear)
        try:
            menu.tk_popup(e.x_root, e.y_root)
        finally:
            menu.grab_release()

    def _send(self) -> None:
        cmd = self.cmd.get().strip()
        if not cmd:
            return
        self.cmd.delete(0, "end")
        self.append_line(f"> {cmd}", "CMD", "Desktop")
        if self.on_command:
            self.on_command(cmd)
