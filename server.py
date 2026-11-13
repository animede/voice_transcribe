"""音声を Gemma 4 (llama-server) に直接渡して文字起こしするアプリ。

起動:
    先に llama-server を、音声が扱えるモデルで起動しておく(例: Gemma 4 E2B / E4B)。
        llama-server -hf unsloth/gemma-4-E2B-it-GGUF --reasoning off
    そのあと ./run.sh(Windows は .\\run.bat)。ブラウザで http://127.0.0.1:7880 を開く。

環境変数:
    LLM_BASE_URL  llama-server の場所。既定は http://127.0.0.1:8080/v1
    CHUNK_SEC     長い音声を分ける長さ(秒)。既定は 30
"""
import base64
import json
import os
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

import audio

HERE = Path(__file__).parent
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1").rstrip("/")
CHUNK_SEC = float(os.getenv("CHUNK_SEC", "30"))
MAX_UPLOAD = 200 * 2**20  # 16kHz・16 ビットで約 1 時間 50 分

LANGS = {"auto": "", "ja": "音声は日本語です。", "en": "The audio is in English. "}

app = FastAPI(title="voice_transcribe")


def prompt(lang: str, hint: str) -> str:
    p = LANGS.get(lang, "") + "この音声を、話されたとおりに文字に起こしてください。"
    p += "句読点を付けてください。説明や前置きは書かず、文字起こしの結果だけを出力してください。"
    if hint.strip():
        p += f"\n次の言葉が出てくることがあります: {hint.strip()}"
    return p


@app.get("/")
def page():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/api/status")
async def status():
    """llama-server が動いているか、どのモデルかを調べる。"""
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{LLM_BASE_URL}/models")
            r.raise_for_status()
            models = [m.get("id", "") for m in r.json().get("data", [])]
        return {"ok": True, "base_url": LLM_BASE_URL, "model": models[0] if models else "", "chunk_sec": CHUNK_SEC}
    except Exception as e:
        return {"ok": False, "base_url": LLM_BASE_URL, "error": str(e), "chunk_sec": CHUNK_SEC}


async def transcribe_chunk(c: httpx.AsyncClient, wav: bytes, text: str) -> str:
    body = {
        "messages": [{"role": "user", "content": [
            {"type": "input_audio", "input_audio": {"data": base64.b64encode(wav).decode(), "format": "wav"}},
            {"type": "text", "text": text},
        ]}],
        "temperature": 0,
    }
    r = await c.post(f"{LLM_BASE_URL}/chat/completions", json=body)
    if r.status_code != 200:
        raise RuntimeError(f"llama-server がエラーを返しました({r.status_code}): {r.text[:300]}")
    return r.json()["choices"][0]["message"]["content"].strip()


@app.post("/api/transcribe")
async def transcribe(request: Request, lang: str = Query("ja"), hint: str = Query("", max_length=500)):
    """16kHz・モノラルの WAV を本文で受け取り、区切りごとの結果を 1 行 1 件の JSON で順に返す。"""
    data = await request.body()
    if not data or len(data) > MAX_UPLOAD:
        raise HTTPException(400, "音声が空か、大きすぎます")
    try:
        x = audio.read_wav(data)
    except Exception as e:
        raise HTTPException(400, f"WAV として読めません: {e}")
    parts = audio.split(x, CHUNK_SEC)
    text = prompt(lang, hint)

    async def run():
        yield json.dumps({"type": "start", "total": len(parts), "duration": len(x) / audio.RATE}) + "\n"
        async with httpx.AsyncClient(timeout=300) as c:
            for i, (s, e) in enumerate(parts):
                seg = x[s:e]
                t = time.perf_counter()
                try:
                    out = "" if audio.is_silent(seg) else await transcribe_chunk(c, audio.to_wav(seg), text)
                    err = None
                except Exception as ex:
                    out, err = "", str(ex)
                yield json.dumps({
                    "type": "chunk", "index": i, "total": len(parts),
                    "start": s / audio.RATE, "end": e / audio.RATE,
                    "text": out, "ms": round((time.perf_counter() - t) * 1000), "error": err,
                }, ensure_ascii=False) + "\n"
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(run(), media_type="application/x-ndjson")
