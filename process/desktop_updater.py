"""Check / apply ASF Desktop updates from GitHub Releases."""
from __future__ import annotations

import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

from domain.version import __version__

# Ajuste quando o repositório público existir
GITHUB_REPO = os.environ.get("ASF_DESKTOP_REPO", "KevenCastilho/ASF-Desktop")
API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def check_latest() -> dict:
    """Return {tag, url, notes, newer: bool} or raise."""
    req = Request(API, headers={"Accept": "application/vnd.github+json", "User-Agent": "ASF-Desktop"})
    with urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    tag = (data.get("tag_name") or data.get("name") or "").lstrip("v")
    assets = data.get("assets") or []
    url = ""
    for a in assets:
        name = (a.get("name") or "").lower()
        if name.endswith(".zip") or "asfdesktop" in name or "asf-desktop" in name:
            url = a.get("browser_download_url") or ""
            break
    if not url and assets:
        url = assets[0].get("browser_download_url") or ""
    newer = _is_newer(tag, __version__)
    return {
        "tag": tag,
        "url": url,
        "notes": (data.get("body") or "")[:800],
        "newer": newer,
        "current": __version__,
    }


def _is_newer(remote: str, local: str) -> bool:
    def parts(v: str) -> list[int]:
        out = []
        for p in v.replace("-", ".").split("."):
            try:
                out.append(int("".join(ch for ch in p if ch.isdigit()) or "0"))
            except ValueError:
                out.append(0)
        return out or [0]

    r, l = parts(remote), parts(local)
    n = max(len(r), len(l))
    r += [0] * (n - len(r))
    l += [0] * (n - len(l))
    return r > l


def download_release(url: str, dest_dir: Path, on_progress: Callable[[str, float], None] | None = None) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "ASFDesktop-update.zip"
    if on_progress:
        on_progress("Baixando…", 0.1)
    req = Request(url, headers={"User-Agent": "ASF-Desktop"})
    with urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        with open(zip_path, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if total and on_progress:
                    on_progress("Baixando…", 0.1 + 0.8 * (got / total))
    if on_progress:
        on_progress("Pronto", 1.0)
    return zip_path
