#!/usr/bin/env python3
"""ASF Desktop v2 — single entrypoint."""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _log_crash(msg: str) -> Path:
    log_dir = Path.home() / ".asf-desktop"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        log_dir = ROOT
    path = log_dir / "last-crash.txt"
    try:
        path.write_text(msg, encoding="utf-8")
    except Exception:
        pass
    return path


def _show_error(title: str, message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        print(message, file=sys.stderr)


def main() -> int:
    from bootstrap import bootstrap

    bootstrap()

    try:
        from persistence.single_instance import ensure_single_instance
        from persistence.settings import SettingsStore
        from process.manager import AsfProcessManager
        from integration.ipc_client import IpcClient
        from ui.app import AsfDesktopApp
    except Exception:
        tb = traceback.format_exc()
        path = _log_crash(tb)
        _show_error(
            "ASF Desktop — falha ao carregar",
            f"Não foi possível iniciar o aplicativo.\n\n"
            f"Detalhes gravados em:\n{path}\n\n{tb[-800:]}",
        )
        return 1

    try:
        settings = SettingsStore()
        settings.load()
    except Exception:
        tb = traceback.format_exc()
        path = _log_crash(tb)
        _show_error("ASF Desktop", f"Erro nas configurações.\n{path}\n\n{tb[-500:]}")
        return 1

    if not ensure_single_instance(settings.config_dir):
        _show_error(
            "ASF Desktop",
            "O ASF Desktop já está em execução.\n\n"
            "Se não houver janela aberta, encerre o processo "
            "no Gerenciador de Tarefas ou apague o arquivo "
            f"lock em:\n{settings.config_dir / 'asf-desktop.lock'}",
        )
        return 1

    process_mgr = None
    try:
        process_mgr = AsfProcessManager(settings)
        ipc = IpcClient(settings)
        app = AsfDesktopApp(settings=settings, process_mgr=process_mgr, ipc=ipc)
        app.run()
    except Exception:
        tb = traceback.format_exc()
        path = _log_crash(tb)
        _show_error(
            "ASF Desktop — erro",
            f"O programa fechou com erro.\n\nLog:\n{path}\n\n{tb[-900:]}",
        )
        return 1
    finally:
        if process_mgr is not None:
            try:
                process_mgr.stop(reason="app_exit")
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
