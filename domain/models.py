"""Domain models — no I/O."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConnectionState(str, Enum):
    NO_INSTALL = "NoInstall"
    INVALID_INSTALL = "InvalidInstall"
    STOPPED = "Stopped"
    STARTING = "Starting"
    IPC_DOWN = "IpcDown"
    UNAUTHORIZED = "Unauthorized"
    CONNECTED = "Connected"
    RECONNECTING = "Reconnecting"
    ERROR = "Error"


@dataclass
class BotCardData:
    name: str
    status: str  # online | paused | stopped | error
    subtitle: str = ""
    detail: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


def human_status(bot_connected: bool, farming: bool, keep_running: bool = True) -> str:
    if bot_connected and farming:
        return "online"
    if bot_connected:
        return "online"
    if keep_running:
        return "paused"
    return "stopped"
