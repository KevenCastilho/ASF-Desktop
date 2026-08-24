@echo off
cd /d "%~dp0"
REM Sem janela de CMD persistente: pythonw
where pythonw >nul 2>&1
if %errorlevel%==0 (
  start "" pythonw main.py
  exit /b 0
)
REM fallback: python minimizado
start "" /min python main.py
exit /b 0
