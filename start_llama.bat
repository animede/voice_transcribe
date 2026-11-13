@echo off
rem Start llama-server with Gemma 4 E2B (it understands audio). Keep this window open.
rem   Install llama.cpp first:  winget install llama.cpp
rem   Bigger model:  $env:LLM_MODEL = "unsloth/gemma-4-E4B-it-GGUF"; .\start_llama.bat
rem Do NOT add --no-mmproj: the mmproj file is what lets the model hear audio.
setlocal
if not defined LLM_MODEL set LLM_MODEL=unsloth/gemma-4-E2B-it-GGUF
where llama-server >nul 2>nul || (
  echo llama-server not found. Run: winget install llama.cpp  and open a new terminal.
  exit /b 1
)
llama-server -hf %LLM_MODEL% --host 127.0.0.1 --port 8080 --reasoning off -np 1
