"""WAV を扱う小さな道具。ブラウザが 16kHz・モノラルの WAV にしてから送ってくるので、ffmpeg などは使わない。

長い音声は CHUNK 秒くらいずつに分ける。区切りは、目安の位置の前後 SEARCH 秒のうちで、いちばん静かなところにする
(ことばの途中で切らないため)。
"""
import io
import wave

import numpy as np

RATE = 16000  # Gemma 4 の音声は 16kHz・モノラル


def read_wav(data: bytes) -> np.ndarray:
    """WAV のバイト列を、16kHz・モノラルの int16 の配列にする。"""
    with wave.open(io.BytesIO(data)) as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if width != 2:
        raise ValueError("16 ビットの WAV だけ扱えます")
    x = np.frombuffer(raw, dtype=np.int16)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1).astype(np.int16)
    if rate != RATE:  # ふつうはブラウザで変換済み。違うときだけ簡単に合わせる
        t = np.linspace(0, len(x) / rate, int(len(x) * RATE / rate), endpoint=False)
        x = np.interp(t, np.arange(len(x)) / rate, x).astype(np.int16)
    return x


def to_wav(x: np.ndarray) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(x.astype(np.int16).tobytes())
    return buf.getvalue()


def split(x: np.ndarray, chunk: float = 30.0, search: float = 4.0) -> list[tuple[int, int]]:
    """(始まり, 終わり) のサンプル位置の一覧を返す。"""
    n, size, win = len(x), int(chunk * RATE), int(search * RATE)
    if n <= size + win:
        return [(0, n)]
    # 0.05 秒ごとの音の大きさ
    hop = RATE // 20
    energy = np.sqrt(np.mean(x[: n // hop * hop].astype(np.float32).reshape(-1, hop) ** 2, axis=1))
    cuts, start = [], 0
    while n - start > size + win:
        lo, hi = (start + size - win) // hop, (start + size + win) // hop
        cut = (lo + int(np.argmin(energy[lo:hi]))) * hop
        cuts.append((start, cut))
        start = cut
    cuts.append((start, n))
    return cuts


def is_silent(x: np.ndarray, threshold: float = 120.0) -> bool:
    """ほとんど無音なら True(無音を AI に渡すと、ない言葉を作ることがある)。"""
    return len(x) == 0 or float(np.sqrt(np.mean(x.astype(np.float32) ** 2))) < threshold
