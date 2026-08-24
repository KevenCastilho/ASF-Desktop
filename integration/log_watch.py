"""Detect ASF GetUserInput prompts from stdout lines."""
from __future__ import annotations

import re
from dataclasses import dataclass

from integration.input_types import detect_input_type


@dataclass
class InputRequest:
    bot_name: str
    message: str
    raw: str
    input_type: str | None = None


_GET_INPUT = re.compile(r"GetUserInput\(\)\s*(.*)$", re.I)
_BOT_HINT = re.compile(r"<([^>]+)>")
# NLog-style: BotName | ... GetUserInput
_BOT_PREFIX = re.compile(r"\|\s*([A-Za-z0-9_]+)\s*\|")


def parse_input_line(line: str) -> InputRequest | None:
    if "GetUserInput()" not in line and "GetUserInput" not in line:
        return None
    if "Entrada:" in line or "Input:" in line or "answered" in line.lower():
        return None
    m = _GET_INPUT.search(line)
    msg = (m.group(1).strip() if m else "").strip()
    if not msg:
        msg = "O ASF está pedindo uma entrada (Steam Guard / 2FA / confirmação)."
    bot = ""
    bm = _BOT_HINT.search(line)
    if bm:
        bot = bm.group(1)
    if not bot:
        bp = _BOT_PREFIX.findall(line)
        if bp:
            # último token tipo nome de bot (heurística)
            for cand in reversed(bp):
                if cand.upper() not in ("INFO", "WARN", "ERROR", "DEBUG", "TRACE", "FATAL", "ASF"):
                    bot = cand
                    break
    typ = detect_input_type(msg) or detect_input_type(line)
    return InputRequest(bot_name=bot, message=msg, raw=line, input_type=typ)
