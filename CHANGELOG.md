# ASF Desktop v2 — 0.1.0 (produto inicial completo)

## Inclui

- Splash bootstrap (auto-deps, sem pip manual)
- Processo ASF externo + Headless + console oculta + encerra com Desktop
- IPC completo o bastante para o núcleo + redeem/inventory/command/input
- Setup: selecionar instalação ou baixar stable do GitHub
- Shell: gaveta, voltar, status, tema
- Home (métricas, cards, feed), Bots, Bot Details, Configurar bot, Wizard novo bot
- Atividade, Console (filtros NLog + comando)
- BGR, Redeem, Mass Editor, Inventário (3 modos)
- Config global ASF.json, Settings Desktop (IPC password)
- Import/Export zip de configs
- Plugins (listagem em disco)
- Ajuda/Manual Desktop e ASF
- Popup GetUserInput (janela separada)
- Tray opcional (se Pillow+pystray instalarem)
- Launchers run.bat / run.sh
- Script PyInstaller (pasta portátil, sem MSI)
- Docs de produto em asf-desktop-v2-docs/

## Como executar

```text
python main.py
# ou
run.bat
# ou
./run.sh
```

## 0.1.1 — parciais fechados

- Logs manager (processo / arquivos ASF / crashes / erros) + export ZIP com redaction
- Update Desktop (check GitHub Releases + download ZIP)
- Inventário: ações loot / trade / transfer via comandos ASF
- Input: lista ampliada de tipos Headless + Y/N DeviceConfirmation
- Plugins: nota sobre oficiais (MobileAuthenticator, etc.)

## Stage 1 (completar incompletos) — 2026-08-24

- Setup: pós-config conta bots em `config/`; se zero → abre **Novo bot**; mensagens mais claras
- Home: ranking de cards (farming > online > keep_running)
- Bot Details: resumo humano (jogos/farming) + Resume + JSON no Advanced
- Ajuda/Manual ×4: conteúdo útil mínimo (não placeholder vazio)
- Ferramentas → Diagnóstico: path, PID, IPC, bots, modo
- Redeem: corrige envio duplicado; detalhe IPC no Advanced
- BGR: detalhe IPC no Advanced
- Mass Editor: mais campos bloqueados em massa (login/senha/ID)
- Simple/Advanced: densidade mantida (D-02; menu completo)


## Stage 2 (pendentes de integração) — 2026-08-24

- Baseline documental `asf-api-baseline.md`
- Capability probe (`integration/capabilities.py`) no poll de status
- Input types oficiais + detecção por mensagem/log
- Popup 2FA tenta tipos na ordem detectada
- Settings: iniciar com o sistema (Win Run / Linux autostart)
- Settings: toggles de notificações
- Retenção Activity → tamanho do buffer de logs
- Inventário: evita modo API real se capability negar
- Docs: SPEC-STATUS + matriz Simple/Advanced


## Stage 3 (não implementados) — 2026-08-24

- `integration/schema.py` — Type/Structure com fallback Simple/JSON
- Config bot + Config global ASF usam schema
- DELETE bot (IPC + arquivo) em Configurar e Bot Details
- Inventário resumido em Bot Details (UI-012)
- Scripts PyInstaller `scripts/build_pyinstaller.bat/.sh`
- Testes: `tests/test_schema_and_input.py`

