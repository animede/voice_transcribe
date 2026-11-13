@echo off
rem Start llama-server with Gemma 4 E2B (it understands audio). Keep this window open.
rem   Install llama.cpp first:  winget install llama.cpp
rem   Bigger model:  $env:LLM_MODEL = "unsloth/gemma-4-E4B-it-GGUF:Q4_K_M"; .\start_llama.bat
rem Run this in the voice_transcribe folder (cd there first).
rem Do NOT add --no-mmproj: the mmproj file is what lets the model hear audio.
setlocal
if not defined LLM_MODEL set LLM_MODEL=unsloth/gemma-4-E2B-it-GGUF:Q4_K_M
rem -c 8192: without it llama-server reserves memory for the model's full context and may run out of memory.
if not defined LLM_CTX set LLM_CTX=8192
where llama-server >nul 2>nul || (
  echo llama-server not found. Run: winget install llama.cpp  and open a new terminal.
  exit /b 1
)
llama-server -hf %LLM_MODEL% -c %LLM_CTX% --host 127.0.0.1 --port 8080 --reasoning off -np 1
