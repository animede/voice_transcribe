#!/usr/bin/env bash
# 仮想環境を作って依存を入れる。AI は llama-server が受け持つので、torch などは要らない。
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt
