"""Decode every source to 16 kHz mono 16-bit WAV in WORK/wav (originals are only read).

Stereo sources are also written per channel (`<src>.ch1.wav`, `<src>.ch2.wav`) so the
active channel can be chosen; QuickTime parts are concatenated into one timeline.
Usage: python decode_audio.py [src ...]
"""
from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import soundfile as sf

from config import AUDIO, SOURCES, WORK


def ffmpeg_decode(inp, out, pan: str | None):
    af = ["-af", pan] if pan else []
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(inp), *af,
           "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(out)]
    subprocess.run(cmd, check=True)


def channels(path) -> int:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                          "stream=channels", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return int(out.stdout.strip())


def decode(src: str):
    wav = WORK / "wav"
    files = [AUDIO / f for f in SOURCES[src]["files"]]
    nch = channels(files[0])
    variants = {"": None} if nch == 1 else {".ch1": "pan=mono|c0=c0", ".ch2": "pan=mono|c0=c1"}
    for suffix, pan in variants.items():
        parts = []
        for i, f in enumerate(files):
            out = wav / (f"{src}{suffix}.part{i}.wav" if len(files) > 1 else f"{src}{suffix}.wav")
            ffmpeg_decode(f, out, pan)
            parts.append(out)
        if len(parts) > 1:
            data = np.concatenate([sf.read(p, dtype="int16")[0] for p in parts])
            sf.write(wav / f"{src}{suffix}.wav", data, 16000, subtype="PCM_16")
            for p in parts:
                p.unlink()
    return src, nch


if __name__ == "__main__":
    (WORK / "wav").mkdir(parents=True, exist_ok=True)
    todo = sys.argv[1:] or list(SOURCES)
    with ThreadPoolExecutor(len(todo)) as ex:
        for src, nch in ex.map(decode, todo):
            print(src, "channels", nch, flush=True)
