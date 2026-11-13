@echo off
rem Start the app, then open http://127.0.0.1:7880 in a browser.
rem Start llama-server first with a model that accepts audio, e.g.:
rem   llama-server -hf unsloth/gemma-4-E2B-it-GGUF --reasoning off
rem Another llama-server address:  $env:LLM_BASE_URL = "http://127.0.0.1:8080/v1"
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist .venv\Scripts\uvicorn.exe (
  echo Run setup.bat first.
  exit /b 1
)
if not defined PORT set PORT=7880
.venv\Scripts\uvicorn.exe server:app --host 127.0.0.1 --port %PORT%
