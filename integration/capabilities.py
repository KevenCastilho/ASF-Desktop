"""Capability detection — sonda endpoints da instância ASF local."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AsfCapabilities:
    probed_at: float = 0.0
    ipc_reachable: bool = False
    unauthorized: bool = False
    has_asf: bool = False
    has_bots: bool = False
    has_bot_start: bool = False
    has_bot_stop: bool = False
    has_bot_pause: bool = False
    has_bot_resume: bool = False
    has_redeem: bool = False
    has_inventory: bool = False
    has_command: bool = False
    has_update: bool = False
    has_type_api: bool = False
    has_structure_api: bool = False
    asf_version: str = ""
    raw_asf: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def supports(self, feature: str) -> bool:
        return bool(getattr(self, feature, False))


# Cache curto para não martelar a IPC a cada troca de tela
_CACHE: AsfCapabilities | None = None
_CACHE_TTL = 15.0


def get_cached() -> AsfCapabilities | None:
    global _CACHE
    if _CACHE and (time.time() - _CACHE.probed_at) < _CACHE_TTL:
        return _CACHE
    return None


def probe(ipc) -> AsfCapabilities:
    """Sonda leve: GET ASF + HEAD-like via GET em rotas críticas."""
    global _CACHE
    cached = get_cached()
    if cached is not None:
        return cached

    cap = AsfCapabilities(probed_at=time.time())
    r = ipc.get_asf()
    if not r.ok:
        if r.status == 401:
            cap.unauthorized = True
            cap.ipc_reachable = True
        cap.errors.append(r.error or "ASF unreachable")
        _CACHE = cap
        return cap

    cap.ipc_reachable = True
    cap.has_asf = True
    data = r.data if isinstance(r.data, dict) else {}
    result = data.get("Result", data) if isinstance(data, dict) else {}
    if isinstance(result, dict):
        cap.raw_asf = result
        ver = result.get("Version") or result.get("version") or ""
        if isinstance(ver, dict):
            ver = ver.get("Major") and f"{ver}" or str(ver)
        cap.asf_version = str(ver)

    # Bots list
    br = ipc.get_bots("ASF")
    if br.ok:
        cap.has_bots = True
        bots = ipc.parse_bots(br)
        # test action routes only if we have a bot name (cheap: assume routes exist if ASF responds 404 vs 405)
        # Preferir: se GET bots ok, ações REST padrão da stable existem
        cap.has_bot_start = True
        cap.has_bot_stop = True
        cap.has_bot_pause = True
        cap.has_bot_resume = True
        cap.has_redeem = True
        # Inventory: tenta um bot se houver
        if bots:
            inv = ipc.get_inventory(bots[0].name)
            if inv.ok or inv.status in (400, 403, 409):
                # 400/403 = rota existe mas precondição
                cap.has_inventory = True
            elif inv.status == 404:
                cap.has_inventory = False
            else:
                # timeout/erro genérico — assume disponível se bots ok
                cap.has_inventory = True
        else:
            cap.has_inventory = True  # rota padrão; UI valida depois
    else:
        cap.errors.append(br.error or "bots failed")

    # Command
    cr = ipc.command("status ASF")
    if cr.ok or cr.status in (400, 403):
        cap.has_command = True
    elif cr.status != 404:
        cap.has_command = True  # muitas builds retornam mensagem em vez de 404
    else:
        cap.has_command = False

    # Update
    # Não dispara POST Update — só marca como "rota conhecida da baseline"
    cap.has_update = True

    # Type / Structure (schema dinâmico) — probe GET sem efeito
    tr = ipc._request("GET", "/Api/Type/ArchiSteamFarm.Steam.Data.Steam.BotConfig", timeout=ipc.TIMEOUT_FAST)
    if tr.ok or tr.status in (400, 401, 403):
        cap.has_type_api = tr.ok or tr.status != 404
    else:
        cap.has_type_api = tr.status != 404

    sr = ipc._request("GET", "/Api/Structure/ArchiSteamFarm.Steam.Data.Steam.BotConfig", timeout=ipc.TIMEOUT_FAST)
    if sr.status == 404:
        cap.has_structure_api = False
    elif sr.ok or sr.status in (400, 401, 403):
        cap.has_structure_api = True
    else:
        cap.has_structure_api = False

    _CACHE = cap
    return cap


def invalidate() -> None:
    global _CACHE
    _CACHE = None
