"""Redact secrets from logs and UI text."""
from __future__ import annotations

import re

_PATTERNS = [
    re.compile(r"(SteamPassword\"\s*:\s*\")([^\"]+)(\")", re.I),
    re.compile(r"(password[\"']?\s*[:=]\s*[\"'])([^\"']+)([\"'])", re.I),
    re.compile(r"(IPCPassword\"\s*:\s*\")([^\"]+)(\")", re.I),
    re.compile(r"(Authentication:\s*)(\S+)", re.I),
    re.compile(r"(Entrada:\s*)(\S+)", re.I),  # GetUserInput echo
]


def redact(text: str) -> str:
    if not text:
        return text
    out = text
    for pat in _PATTERNS:
        out = pat.sub(r"\1***\3" if pat.groups == 3 else r"\1***", out)
    # Generic long tokens
    out = re.sub(r"\b[A-Za-z0-9_-]{32,}\b", "***", out)
    return out
