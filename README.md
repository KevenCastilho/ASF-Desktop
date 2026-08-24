# ASF Desktop

**Camada gráfica de QoL para o [ArchiSteamFarm](https://github.com/JustArchiNET/ArchiSteamFarm)**  
Python · Tkinter · Windows & Linux · sem WebView

---

## Introdução

O **ASF Desktop** nasceu para quem usa o ArchiSteamFarm no dia a dia e prefere **não viver no terminal**.

Ele **não substitui** o ASF, **não é um fork** e **não inventa** capacidades dentro do motor da Steam.  
É uma **interface nativa** que orquestra o processo do ASF, conversa com a **IPC/API local** e organiza bots, logs, keys, inventário e configurações de forma legível.

Se o ASF é o motor, o Desktop é o painel: você dirige; o ASF continua mandando no que é dele (credenciais, maFiles, regras de farming, plugins).

---

## Apresentação

| | |
|--|--|
| **Nome** | ASF Desktop (v2) |
| **Papel** | Cliente gráfico / QoL sobre ASF |
| **Stack** | Python 3.11+ · Tkinter · HTTP IPC |
| **Plataformas** | Windows e Linux |
| **ASF** | Processo **externo** (oficial JustArchiNET) |
| **Instalador** | Não obrigatório — pasta portátil + `python main.py` |
| **Modos de UI** | **Simples** e **Avançado** (mesma app, densidades diferentes) |

Visual inspirado em apps desktop leves (ícones estilo Lucide, tema claro/escuro/sistema, gaveta de navegação).  
Dependências como `psutil` (e opcionalmente Pillow/pystray para bandeja) podem ser instaladas **automaticamente no splash**, no espírito de não obrigar o usuário a rodar `pip` na mão.

---

## Resumo rápido

1. Aponte o ASF instalado **ou** baixe a stable oficial do GitHub pelo próprio Desktop.
2. Inicie o ASF pela Home (console do ASF fica oculta enquanto o Desktop controla).
3. Gerencie bots (start/pause/stop/resume), configs, console, redeem/BGR, inventário e logs.
4. Ao **fechar o Desktop**, o processo do ASF é **encerrado** junto.
5. Credenciais Steam ficam **só** nos arquivos do ASF — o Desktop não é cofre de senhas.

---

## Descrição completa

### O que o programa é (e o que não é)

**É**

- Uma UI amigável para operar o ASF localmente
- Um gerenciador de ciclo de vida do processo ASF (iniciar, parar, observar stdout/stderr)
- Um cliente da **IPC HTTP** do ASF (`127.0.0.1:1242` por padrão)
- Um editor assistido de `config/*.json` e `ASF.json`, com visão simples ou avançada
- Um ponto único para ferramentas operacionais (diagnóstico, update, import/export, plugins em disco)

**Não é**

- Fork ou patch do núcleo ASF
- Painel remoto / multi-servidor (remoto **fora** do escopo v2)
- Cópia embutida do HTML do ASF-ui ou ConfigGenerator
- Armazenador de `SteamPassword`, maFiles ou tokens
- Substituição do update oficial do ASF (ele só **dispara** o que a API permite)

### Arquitetura em uma frase
[UI Tkinter] → [IPC client + arquivos config] → [processo ArchiSteamFarm]
                     ↑
              settings do Desktop
           (tema, path, modo, tray…)

Camadas no código (KISS): domain/, integration/, process/, persistence/, ui/, security/.

### Relação com o ASF

| Tema | Comportamento |
|------|----------------|
| Instalação | Selecionar exe/pasta **ou** baixar zip official do GitHub |
| Execução | Subprocesso com janela de console **oculta** (quando o SO permite) |
| Comunicação | IPC/API local + leitura/escrita de JSON em config/ |
| Console do Desktop | **stdout/stderr reais** do processo (não WebSocket NLog) |
| 2FA / input | Popup separado; envio via comando input (modo Headless preferido) |
| Encerramento | Fechar o Desktop **termina** o ASF |

### Modos Simples e Avançado (D-02)

- **Simples:** essencial operacional — status, ações, campos principais, menos ruído técnico.
- **Avançado:** mesma navegação, **mais densidade** — métricas, JSON da API, host/porta IPC, DEBUG no console, schema completo quando disponível.

**Simple ≠ “versão limitada”.** O menu não some pela metade; muda a **densidade** das telas.

### Navegação e shell

- **Gaveta lateral** (☰) com ícones Lucide e scroll interno quando necessário
- **Voltar** contextual (sem histórico estilo browser com setas duplas)
- **Engrenagem** → Configurações
- **Barra de status** + indicador Running / Stopped / Starting / Unauthorized
- **Tema:** sistema, escuro ou claro (reconstrói a UI)
- **Bandeja (tray):** opcional (Pillow + pystray); comportamento do **X** configurável (tray ou sair)
- **Uma instância** por vez (lock com tolerância a crash)

### Telas e fluxos

| Área | Função |
|------|--------|
| **Setup** | “Já tenho ASF” (file/folder picker) ou “Baixar do GitHub”; se não houver bots → wizard do primeiro bot |
| **Home** | Play/Pause/Stop do ASF, contadores Online/Pausado/Parado, cards dos bots mais relevantes (farming prioritário), feed recente; no Avançado: CPU/RAM/PID e URL IPC |
| **Bots** | Lista completa, busca/filtro, carregar mais, ações rápidas, menu ⋮ → detalhes |
| **Bot Details** | Status legível, jogos em farming quando a API expõe, Resume, inventário resumido, JSON no Avançado, Configurar / Excluir |
| **Novo bot** | Wizard: nome (validação + anti-duplicata) → Steam login/senha → concluir e opcionalmente iniciar |
| **Configurar bot** | Simple: campos essenciais; Advanced: schema /Api/Type|Structure se existir, senão JSON do disco; salvar + reinício opcional; **excluir** (IPC DELETE + arquivo) |
| **Config global ASF** | Editor do ASF.json (Simple/Advanced + schema quando possível) |
| **Mass Editor** | Mesma propriedade em vários bots; bloqueia login/senha/nome/ID em massa |
| **Atividade** | Feed derivado dos logs do processo |
| **Console** | Saída do ASF, filtros por nível NLog, busca, barra de comando IPC; Simple oculta DEBUG/TRACE por padrão |
| **Inventário** | Global / por bot (logs) e, no Avançado, tentativa de API real se a capability existir; loot/transfer conforme comandos oficiais |
| **BGR** | Várias keys (uma por linha), import txt, bot + start/pause/stop |
| **Redeem** | CD-Keys no bot escolhido; detalhe IPC no Avançado |
| **Plugins** | Lista pastas em ASF/plugins/ e DLLs (sem inventar API) |
| **Logs** | Processo, arquivos, crashes do Desktop; exportação |
| **Importar / Exportar** | Backup/restauração da pasta config |
| **Ferramentas** | Atalhos + diagnóstico (path, PID, IPC, bots) |
| **Update Desktop** | Consulta releases no GitHub do próprio Desktop |
| **Update ASF** | Dispara update oficial via IPC |
| **Ajuda / Manual ×4** | Desktop e ASF (textos embutidos + pontes para a wiki oficial) |
| **Configurações** | Tema, fechar→tray/sair, path ASF, senha IPC (se necessário), autostart, notificações, no Avançado host/porta IPC e retenção de Activity |

### Integração técnica (resumo)

- Cliente HTTP com timeouts curtos (UI não deve “congelar” segundos a fio)
- **Capability probe** em runtime: esconde ou evita rotas que a build não expõe
- **Baseline documental** em asf-desktop-v2-docs/architecture/asf-api-baseline.md
- Redaction de segredos óbvios em logs/console
- Bootstrap: splash + instalação automática de deps quando possível

### Empacotamento

- Uso diário: pasta + Python + main.py / run.bat / run.sh
- Opcional: PyInstaller (scripts/build_pyinstaller.bat ou .sh) → pasta dist/ASFDesktop/

### Segurança (regras de ouro)

- Senhas e maFiles: **ASF**
- Desktop settings: preferências de UI/path — **sem** copiar vault Steam
- 2FA: valor digitado no popup **não** é gravado pelo Desktop
- Não versionar settings.json com dados sensíveis do seu PC

---

## Como instalar e usar

### Requisitos

- **Python 3.11+** com **Tkinter** (no Windows, o instalador oficial costuma incluir)
- Rede na primeira vez (deps e, se for o caso, download do ASF)
- ASF oficial (já instalado **ou** baixado pelo Desktop)

### Instalação (desenvolvimento / portátil)

1. Extraia o zip do ASF Desktop.
2. Entre na pasta asf-desktop-v2.
3. Execute:

**Windows (recomendado, sem janela de console extra):**

    run.bat

ou:

    pythonw main.py

**Linux / genérico:**

    chmod +x run.sh
    ./run.sh

ou:

    python3 main.py

4. No **splash**, o app tenta instalar sozinho o que faltar (psutil, etc.).
5. Se algo falhar, em último caso:

    pip install -r requirements.txt

### Primeiro uso

1. **Setup**
   - *Já tenho o ASF* → selecione ArchiSteamFarm.exe (ou a pasta), **ou**
   - *Baixar do GitHub* → stable oficial para a pasta padrão do Desktop.
2. Se não existir bot em config/, o fluxo oferece para **Novo bot**.
3. Na **Home**, inicie o ASF (Play).
4. Aguarde IPC (**Running** na barra).
5. Use **Bots** / cards para operar contas.
6. Ajuste **Simples/Avançado** na gaveta conforme o quanto de detalhe técnico você quer ver.

### Uso do dia a dia

- **Farming ok?** Home e cards.
- **Guard / 2FA?** Popup separado — cole o código.
- **Keys?** Redeem ou BGR.
- **Ver o que o ASF escreveu?** Console ou Atividade.
- **Mudar Enabled em 10 bots?** Mass Editor.
- **Sair de verdade?** Configurações → “Encerrar ASF Desktop” no X, ou sair pela bandeja; o processo ASF deve morrer junto.

### Build binário (opcional)

    scripts\build_pyinstaller.bat

    ./scripts/build_pyinstaller.sh

Saída típica: dist/ASFDesktop/

### Documentação extra

- asf-desktop-v2-docs/ — visão, ADRs, baseline IPC, matriz Simple/Advanced, gates

---

## Créditos

### ASF Desktop

- **Concepção, produto e direção do projeto:** autor do ASF Desktop — decisões de escopo, UX, QoL e reconstrução v2.
- **Assistência de arquitetura, especificação e implementação assistida:** **Grok** (xAI) — análise do material v1, consolidação da spec v2, código e documentação desta linha de desenvolvimento.

### ArchiSteamFarm

O ASF Desktop **depende inteiramente** do trabalho do ecossistema oficial:

- ArchiSteamFarm — https://github.com/JustArchiNET/ArchiSteamFarm — © JustArchiNET / JustArchi e contribuidores
- Wiki e contratos de IPC/API/comandos: documentação oficial do projeto ASF

Este Desktop **não afilia** nem substitui o ASF; apenas consome a API e os arquivos de configuração no formato que o ASF define.

### Agradecimentos

- Comunidade e mantenedores do ArchiSteamFarm
- Referências de UX desktop nativa (incl. experiências com Tkinter em outros utilitários do autor)

---

## Licença e aviso

- Respeite a licença e os termos do **ArchiSteamFarm** e da Steam.
- Uso por sua conta e risco; automatização de contas Steam está sujeita às regras da Valve.
- Código do Desktop: conforme a licença que você publicar neste repositório.

---

*ASF Desktop — menos terminal, mesmo ASF.*
