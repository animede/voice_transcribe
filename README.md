# voice_transcribe

音声を Gemma 4 に直接渡して文字起こしするアプリ。文字起こし専用のモデル(Whisper など)は使わず、llama-server で動かしている Gemma 4 にそのまま音声を聞かせる。

- マイクで録音するか、音声ファイル(mp3・m4a・wav など)を選ぶ/ドロップする
- 長い音声は 30 秒くらいずつ、静かなところで分けて順に処理し、終わったところから画面に出す
- 結果はコピー、テキスト(.txt)、時間つきの字幕(.srt)で保存できる
- 出てくる名前や用語をヒントとして渡せる

音声はブラウザの中で 16kHz・モノラルの WAV に変換してから送るので、サーバーに ffmpeg は要らない。AI の部分は llama-server が受け持つので、このアプリ自体は軽い(依存は FastAPI・uvicorn・httpx・numpy だけ)。

## 1. llama-server を起動する

音声が扱えるモデル(Gemma 4 の E2B か E4B)で起動する。`-hf` で指定すると、音声と画像を扱う部分(mmproj)も一緒にダウンロードされる。

```
llama-server -hf unsloth/gemma-4-E2B-it-GGUF --reasoning off
```

Windows で llama.cpp を入れるには `winget install llama.cpp`。

## 2. アプリを起動する

### Windows(PowerShell)
```
.\setup.bat
.\run.bat
```

### Linux / macOS
```
./setup.sh
./run.sh
```

ブラウザで http://127.0.0.1:7880 を開く。

## 設定(環境変数)

| 名前 | 既定 | 意味 |
|---|---|---|
| `LLM_BASE_URL` | `http://127.0.0.1:8080/v1` | llama-server の場所 |
| `CHUNK_SEC` | `30` | 長い音声を分ける長さ(秒) |
| `PORT` | `7880` | このアプリのポート |

PowerShell では `$env:LLM_BASE_URL = "http://127.0.0.1:8081/v1"` のように設定してから起動する。

## ファイル

- `server.py` API と画面の配信。区切りごとに llama-server へ音声を送り、結果を 1 行 1 件の JSON で順に返す
- `audio.py` WAV の読み書き、静かなところで分ける、無音の判定
- `static/index.html` 画面(録音、16kHz WAV への変換、結果の表示と保存)

## 注意

- llama.cpp の音声入力は、まだ試験的な機能です。
- ほとんど無音の区切りは AI に渡さない(無音を渡すと、ない言葉を作ることがあるため)。
