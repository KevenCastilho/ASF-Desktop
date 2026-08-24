"""
Schema dinâmico via /Api/Type e /Api/Structure (quando a build expõe).

Fallback: campos conhecidos Simple + dump do JSON em disco (Advanced).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from integration.ipc_client import IpcClient


# Tipos curtos usados na UI
FieldKind = str  # bool | str | int | number | json


@dataclass
class SchemaField:
    name: str
    kind: FieldKind
    description: str = ""


# Fallback se Type/Structure indisponível
BOT_SIMPLE_FIELDS: list[tuple[str, FieldKind]] = [
    ("Enabled", "bool"),
    ("SteamLogin", "str"),
    ("SteamPassword", "str"),
    ("SteamParentalCode", "str"),
    ("OnlinePreferences", "str"),
    ("HoursUntilCardDrops", "int"),
]

ASF_SIMPLE_FIELDS: list[tuple[str, FieldKind]] = [
    ("IPC", "bool"),
    ("IPCPassword", "str"),
    ("Headless", "bool"),
    ("AutoRestart", "bool"),
    ("UpdatePeriod", "int"),
    ("Blacklist", "json"),
]

# Type names tentados (builds 6.x variam namespaces)
_BOT_TYPE_CANDIDATES = [
    "ArchiSteamFarm.Steam.Data.BotConfig",
    "ArchiSteamFarm.Steam.Storage.BotConfig",
    "BotConfig",
]
_ASF_TYPE_CANDIDATES = [
    "ArchiSteamFarm.Storage.GlobalConfig",
    "ArchiSteamFarm.Steam.Data.GlobalConfig",
    "GlobalConfig",
]


def _kind_from_type_name(type_name: str) -> FieldKind:
    t = (type_name or "").lower()
    if "bool" in t:
        return "bool"
    if any(x in t for x in ("int", "uint", "byte", "long", "short")):
        return "int"
    if any(x in t for x in ("double", "float", "decimal", "single")):
        return "number"
    if any(x in t for x in ("list", "dict", "dictionary", "hashset", "ienumerable", "[]")):
        return "json"
    return "str"


def _fields_from_structure(payload: Any) -> list[SchemaField]:
    """Interpreta respostas tipicamente { Result: { Prop: TypeName, ... } } ou lista."""
    fields: list[SchemaField] = []
    if payload is None:
        return fields
    data = payload.get("Result", payload) if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        for k, v in data.items():
            if k.startswith("_"):
                continue
            if isinstance(v, str):
                fields.append(SchemaField(name=k, kind=_kind_from_type_name(v), description=v))
            elif isinstance(v, dict):
                tn = v.get("Type") or v.get("type") or v.get("PropertyType") or ""
                desc = v.get("Description") or v.get("description") or str(tn)
                fields.append(SchemaField(name=k, kind=_kind_from_type_name(str(tn)), description=str(desc)))
            else:
                fields.append(SchemaField(name=k, kind="str"))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                name = item.get("Name") or item.get("name") or item.get("PropertyName")
                if not name:
                    continue
                tn = item.get("Type") or item.get("type") or ""
                fields.append(SchemaField(name=str(name), kind=_kind_from_type_name(str(tn))))
    return fields


def fetch_structure(ipc: IpcClient, type_name: str) -> list[SchemaField]:
    for base in (f"/Api/Structure/{type_name}", f"/Api/Type/{type_name}"):
        r = ipc._request("GET", base, timeout=ipc.TIMEOUT_FAST)
        if r.ok and r.data is not None:
            fields = _fields_from_structure(r.data)
            if fields:
                return fields
    return []


def bot_schema(ipc: IpcClient, mode: str, disk_data: dict) -> list[SchemaField]:
    mode = (mode or "simple").lower()
    if mode == "simple":
        return [SchemaField(n, k) for n, k in BOT_SIMPLE_FIELDS]
    # advanced: try API then disk keys
    for cand in _BOT_TYPE_CANDIDATES:
        fields = fetch_structure(ipc, cand)
        if fields:
            return fields
    if disk_data:
        out = []
        for k, v in sorted(disk_data.items()):
            if isinstance(v, bool):
                kind = "bool"
            elif isinstance(v, int) and not isinstance(v, bool):
                kind = "int"
            elif isinstance(v, (list, dict)):
                kind = "json"
            else:
                kind = "str"
            out.append(SchemaField(k, kind))
        return out
    return [SchemaField(n, k) for n, k in BOT_SIMPLE_FIELDS]


def asf_schema(ipc: IpcClient, mode: str, disk_data: dict) -> list[SchemaField]:
    mode = (mode or "simple").lower()
    if mode == "simple":
        return [SchemaField(n, k) for n, k in ASF_SIMPLE_FIELDS]
    for cand in _ASF_TYPE_CANDIDATES:
        fields = fetch_structure(ipc, cand)
        if fields:
            return fields
    if disk_data:
        out = []
        for k, v in sorted(disk_data.items()):
            if isinstance(v, bool):
                kind = "bool"
            elif isinstance(v, int) and not isinstance(v, bool):
                kind = "int"
            elif isinstance(v, (list, dict)):
                kind = "json"
            else:
                kind = "str"
            out.append(SchemaField(k, kind))
        return out
    return [SchemaField(n, k) for n, k in ASF_SIMPLE_FIELDS]
