"""Single-instance lock — tolerante a lock órfão após crash."""
from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path

_lock_fh = None


def ensure_single_instance(config_dir: Path) -> bool:
    """Return True if this process owns the lock."""
    global _lock_fh
    config_dir.mkdir(parents=True, exist_ok=True)
    lock_path = config_dir / "asf-desktop.lock"

    if os.name == "nt":
        return _lock_windows(lock_path)
    return _lock_unix(lock_path)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_pid(lock_path: Path) -> int:
    try:
        text = lock_path.read_text(encoding="utf-8", errors="ignore").strip()
        return int("".join(ch for ch in text if ch.isdigit()) or "0")
    except Exception:
        return 0


def _lock_windows(lock_path: Path) -> bool:
    global _lock_fh
    import msvcrt

    # Se lock antigo e processo morto, remove
    if lock_path.exists():
        pid = _read_pid(lock_path)
        if pid and not _pid_alive(pid):
            try:
                lock_path.unlink(missing_ok=True)
            except OSError:
                pass

    try:
        _lock_fh = open(lock_path, "a+b")
        _lock_fh.seek(0)
        try:
            msvcrt.locking(_lock_fh.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            # outra instância viva
            try:
                _lock_fh.close()
            except Exception:
                pass
            _lock_fh = None
            return False
        _lock_fh.seek(0)
        _lock_fh.truncate()
        _lock_fh.write(str(os.getpid()).encode())
        _lock_fh.flush()
    except OSError:
        # não bloquear o app por falha de lock
        return True

    atexit.register(_release)
    return True


def _lock_unix(lock_path: Path) -> bool:
    global _lock_fh
    import fcntl

    if lock_path.exists():
        pid = _read_pid(lock_path)
        if pid and not _pid_alive(pid):
            try:
                lock_path.unlink(missing_ok=True)
            except OSError:
                pass

    try:
        _lock_fh = open(lock_path, "a+")
        fcntl.flock(_lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_fh.seek(0)
        _lock_fh.truncate()
        _lock_fh.write(str(os.getpid()))
        _lock_fh.flush()
    except OSError:
        return False

    atexit.register(_release)
    return True


def _release() -> None:
    global _lock_fh
    try:
        if _lock_fh:
            _lock_fh.close()
    except Exception:
        pass
    _lock_fh = None
