"""Download ASF stable release from GitHub."""
from __future__ import annotations

import json
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

GITHUB_API = "https://api.github.com/repos/JustArchiNET/ArchiSteamFarm/releases/latest"


def _asset_name() -> str:
    if os.name == "nt":
        return "ASF-win-x64.zip"
    # Linux generic
    return "ASF-linux-x64.zip"


def fetch_latest_asset_url() -> tuple[str, str]:
    """Return (version_tag, download_url)."""
    req = Request(GITHUB_API, headers={"Accept": "application/vnd.github+json", "User-Agent": "ASF-Desktop"})
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    tag = data.get("tag_name") or data.get("name") or "unknown"
    want = _asset_name().lower()
    for asset in data.get("assets") or []:
        name = (asset.get("name") or "").lower()
        if name == want or want in name:
            return tag, asset["browser_download_url"]
    # fallback: first zip
    for asset in data.get("assets") or []:
        if str(asset.get("name", "")).endswith(".zip"):
            return tag, asset["browser_download_url"]
    raise RuntimeError("Nenhum asset zip encontrado no release mais recente do ASF.")


def download_and_extract(
    dest_dir: Path,
    on_progress: Callable[[str, float], None] | None = None,
) -> Path:
    """
    Baixa ASF stable e extrai em dest_dir.
    Retorna caminho do executável (ou pasta raiz).
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    if on_progress:
        on_progress("Consultando GitHub…", 0.05)
    tag, url = fetch_latest_asset_url()
    if on_progress:
        on_progress(f"Baixando {tag}…", 0.1)
    zip_path = dest_dir / "ASF-download.zip"
    req = Request(url, headers={"User-Agent": "ASF-Desktop"})
    with urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        with open(zip_path, "wb") as f:
            while True:
                chunk = resp.read(1024 * 64)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if total and on_progress:
                    on_progress(f"Baixando {tag}…", 0.1 + 0.7 * (got / total))
    if on_progress:
        on_progress("Extraindo…", 0.85)
    extract_to = dest_dir / tag
    if extract_to.exists():
        shutil.rmtree(extract_to, ignore_errors=True)
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    try:
        zip_path.unlink()
    except OSError:
        pass
    # find executable
    for name in ("ArchiSteamFarm.exe", "ArchiSteamFarm"):
        for p in extract_to.rglob(name):
            if p.is_file():
                if on_progress:
                    on_progress("Concluído", 1.0)
                return p
    if on_progress:
        on_progress("Concluído (exe não localizado — use a pasta)", 1.0)
    return extract_to
