"""Transcribe one stretch of one decoded WAV with faster-whisper (Thai, word timestamps).

Times in the output are positions in the source audio (seconds), so chunks can be merged.
Usage: python asr.py MODEL WAV START_S END_S OUT_JSON [--threads N] [--compute int8] [--beam 5]
MODEL is a folder name under ~/work/tools/models (e.g. biodatlab-th-combined-ct2, large-v3-ct2).
"""
from __future__ import annotations

import argparse
import json
import time

import soundfile as sf

from config import MODELS


def run(args):
    from faster_whisper import WhisperModel

    sr = 16000
    info = sf.info(args.wav)
    start = max(0, int(args.start * sr))
    stop = min(info.frames, int(args.end * sr))
    audio, _ = sf.read(args.wav, start=start, stop=stop, dtype="float32")
    model = WhisperModel(str(MODELS / args.model), device="cpu", compute_type=args.compute,
                         cpu_threads=args.threads, num_workers=1)
    t0 = time.time()
    segs, meta = model.transcribe(
        audio, language="th", task="transcribe", beam_size=args.beam, best_of=5,
        word_timestamps=True, condition_on_previous_text=False,
        vad_filter=True, vad_parameters={"threshold": 0.35, "min_silence_duration_ms": 600, "speech_pad_ms": 300},
        hallucination_silence_threshold=2.0, no_speech_threshold=0.6, log_prob_threshold=-1.0,
        compression_ratio_threshold=4.0, temperature=[0.0, 0.2, 0.4, 0.6])
    out = []
    for s in segs:
        out.append({
            "start": round(args.start + s.start, 3), "end": round(args.start + s.end, 3), "text": s.text.strip(),
            "avg_logprob": round(s.avg_logprob, 3), "no_speech_prob": round(s.no_speech_prob, 3),
            "compression_ratio": round(s.compression_ratio, 2), "temperature": s.temperature,
            "words": [[round(args.start + w.start, 3), round(args.start + w.end, 3), w.word, round(w.probability, 3)]
                      for w in (s.words or [])],
        })
    doc = {"model": args.model, "wav": str(args.wav), "start": args.start, "end": args.end,
           "compute": args.compute, "beam": args.beam, "elapsed_s": round(time.time() - t0, 1),
           "speech_s": round(meta.duration_after_vad, 1), "segments": out}
    with open(args.out, "w") as f:
        json.dump(doc, f, ensure_ascii=False)
    return doc


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("wav")
    ap.add_argument("start", type=float)
    ap.add_argument("end", type=float)
    ap.add_argument("out")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--compute", default="int8")
    ap.add_argument("--beam", type=int, default=5)
    d = run(ap.parse_args())
    print(f"{d['model']} {d['start']}-{d['end']} speech {d['speech_s']}s elapsed {d['elapsed_s']}s segs {len(d['segments'])}")
