"""Run the Whisper passes over every meeting in parallel worker processes.

Pass "best": for every stretch listed in meeting.json "asr.best" (the clearest recording: Wispr mic channel
where it exists, highest SNR in levels.json; Plaud/backup only where Wispr is missing or zero-filled) is cut into
~5 min chunks at quiet points and transcribed by both models:
  th = biodatlab/whisper-th-large-v3-combined (Thai fine-tune, CTranslate2 int8)
  v3 = openai large-v3 (Systran CTranslate2, int8)
Pass "alt" (optional, `--alt`, stretches from "asr.alt"): Thai fine-tune on a second recording for acoustic diversity.
Decoding (lessons.md, "Whisper Thai settings"): BatchedInferencePipeline, Silero VAD chunks <= 15 s (longer
chunks made the Thai model loop), beam 5, temperature 0, no fallback (Thai text has a high zlib ratio, so the
default fallback re-decoded every window), word timestamps, language th.
Output: WORK/asr/<model>/<src>_<start>_<end>.json (times = positions in the source audio, seconds).
Usage: python run_asr.py [--workers 12 --threads 8] [--alt] [--only th|v3]
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import time

import numpy as np
import soundfile as sf

from config import CFG, MODELS, SOURCES, WORK

MODEL_DIRS = {"th": "biodatlab-th-combined-ct2", "v3": "large-v3-ct2", "th-alt": "biodatlab-th-combined-ct2",
              "pt": "pathumma-th-ct2"}  # pt: Pathumma Thai fine-tune, only for re-checking weak spots
CHUNK_S = 300
SR = 16000

# (meeting, src, start_s, end_s|None) from meeting.json "asr": the clearest recording per stretch (Wispr mic
# channel where it exists; Plaud / backup only where Wispr is missing or zero-filled). "alt" = second recording.
BEST = [tuple(r) for r in CFG["asr"]["best"]]
ALT = [tuple(r) for r in CFG["asr"].get("alt", [])]


def wav_for(src: str):
    kind = SOURCES[src]["kind"]
    return WORK / "wav" / (f"{src}.ch1.wav" if kind in ("wispr", "quicktime") else f"{src}.wav")


def quiet_cuts(path, start: float, end: float) -> list[float]:
    """Cut points ~every CHUNK_S s, moved to the quietest second within +-20 s."""
    x, _ = sf.read(path, start=int(start * SR), stop=int(end * SR), dtype="float32")
    fr = 800
    n = len(x) // fr
    e = np.convolve(np.mean(x[: n * fr].reshape(n, fr) ** 2, axis=1), np.ones(20) / 20, mode="same")
    cuts, t = [start], start + CHUNK_S
    while t < end - 60:
        lo, hi = int((t - 20 - start) * 20), int((t + 20 - start) * 20)
        i = lo + int(np.argmin(e[lo:hi]))
        cuts.append(start + i / 20)
        t = cuts[-1] + CHUNK_S
    return cuts + [end]


def plan(stretches, models) -> list[tuple]:
    jobs = []
    for meeting, src, start, end in stretches:
        path = wav_for(src)
        end = end if end is not None else sf.info(path).frames / SR
        cuts = quiet_cuts(path, start, end)
        for a, b in zip(cuts, cuts[1:]):
            for m in models:
                out = WORK / "asr" / m / f"{src}_{a:08.2f}_{b:08.2f}.json"
                if not out.exists():
                    jobs.append((m, meeting, src, str(path), a, b, str(out)))
    return jobs


_MODELS: dict = {}


def worker_init(threads: int):
    global _THREADS
    _THREADS = threads


def transcribe(job):
    from faster_whisper import BatchedInferencePipeline, WhisperModel

    m, meeting, src, path, a, b, out = job
    if m not in _MODELS:
        _MODELS[m] = BatchedInferencePipeline(WhisperModel(str(MODELS / MODEL_DIRS[m]), device="cpu",
                                                           compute_type="int8", cpu_threads=_THREADS))
    audio, _ = sf.read(path, start=int(a * SR), stop=int(b * SR), dtype="float32")
    t0 = time.time()
    segs, info = _MODELS[m].transcribe(
        audio, language="th", task="transcribe", batch_size=8, chunk_length=15, beam_size=5,
        word_timestamps=True, temperature=0.0, compression_ratio_threshold=None, log_prob_threshold=None,
        vad_parameters={"threshold": 0.35, "min_silence_duration_ms": 300, "speech_pad_ms": 200})
    rows = [{"start": round(a + s.start, 3), "end": round(a + s.end, 3), "text": s.text.strip(),
             "avg_logprob": round(s.avg_logprob, 3), "no_speech_prob": round(s.no_speech_prob, 3),
             "compression_ratio": round(s.compression_ratio, 2),
             "words": [[round(a + w.start, 3), round(a + w.end, 3), w.word, round(w.probability, 3)] for w in (s.words or [])]}
            for s in segs]
    doc = {"model": MODEL_DIRS[m], "meeting": meeting, "src": src, "start": a, "end": b,
           "elapsed_s": round(time.time() - t0, 1), "speech_s": round(info.duration_after_vad, 1), "segments": rows}
    tmp = out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(doc, f, ensure_ascii=False)
    os.replace(tmp, out)
    return f"{m} {src} {a:.0f}-{b:.0f} speech {doc['speech_s']}s in {doc['elapsed_s']}s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--alt", action="store_true")
    ap.add_argument("--only", choices=["th", "v3", "pt"])
    args = ap.parse_args()
    models = [args.only] if args.only else ["th", "v3"]
    if args.alt:
        models = ["th-alt"]
    for m in models:
        (WORK / "asr" / m).mkdir(parents=True, exist_ok=True)
    jobs = plan(ALT if args.alt else BEST, models)
    print(f"{len(jobs)} jobs", flush=True)
    ctx = mp.get_context("spawn")
    with ctx.Pool(args.workers, initializer=worker_init, initargs=(args.threads,), maxtasksperchild=None) as pool:
        for i, msg in enumerate(pool.imap_unordered(transcribe, jobs), 1):
            print(f"[{i}/{len(jobs)}] {time.strftime('%H:%M:%S')} {msg}", flush=True)


if __name__ == "__main__":
    main()
