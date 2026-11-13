#!/usr/bin/env bash
# llama-server を Gemma 4 E2B(音声を聞ける)で起動する。この窓は開いたままにする。
# 大きいモデル: LLM_MODEL=unsloth/gemma-4-E4B-it-GGUF:Q4_K_M ./start_llama.sh
# -c 8192: 付けないと、モデルの最大の長さぶんのメモリを確保して足りなくなることがある。
# --no-mmproj は付けない(mmproj があるから音声を聞ける)。
command -v llama-server >/dev/null || { echo "llama-server が見つかりません(PATH に入れるか、llama.cpp をビルドしてください)" >&2; exit 1; }
exec llama-server -hf "${LLM_MODEL:-unsloth/gemma-4-E2B-it-GGUF:Q4_K_M}" -c "${LLM_CTX:-8192}" --host 127.0.0.1 --port 8080 --reasoning off -np 1
