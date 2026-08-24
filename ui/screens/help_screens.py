from __future__ import annotations

import tkinter as tk

from ui import theme as T
from ui.components import widgets as W
from ui.components.chrome import FlatScrollbar
from ui.mode_util import is_advanced, mode_label


HELP_DESKTOP = """ASF Desktop — Ajuda rápida

O que é
  Camada gráfica de conforto para o ArchiSteamFarm (ASF).
  Não substitui o ASF: credenciais e bots ficam nos arquivos do ASF.

Primeiros passos
  1. Configure o caminho do ASF (Setup ou Configurações).
  2. Na Home, use Play para iniciar o processo ASF.
  3. Crie bots em Bots → Novo bot, se ainda não houver.
  4. Use Start/Pause/Stop nos cards ou em Bot Details.

Modo Simples vs Avançado
  Gaveta → INTERFACE. Simples mostra o essencial;
  Avançado aumenta densidade técnica (métricas, JSON, IPC).

Fechar o aplicativo
  Encerra o Desktop e o processo ASF juntos.

Problemas comuns
  • ASF parado: inicie na Home.
  • Sem bots: crie em Novo bot ou confira a pasta config/.
  • IPC falhou: confira senha IPC no ASF.json e em Configurações.
  • 2FA: um popup deve abrir; se não abrir, veja o Console.

Mais detalhes: tela Manual Desktop.
"""

MANUAL_DESKTOP = """Manual — ASF Desktop

Navegação
  Menu (☰) abre a gaveta. Voltar aparece quando há histórico.
  Engrenagem abre Configurações.

Telas principais
  Home — status, resumo de bots, atividade recente.
  Bots — lista completa, busca e filtros.
  Bot Details — um bot, ações e (Avançado) JSON da API.
  Console — stdout/stderr real do processo ASF.
  Inventário / BGR / Redeem — operações de itens e keys.
  Mass Editor — mesma propriedade em vários bots.
  Config global ASF — ASF.json.
  Logs — processo, arquivos e crashes do Desktop.

Segurança
  Senhas Steam e maFiles são do ASF, não do Desktop.
  O Console tenta ocultar segredos óbvios (redaction).

Atualização
  Update Desktop consulta releases no GitHub.
  Update ASF usa o mecanismo oficial via IPC.
"""

HELP_ASF = """Ajuda — ArchiSteamFarm

ASF é o motor que farmas cartas Steam em segundo plano.
Documentação oficial:
  https://github.com/JustArchiNET/ArchiSteamFarm/wiki

IPC local (padrão)
  http://127.0.0.1:1242
  Swagger (ASF rodando): /swagger

Headless
  O Desktop prefere Headless=true para 2FA via comando input,
  sem console interativa.

Plugins
  Pastas em ASF/plugins/. O Desktop lista o que encontrar no disco.
"""

MANUAL_ASF = """Manual resumido — ASF

Config
  ASF/config/ASF.json — global
  ASF/config/<Bot>.json — por bot

Comandos úteis (Console / IPC Command)
  status, resume, pause, start, stop
  redeem, loot, transfer
  input <Bot> <Type> <Value> — 2FA e inputs

Bots
  KeepRunning, Enabled, SteamLogin, SteamPassword
  (senha só no arquivo do ASF)

Atualização do ASF
  Preferir o update oficial (IPC Update) em vez de substituir
  a pasta manualmente com o ASF em execução.

Wiki completa no GitHub do JustArchiNET.
"""


class _TextPage(tk.Frame):
    def __init__(self, parent, app, title: str, body: str) -> None:
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        c = app.colors
        W.h1(self, title, c).pack(anchor="w", padx=24, pady=(20, 8))
        wrap = tk.Frame(self, bg=c["card"], highlightbackground=c["border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        self.text = tk.Text(
            wrap, bg=c["card"], fg=c["fg_secondary"], relief="flat",
            font=T.FONT_SMALL, wrap="word", highlightthickness=0, padx=14, pady=12,
        )
        sb = FlatScrollbar(wrap, command=self.text.yview, colors=c)
        self.text.configure(yscrollcommand=sb.set)
        self.text.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.text.insert("1.0", body)
        self.text.configure(state="disabled")

    def on_show(self, **kwargs) -> None:
        pass


class HelpDesktopScreen(_TextPage):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, app, "Ajuda — Desktop", HELP_DESKTOP)


class ManualDesktopScreen(_TextPage):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, app, "Manual — Desktop", MANUAL_DESKTOP)


class HelpAsfScreen(_TextPage):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, app, "Ajuda — ASF", HELP_ASF)


class ManualAsfScreen(_TextPage):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, app, "Manual — ASF", MANUAL_ASF)
