"""Check / apply ASF Desktop updates from GitHub Releases.

Repo oficial: https://github.com/KevenCastilho/ASF-Desktop
"""
from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

from domain.version import __version__

# Repositório público do ASF Desktop (override: env ASF_DESKTOP_REPO)
GITHUB_OWNER = "KevenCastilho"
GITHUB_NAME = "ASF-Desktop"
GITHUB_REPO = os.environ.get("ASF_DESKTOP_REPO", f"{GITHUB_OWNER}/{GITHUB_NAME}")
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
API_RELEASES = f"https://api.github.com/repos/{GITHUB_REPO}/releases"


def _ua_headers() -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ASF-Desktop-Updater",
    }


def check_latest() -> dict:
    """Return {tag, url, notes, newer, current, repo_url, html_url}."""
    req = Request(API_LATEST, headers=_ua_headers())
    try:
        with urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        # Sem release ainda: tenta listar releases; se vazio, informa repo
        try:
            req2 = Request(API_RELEASES, headers=_ua_headers())
            with urlopen(req2, timeout=20) as resp:
                lst = json.loads(resp.read().decode())
            if not lst:
                return {
                    "tag": "",
                    "url": "",
                    "notes": (
                        f"Nenhum release publicado ainda em {GITHUB_URL}/releases\n"
                        "Publique um Release com asset .zip para o auto-update funcionar."
                    ),
                    "newer": False,
                    "current": __version__,
                    "repo_url": GITHUB_URL,
                    "html_url": f"{GITHUB_URL}/releases",
                }
            data = lst[0]
        except Exception:
            raise e

    tag = (data.get("tag_name") or data.get("name") or "").lstrip("v")
    html_url = data.get("html_url") or f"{GITHUB_URL}/releases"
    assets = data.get("assets") or []
    url = ""
    for a in assets:
        name = (a.get("name") or "").lower()
        if name.endswith(".zip") or "asfdesktop" in name or "asf-desktop" in name:
            url = a.get("browser_download_url") or ""
            break
    if not url and assets:
        url = assets[0].get("browser_download_url") or ""
    # Fallback: zipball do tag (código-fonte do release)
    if not url and tag:
        url = data.get("zipball_url") or f"https://api.github.com/repos/{GITHUB_REPO}/zipball/{data.get('tag_name') or tag}"

    newer = _is_newer(tag, __version__) if tag else False
    return {
        "tag": tag,
        "url": url,
        "notes": (data.get("body") or "")[:800],
        "newer": newer,
        "current": __version__,
        "repo_url": GITHUB_URL,
        "html_url": html_url,
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
    req = Request(url, headers=_ua_headers())
    with urlopen(req, timeout=180) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        with open(zip_path, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if on_progress and total:
                    on_progress("Baixando…", min(0.95, got / total))
    if on_progress:
        on_progress("Concluído", 1.0)
    return zip_path


def extract_hint(zip_path: Path) -> str:
    """Lista nomes de topo do zip para ajudar o usuário."""
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            names = z.namelist()[:8]
        return "\n".join(names)
    except Exception:
        return ""
