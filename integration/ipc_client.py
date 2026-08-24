"""ASF IPC/HTTP client — capability-aware, UI-safe timeouts."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class IpcResult:
    ok: bool
    status: int = 0
    data: Any = None
    error: str = ""


@dataclass
class BotSummary:
    name: str
    is_connected: bool = False
    is_farming: bool = False
    keep_running: bool = False
    raw: dict = field(default_factory=dict)


class IpcClient:
    # Timeouts curtos para UI nunca travar 5s+
    TIMEOUT_FAST = 0.8
    TIMEOUT_NORMAL = 2.0
    TIMEOUT_SLOW = 8.0

    def __init__(self, settings) -> None:
        self.settings = settings
        self.last_error: str = ""
        self._bots_cache: list[BotSummary] = []
        self._bots_cache_at: float = 0.0
        self._bots_ttl: float = 2.0

    @property
    def base_url(self) -> str:
        host = self.settings.get("ipc_host", "127.0.0.1")
        port = int(self.settings.get("ipc_port", 1242))
        return f"http://{host}:{port}"

    def _password(self) -> str:
        return (self.settings.get("ipc_password") or "").strip()

    def _request(
        self,
        method: str,
        path: str,
        body: Any = None,
        timeout: float | None = None,
    ) -> IpcResult:
        if timeout is None:
            timeout = self.TIMEOUT_NORMAL
        url = self.base_url.rstrip("/") + path
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        pwd = self._password()
        if pwd:
            headers["Authentication"] = pwd
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                payload = json.loads(raw) if raw else None
                return IpcResult(ok=True, status=getattr(resp, "status", 200), data=payload)
        except HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")[:400]
            except Exception:
                pass
            self.last_error = f"HTTP {e.code}: {err_body or e.reason}"
            return IpcResult(ok=False, status=e.code, error=self.last_error)
        except URLError as e:
            self.last_error = f"IPC indisponível: {e.reason}"
            return IpcResult(ok=False, status=0, error=self.last_error)
        except TimeoutError:
            self.last_error = "IPC timeout"
            return IpcResult(ok=False, status=0, error=self.last_error)
        except Exception as e:
            self.last_error = str(e)
            return IpcResult(ok=False, status=0, error=self.last_error)

    def get_asf(self) -> IpcResult:
        return self._request("GET", "/Api/ASF", timeout=self.TIMEOUT_FAST)

    def get_bots(self, names: str = "ASF", *, use_cache: bool = True) -> IpcResult:
        if use_cache and self._bots_cache and (time.monotonic() - self._bots_cache_at) < self._bots_ttl:
            # synthetic ok with cached structure not needed — callers use parse or cache helpers
            pass
        return self._request("GET", f"/Api/Bot/{names}", timeout=self.TIMEOUT_FAST)

    def bots_cached(self, force: bool = False) -> list[BotSummary]:
        now = time.monotonic()
        if not force and self._bots_cache and (now - self._bots_cache_at) < self._bots_ttl:
            return list(self._bots_cache)
        r = self.get_bots(use_cache=False)
        bots = self.parse_bots(r)
        if r.ok:
            self._bots_cache = bots
            self._bots_cache_at = now
        return bots

    def invalidate_bots_cache(self) -> None:
        self._bots_cache_at = 0.0

    def start_bot(self, names: str) -> IpcResult:
        self.invalidate_bots_cache()
        return self._request("POST", f"/Api/Bot/{names}/Start", timeout=self.TIMEOUT_NORMAL)

    def stop_bot(self, names: str) -> IpcResult:
        self.invalidate_bots_cache()
        return self._request("POST", f"/Api/Bot/{names}/Stop", timeout=self.TIMEOUT_NORMAL)

    def pause_bot(self, names: str) -> IpcResult:
        self.invalidate_bots_cache()
        return self._request("POST", f"/Api/Bot/{names}/Pause", timeout=self.TIMEOUT_NORMAL)

    def resume_bot(self, names: str) -> IpcResult:
        self.invalidate_bots_cache()
        return self._request("POST", f"/Api/Bot/{names}/Resume", timeout=self.TIMEOUT_NORMAL)

    def exit_asf(self) -> IpcResult:
        return self._request("POST", "/Api/ASF/Exit", timeout=self.TIMEOUT_NORMAL)

    def restart_asf(self) -> IpcResult:
        return self._request("POST", "/Api/ASF/Restart", timeout=self.TIMEOUT_SLOW)

    def update_asf(self) -> IpcResult:
        return self._request("POST", "/Api/ASF/Update", timeout=self.TIMEOUT_SLOW)

    def command(self, cmd: str) -> IpcResult:
        r = self._request("POST", "/Api/Command", body={"Command": cmd}, timeout=self.TIMEOUT_NORMAL)
        if not r.ok:
            r2 = self._request("POST", f"/Api/Command/{cmd}", timeout=self.TIMEOUT_NORMAL)
            if r2.ok:
                return r2
        return r

    def input_command(self, bot: str, type_name: str, value: str) -> IpcResult:
        cmd = f"input {bot} {type_name} {value}".strip()
        return self.command(cmd)

    def redeem_keys(self, bot: str, keys: list[str]) -> IpcResult:
        for body in (
            {"KeysToRedeem": keys},
            {"keysToRedeem": keys},
            keys,
        ):
            r = self._request("POST", f"/Api/Bot/{bot}/Redeem", body=body, timeout=self.TIMEOUT_SLOW)
            if r.ok:
                return r
        return r

    def get_inventory(self, bot: str) -> IpcResult:
        return self._request("GET", f"/Api/Bot/{bot}/Inventory", timeout=self.TIMEOUT_NORMAL)

    def update_bot_config(self, bot: str, patch: dict) -> IpcResult:
        return self._request("POST", f"/Api/Bot/{bot}", body=patch, timeout=self.TIMEOUT_NORMAL)

    def delete_bot(self, bot: str) -> IpcResult:
        return self._request("DELETE", f"/Api/Bot/{bot}", timeout=self.TIMEOUT_NORMAL)

    def parse_bots(self, result: IpcResult) -> list[BotSummary]:
        bots: list[BotSummary] = []
        if not result.ok or not result.data:
            return bots
        data = result.data
        payload = data.get("Result", data) if isinstance(data, dict) else data
        if not isinstance(payload, dict):
            return bots
        for name, info in payload.items():
            if not isinstance(info, dict):
                continue
            connected = bool(info.get("IsConnectedAndLoggedOn"))
            keep = bool(info.get("KeepRunning", True))
            cards = info.get("CardsFarmer") or {}
            farming = False
            if isinstance(cards, dict):
                farming = bool(cards.get("CurrentGamesFarming")) and not bool(cards.get("Paused"))
            bots.append(
                BotSummary(
                    name=name,
                    is_connected=connected,
                    is_farming=farming,
                    keep_running=keep,
                    raw=info,
                )
            )
        return bots
