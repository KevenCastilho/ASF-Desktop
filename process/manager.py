"""ASF external process lifecycle."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Callable

from security.redaction import redact
from integration.log_watch import parse_input_line
from integration.asf_config import read_global, write_global


class AsfProcessManager:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.proc: subprocess.Popen | None = None
        self._reader_thread: threading.Thread | None = None
        self._stop_reader = threading.Event()
        ret = 500
        try:
            ret = int(self.settings.get("activity_retention") or 500)
        except Exception:
            pass
        self.log_lines: deque[str] = deque(maxlen=max(200, ret * 2))
        self._listeners: list[Callable[[str], None]] = []
        self._input_listeners: list[Callable] = []
        self._lock = threading.Lock()

    def add_log_listener(self, cb: Callable[[str], None]) -> None:
        self._listeners.append(cb)

    def add_input_listener(self, cb) -> None:
        self._input_listeners.append(cb)

    def is_running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def resolve_executable(self) -> Path | None:
        raw = (self.settings.get("asf_path") or "").strip()
        if not raw:
            return None
        p = Path(raw)
        if p.is_file():
            return p
        if p.is_dir():
            for name in ("ArchiSteamFarm.exe", "ArchiSteamFarm", "ArchiSteamFarm.dll"):
                cand = p / name
                if cand.is_file():
                    return cand
        return None

    def validate_install(self, path: Path | None = None) -> tuple[bool, str]:
        exe = path or self.resolve_executable()
        if exe is None:
            return False, "Caminho do ASF não configurado."
        if not exe.is_file():
            return False, f"Executável não encontrado: {exe}"
        # Minimal footprint of a real ASF tree
        root = exe.parent
        if not (root / "config").exists() and not (root / "plugins").exists():
            # still allow bare exe for flexibility
            pass
        return True, str(exe)

    def start(self) -> tuple[bool, str]:
        if self.is_running():
            return True, "ASF já está em execução."
        ok, msg = self.validate_install()
        if not ok:
            return False, msg
        exe = self.resolve_executable()
        assert exe is not None
        workdir = exe.parent

        creationflags = 0
        startupinfo = None
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            startupinfo = subprocess.STARTUPINFO()
            if hasattr(subprocess, "STARTF_USESHOWWINDOW"):
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0

        try:
            # Prefer Headless so GetUserInput goes through IPC-friendly path
            try:
                ap = str(exe)
                g = read_global(ap)
                if not g.get("Headless"):
                    g["Headless"] = True
                    if "IPC" not in g:
                        g["IPC"] = True
                    write_global(ap, g)
            except Exception:
                pass
            self.proc = subprocess.Popen(
                [str(exe)],
                cwd=str(workdir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                startupinfo=startupinfo,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as e:
            return False, f"Falha ao iniciar ASF: {e}"

        self._stop_reader.clear()
        self._reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader_thread.start()
        return True, "ASF iniciado."

    def _read_stdout(self) -> None:
        proc = self.proc
        if not proc or not proc.stdout:
            return
        try:
            for line in proc.stdout:
                if self._stop_reader.is_set():
                    break
                line = line.rstrip("\n\r")
                safe = redact(line)
                with self._lock:
                    self.log_lines.append(safe)
                for cb in list(self._listeners):
                    try:
                        cb(safe)
                    except Exception:
                        pass
                req = parse_input_line(safe)
                if req:
                    for cb in list(self._input_listeners):
                        try:
                            cb(req)
                        except Exception:
                            pass
        except Exception:
            pass

    def stop(self, reason: str = "") -> None:
        """Encerra rápido — UI não deve esperar vários segundos."""
        self._stop_reader.set()
        proc = self.proc
        self.proc = None
        if proc is None:
            return
        if proc.poll() is None:
            try:
                # IPC Exit já pode ter sido pedido; aqui só garante processo
                if os.name == "nt":
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=1.2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    try:
                        proc.wait(timeout=0.8)
                    except subprocess.TimeoutExpired:
                        pass
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    def get_recent_logs(self, n: int = 200) -> list[str]:
        with self._lock:
            return list(self.log_lines)[-n:]
