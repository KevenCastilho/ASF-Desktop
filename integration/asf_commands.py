"""
Comandos ASF oficiais usados pelo Desktop (nível Master).

Fonte: wiki Commands / Trading — ArchiSteamFarm.

loot [Bots]
  Envia itens LootableTypes do bot → Master (SteamUserPermissions).

loot@ [Bots] <AppIDs>
  Idem, filtrado por AppIDs.

transfer [Bots] <TargetBot>
  Envia TransferableTypes do(s) bot(s) → TargetBot.

transfer@ [Bots] <AppIDs> <TargetBot>
  Idem, filtrado por AppIDs.

redeem [Bots] <keys…>
  Via API /Api/Bot/{name}/Redeem ou comando.

Permissão: Master (ou superior) no SteamUserPermissions do bot.
IPC /Api/Command executa como contexto privilegiado local.
"""
from __future__ import annotations

from integration.ipc_client import IpcClient, IpcResult


def loot(ipc: IpcClient, bots: str = "ASF") -> IpcResult:
    """loot [Bots] — itens lootable → Master."""
    return ipc.command(f"loot {bots}".strip())


def loot_appids(ipc: IpcClient, bots: str, app_ids: str) -> IpcResult:
    """loot@ [Bots] <AppIDs>"""
    return ipc.command(f"loot@ {bots} {app_ids}".strip())


def transfer(ipc: IpcClient, bots: str, target_bot: str) -> IpcResult:
    """transfer [Bots] <TargetBot>"""
    return ipc.command(f"transfer {bots} {target_bot}".strip())


def transfer_appids(ipc: IpcClient, bots: str, app_ids: str, target_bot: str) -> IpcResult:
    """transfer@ [Bots] <AppIDs> <TargetBot>"""
    return ipc.command(f"transfer@ {bots} {app_ids} {target_bot}".strip())


def redeem_keys(ipc: IpcClient, bot: str, keys: list[str]) -> IpcResult:
    r = ipc.redeem_keys(bot, keys)
    if r.ok:
        return r
    return ipc.command(f"redeem {bot} {','.join(keys)}")
