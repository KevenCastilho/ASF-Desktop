"""
Tipos oficiais de input do ASF (Headless / comando `input`).

Fonte: wiki Commands — input <Bots> <Type> <Value>
Baseline típica stable 6.x (ajustar após asf-api-baseline real).

O Desktop tenta detectar o tipo pela mensagem do GetUserInput / log.
"""
from __future__ import annotations

import re

# Ordem de tentativa quando o tipo não é óbvio na mensagem
DEFAULT_TRY_ORDER = [
    "TwoFactorAuthentication",
    "SteamGuard",
    "LoginConfirmationRequired",
    "SteamParentalCode",
    "DeviceConfirmation",
]

# Padrões mensagem → tipo
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"two[\s-]*factor|2fa|authenticator|mobile", re.I), "TwoFactorAuthentication"),
    (re.compile(r"steam\s*guard|email\s*code|e-?mail", re.I), "SteamGuard"),
    (re.compile(r"parental|family\s*view", re.I), "SteamParentalCode"),
    (re.compile(r"device\s*confirm|confirmação\s*de\s*dispositivo", re.I), "DeviceConfirmation"),
    (re.compile(r"login\s*confirm|confirmação\s*de\s*login", re.I), "LoginConfirmationRequired"),
    (re.compile(r"password|senha", re.I), "Password"),
]


def detect_input_type(message: str) -> str | None:
    msg = message or ""
    for pat, typ in _PATTERNS:
        if pat.search(msg):
            return typ
    return None


def types_to_try(message: str) -> list[str]:
    detected = detect_input_type(message)
    if detected:
        rest = [t for t in DEFAULT_TRY_ORDER if t != detected]
        return [detected] + rest
    return list(DEFAULT_TRY_ORDER)
