@echo off
rem Create .venv and install dependencies (Windows). No torch is needed: llama-server does the AI part.
setlocal
cd /d "%~dp0"
py -3 -m venv .venv || python -m venv .venv || goto :error
.venv\Scripts\python.exe -m pip install -U pip || goto :error
.venv\Scripts\python.exe -m pip install -r requirements.txt || goto :error
echo Done. Start llama-server, then .\run.bat (PowerShell) or run.bat (cmd)
exit /b 0
:error
echo Setup failed.
exit /b 1
