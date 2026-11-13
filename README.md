# voice_transcribe

音声を Gemma 4 に直接渡して文字起こしするアプリ。文字起こし専用のモデル(Whisper など)は使わず、llama-server で動かしている Gemma 4 にそのまま音声を聞かせる。

- マイクで録音するか、音声ファイル(mp3・m4a・wav など)を選ぶ/ドロップする。WAV は 8/16/24/32 ビット、浮動小数点、多チャンネルも読める(ブラウザが読めない WAV は自前で読む)
- 長い音声は 30 秒くらいずつ、静かなところで分けて順に処理し、終わったところから画面に出す
- 結果はコピー、テキスト(.txt)、時間つきの字幕(.srt)で保存できる
- 出てくる名前や用語をヒントとして渡せる

音声はブラウザの中で 16kHz・モノラルの WAV に変換してから送るので、サーバーに ffmpeg は要らない。AI の部分は llama-server が受け持つので、このアプリ自体は軽い(依存は FastAPI・uvicorn・httpx・numpy だけ)。

## 使い方(Windows・PowerShell)

ターミナルを 2 つ使う。1 つ目で llama-server、2 つ目でこのアプリを動かす。

1. llama.cpp を入れる(初回だけ。入れたらターミナルを開き直す)
   ```
   winget install llama.cpp
   ```
2. 1 つ目のターミナルで、このアプリのフォルダに移動して llama-server を起動する(初回はモデルをダウンロードする)
   ```
   cd $HOME\voice_transcribe
   .\start_llama.bat
   ```
   `cd` の先は、`git clone` したフォルダにする。
   Gemma 4 E2B を、音声を扱う部分(mmproj)と一緒に読み込む。大きい E4B を使うなら `$env:LLM_MODEL = "unsloth/gemma-4-E4B-it-GGUF:Q4_K_M"` を設定してから起動する。
3. 2 つ目のターミナルでも同じフォルダに移動して、アプリを入れて起動する
   ```
   cd $HOME\voice_transcribe
   .\setup.bat
   .\run.bat
   ```
4. ブラウザで http://127.0.0.1:7880 を開く。初めて録音するときは、マイクを使ってよいかを聞かれるので「許可」を選ぶ。

止めるときは、それぞれのターミナルで Ctrl+C を押す。

**`--no-mmproj` を付けない**:mmproj は音声と画像を受け取る部分。前作の「困ったとき」で紹介した `--no-mmproj` を付けて起動すると、音声を渡せない。画面の上に「音声を扱えません」と出たら、付けずに起動し直す。

## 使い方(Linux / macOS)

```
./start_llama.sh      # 1 つ目のターミナル
./setup.sh            # 2 つ目のターミナル(初回だけ)
./run.sh
```

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
- `start_llama.bat` / `start_llama.sh` llama-server を Gemma 4 E2B で起動する

## 注意

- llama.cpp の音声入力は、まだ試験的な機能です。
- ほとんど無音の区切りは AI に渡さない(無音を渡すと、ない言葉を作ることがあるため)。
