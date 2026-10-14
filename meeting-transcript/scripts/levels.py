"""Per-window loudness and a simple SNR estimate for every decoded WAV.

For each 30 s window: rms_db (whole window), p90_db / p10_db of 50 ms frame energies
(speech level vs noise floor) and snr_db = p90 - p10. Writes WORK/levels.json.
Usage: python levels.py
"""
from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import soundfile as sf

from config import WORK

WIN_S = 30
FRAME = 800  # 50 ms at 16 kHz


def analyse(path):
    x, sr = sf.read(path, dtype="float32")
    n = len(x) // FRAME
    fr = x[: n * FRAME].reshape(n, FRAME)
    e = 10 * np.log10(np.mean(fr ** 2, axis=1) + 1e-12)
    per = WIN_S * sr // FRAME
    rows = []
    for i in range(0, n, per):
        w = e[i:i + per]
        if len(w) < 20:
            continue
        p90, p10 = np.percentile(w, 90), np.percentile(w, 10)
        rms = 10 * np.log10(np.mean(10 ** (w / 10)) + 1e-12)
        rows.append({"t": i * FRAME / sr, "rms_db": round(float(rms), 1), "p90_db": round(float(p90), 1),
                     "p10_db": round(float(p10), 1), "snr_db": round(float(p90 - p10), 1)})
    return path.stem, rows


if __name__ == "__main__":
    wavs = sorted((WORK / "wav").glob("*.wav"))
    out = {}
    with ProcessPoolExecutor(len(wavs)) as ex:
        for name, rows in ex.map(analyse, wavs):
            out[name] = rows
    (WORK / "levels.json").write_text(json.dumps(out))
    for name, rows in sorted(out.items()):
        act = [r for r in rows if r["p90_db"] > -60]
        print(f"{name:10s} windows={len(rows):4d} active={len(act):4d} "
              f"median_p90={np.median([r['p90_db'] for r in rows]):6.1f} "
              f"median_snr={np.median([r['snr_db'] for r in rows]):5.1f}")
