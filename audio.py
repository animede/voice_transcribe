"""WAV を扱う小さな道具。ブラウザが 16kHz・モノラルの WAV にしてから送ってくるので、ffmpeg などは使わない。

長い音声は CHUNK 秒くらいずつに分ける。区切りは、目安の位置の前後 SEARCH 秒のうちで、いちばん静かなところにする
(ことばの途中で切らないため)。
"""
import io
import wave

import numpy as np

RATE = 16000  # Gemma 4 の音声は 16kHz・モノラル


def _parse_wav(data: bytes) -> tuple[np.ndarray, int]:
    """WAV を読んで (-1〜1 の float32 の配列[サンプル, チャンネル], サンプリング周波数) を返す。

    標準の wave モジュールが読めない形式(32 ビット浮動小数点、拡張ヘッダー)も読む。
    """
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("WAV ではありません")
    fmt, body, o = None, None, 12
    while o + 8 <= len(data):
        cid, size = data[o:o + 4], int.from_bytes(data[o + 4:o + 8], "little")
        if cid == b"fmt ":
            code = int.from_bytes(data[o + 8:o + 10], "little")
            if code == 0xFFFE:  # WAVE_FORMAT_EXTENSIBLE
                code = int.from_bytes(data[o + 32:o + 34], "little")
            fmt = (code, int.from_bytes(data[o + 10:o + 12], "little"), int.from_bytes(data[o + 12:o + 16], "little"),
                   int.from_bytes(data[o + 22:o + 24], "little"))
        elif cid == b"data":
            body = data[o + 8:o + 8 + size]
        o += 8 + size + (size & 1)
    if not fmt or body is None:
        raise ValueError("WAV の中身が見つかりません")
    code, ch, rate, bits = fmt
    if code == 3 and bits in (32, 64):
        x = np.frombuffer(body[: len(body) // (bits // 8) * (bits // 8)], dtype=np.float32 if bits == 32 else np.float64)
    elif code == 1 and bits == 8:
        x = (np.frombuffer(body, dtype=np.uint8).astype(np.float32) - 128) / 128
    elif code == 1 and bits == 16:
        x = np.frombuffer(body[: len(body) // 2 * 2], dtype="<i2") / 32768
    elif code == 1 and bits == 24:
        b = np.frombuffer(body[: len(body) // 3 * 3], dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        x = ((b[:, 0] << 8 | b[:, 1] << 16 | b[:, 2] << 24) >> 8) / 8388608
    elif code == 1 and bits == 32:
        x = np.frombuffer(body[: len(body) // 4 * 4], dtype="<i4") / 2147483648
    else:
        raise ValueError(f"この WAV の形式には対応していません(形式 {code}、{bits} ビット)")
    x = x[: len(x) // ch * ch].astype(np.float32).reshape(-1, ch)
    return x, rate


def read_wav(data: bytes) -> np.ndarray:
    """WAV のバイト列を、16kHz・モノラルの int16 の配列にする(8/16/24/32 ビット、浮動小数点、多チャンネルに対応)。"""
    f, rate = _parse_wav(data)
    x = (np.clip(f.mean(axis=1), -1, 1) * 32767).astype(np.int16)
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
