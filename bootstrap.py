"""
Bootstrap — splash + auto-install de dependências (apenas stdlib).
Mesmo espírito do MineRun: o usuário não roda pip na mão.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
import tkinter as tk
import tkinter.ttk as ttk

# módulo importável -> pacote pip
_REQUIRED = {
    "psutil": "psutil",
    "PIL": "Pillow",  # ícones Lucide + tray
}

_OPTIONAL = {
    "pystray": "pystray",
}


def _check_missing(mapping: dict[str, str]) -> list[str]:
    missing: list[str] = []
    for mod, pkg in mapping.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    return missing


def _pip_install(pkg: str) -> str | None:
    base = [sys.executable, "-m", "pip", "install", "--quiet", pkg]
    strategies = [
        base,
        base + ["--break-system-packages"],
        base + ["--user"],
    ]
    last_err = ""
    for cmd in strategies:
        try:
            subprocess.check_call(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
            )
            return None
        except subprocess.CalledProcessError as e:
            last_err = (e.stderr or b"").decode(errors="replace").strip()
        except Exception as e:
            last_err = str(e)
    return last_err or f"falha ao instalar {pkg}"


def _run_splash(jobs: list[tuple[str, str]]) -> list[str]:
    """
    jobs: lista (rótulo, pacote_pip)
    Sempre mostra splash (feedback visual de boot).
    """
    _BG = "#0d1117"
    _BG_HDR = "#161b22"
    _BORDER = "#30363d"
    _FG = "#e6edf3"
    _MUTED = "#8b949e"
    _GREEN = "#3fb950"
    _RED = "#f85149"
    _ACCENT = "#3fb950"

    W, H = 420, 220
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg=_BORDER)
    try:
        splash.attributes("-topmost", True)
    except tk.TclError:
        pass
    sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
    splash.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")

    inner = tk.Frame(splash, bg=_BG)
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    hdr = tk.Frame(inner, bg=_BG_HDR)
    hdr.pack(fill="x")
    tk.Label(
        hdr, text="ASF Desktop", bg=_BG_HDR, fg=_FG,
        font=("Segoe UI", 14, "bold"),
    ).pack(side="left", padx=16, pady=12)
    tk.Label(
        hdr, text="v0.1", bg=_BG_HDR, fg=_MUTED, font=("Segoe UI", 9),
    ).pack(side="right", padx=16)

    body = tk.Frame(inner, bg=_BG)
    body.pack(fill="both", expand=True, padx=20, pady=12)

    status_var = tk.StringVar(value="Iniciando…")
    status_lbl = tk.Label(
        body, textvariable=status_var, bg=_BG, fg=_MUTED,
        font=("Segoe UI", 10), anchor="w",
    )
    status_lbl.pack(fill="x", pady=(8, 12))

    style = ttk.Style(splash)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "S.Horizontal.TProgressbar",
        troughcolor=_BG_HDR,
        background=_ACCENT,
        bordercolor=_BORDER,
        lightcolor=_ACCENT,
        darkcolor=_ACCENT,
    )
    pb = ttk.Progressbar(
        body, mode="indeterminate", length=360, style="S.Horizontal.TProgressbar"
    )
    pb.pack(pady=(0, 8))
    pb.start(12)

    tk.Frame(inner, bg=_BORDER, height=1).pack(fill="x")
    tk.Label(
        inner, text="Preparando ambiente · sem terminal",
        bg=_BG_HDR, fg=_MUTED, font=("Segoe UI", 8),
    ).pack(fill="x", pady=6)

    splash.update_idletasks()
    splash.update()

    failed: list[str] = []

    if not jobs:
        status_var.set("Tudo pronto.")
        status_lbl.config(fg=_GREEN)
        splash.update()
        splash.after(900, splash.destroy)
        splash.mainloop()
        return failed

    total = len(jobs)
    for i, (label, pkg) in enumerate(jobs, 1):
        status_var.set(f"{label} ({i}/{total}): {pkg}…")
        status_lbl.config(fg=_MUTED)
        splash.update()
        err = _pip_install(pkg)
        if err:
            failed.append(pkg)
            status_var.set(f"Não foi possível instalar {pkg}.")
            status_lbl.config(fg=_RED)
        else:
            status_var.set(f"{pkg} ok.")
            status_lbl.config(fg=_GREEN)
        splash.update()
        splash.after(250)
        splash.update()

    pb.stop()
    if failed:
        status_var.set(
            "Algumas dependências opcionais falharam — o app continua."
        )
        status_lbl.config(fg=_RED)
        splash.after(1800, splash.destroy)
    else:
        status_var.set("Tudo pronto!")
        status_lbl.config(fg=_GREEN)
        splash.after(700, splash.destroy)

    splash.mainloop()
    return failed


def bootstrap() -> None:
    missing_req = _check_missing(_REQUIRED)
    missing_opt = _check_missing(_OPTIONAL)
    jobs: list[tuple[str, str]] = []
    for pkg in missing_req:
        jobs.append(("Instalando dependência", pkg))
    for pkg in missing_opt:
        jobs.append(("Instalando opcional (tray)", pkg))
    # Sempre mostra splash (mesmo com lista vazia)
    failed = _run_splash(jobs)
    for pkg in failed:
        if pkg in _REQUIRED.values():
            print(
                f"[ASF Desktop] AVISO: '{pkg}' não instalado. "
                f"Recursos limitados.",
                file=sys.stderr,
            )
