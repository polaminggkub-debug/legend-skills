"""Speaker embeddings for diarization: Silero VAD speech -> 1.5 s windows (0.75 s hop) -> ECAPA.

Model: speechbrain/spkrec-ecapa-voxceleb (ungated). Embeddings are L2-normalised.
Output: WORK/diar/<src>.npz with t0, t1 (seconds in the source audio) and emb [N, 192].
Plaud device files are embedded too, so a Plaud-only meeting can be linked to the same people through a
stretch where Plaud and Wispr overlap. Threads: env EMB_THREADS (default 8).
Usage: python diarize_embed.py [src ...]   (default: meeting.json "diarize.embed", else every source)
"""
from __future__ import annotations

import os
import sys

import numpy as np
import soundfile as sf
import torch

from config import CFG, SOURCES, WORK
from run_asr import wav_for

SR = 16000
WIN, HOP = 1.5, 0.75   # ECAPA windows: 1.5 s / hop 0.75 s (shorter windows are too noisy to cluster)
DEFAULT = CFG.get("diarize", {}).get("embed") or list(SOURCES)


def speech_regions(x: np.ndarray) -> list[tuple[float, float]]:
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    opts = VadOptions(threshold=0.4, min_silence_duration_ms=250, speech_pad_ms=100, min_speech_duration_ms=300)
    return [(s["start"] / SR, s["end"] / SR) for s in get_speech_timestamps(x, opts)]


def windows(regions) -> list[tuple[float, float]]:
    out = []
    for a, b in regions:
        if b - a < 0.8:
            continue
        if b - a <= WIN:
            out.append((a, b))
            continue
        t = a
        while t + WIN <= b + 1e-6:
            out.append((t, t + WIN))
            t += HOP
        if out[-1][1] < b - 0.3:
            out.append((b - WIN, b))
    return out


def embed(src: str, clf):
    x, _ = sf.read(wav_for(src), dtype="float32")
    wins = windows(speech_regions(x))
    embs = []
    n = int(WIN * SR)
    for i in range(0, len(wins), 256):
        batch = wins[i:i + 256]
        arr = np.zeros((len(batch), n), dtype=np.float32)
        lens = np.zeros(len(batch), dtype=np.float32)
        for j, (a, b) in enumerate(batch):
            seg = x[int(a * SR): int(b * SR)][:n]
            arr[j, :len(seg)] = seg
            lens[j] = len(seg) / n
        with torch.no_grad():
            e = clf.encode_batch(torch.from_numpy(arr), torch.from_numpy(lens)).squeeze(1).numpy()
        embs.append(e / np.linalg.norm(e, axis=1, keepdims=True))
    t = np.array(wins)
    np.savez_compressed(WORK / "diar" / f"{src}.npz", t0=t[:, 0], t1=t[:, 1], emb=np.concatenate(embs))
    return src, len(wins)


def main():
    from speechbrain.inference.speaker import EncoderClassifier
    torch.set_num_threads(int(os.environ.get("EMB_THREADS", "8")))
    (WORK / "diar").mkdir(parents=True, exist_ok=True)
    clf = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                         savedir=str(WORK / "sb-ecapa"), run_opts={"device": "cpu"})
    for src in sys.argv[1:] or DEFAULT:
        if (WORK / "diar" / f"{src}.npz").exists():
            continue
        s, n = embed(src, clf)
        print(f"{s}: {n} windows", flush=True)


if __name__ == "__main__":
    main()
