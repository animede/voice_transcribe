#!/usr/bin/env bash
# 起動。先に llama-server を音声が扱えるモデルで起動しておく。ブラウザで http://127.0.0.1:7880
cd "$(dirname "$0")"
[ -x .venv/bin/uvicorn ] || { echo "先に ./setup.sh を実行してください" >&2; exit 1; }
exec .venv/bin/uvicorn server:app --host 127.0.0.1 --port "${PORT:-7880}"
