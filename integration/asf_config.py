"""Read/write ASF config files (never log secrets)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def asf_root_from_path(asf_path: str) -> Path | None:
    if not asf_path:
        return None
    p = Path(asf_path)
    if p.is_file():
        return p.parent
    if p.is_dir():
        return p
    return None


def config_dir(asf_path: str) -> Path | None:
    root = asf_root_from_path(asf_path)
    if not root:
        return None
    d = root / "config"
    return d if d.is_dir() or root.exists() else None


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")


def read_ipc_password(asf_path: str) -> str:
    d = config_dir(asf_path)
    if not d:
        return ""
    asf_json = d / "ASF.json"
    data = read_json(asf_json)
    pwd = data.get("IPCPassword")
    return str(pwd) if pwd else ""


def list_bot_names(asf_path: str) -> list[str]:
    d = config_dir(asf_path)
    if not d or not d.is_dir():
        return []
    names = []
    for p in sorted(d.glob("*.json")):
        if p.name.upper() == "ASF.JSON":
            continue
        names.append(p.stem)
    return names


def read_bot(asf_path: str, name: str) -> dict[str, Any]:
    d = config_dir(asf_path)
    if not d:
        return {}
    return read_json(d / f"{name}.json")


def write_bot(asf_path: str, name: str, data: dict[str, Any]) -> Path:
    d = config_dir(asf_path)
    if not d:
        root = asf_root_from_path(asf_path)
        d = (root / "config") if root else Path("config")
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{name}.json"
    write_json(path, data)
    return path


def read_global(asf_path: str) -> dict[str, Any]:
    d = config_dir(asf_path)
    if not d:
        return {}
    return read_json(d / "ASF.json")


def write_global(asf_path: str, data: dict[str, Any]) -> Path:
    d = config_dir(asf_path)
    if not d:
        root = asf_root_from_path(asf_path)
        d = (root / "config") if root else Path("config")
    d.mkdir(parents=True, exist_ok=True)
    path = d / "ASF.json"
    write_json(path, data)
    return path


def delete_bot_file(asf_path: str, name: str) -> bool:
    d = config_dir(asf_path)
    if not d:
        return False
    path = d / f"{name}.json"
    if path.is_file():
        path.unlink()
        return True
    return False
