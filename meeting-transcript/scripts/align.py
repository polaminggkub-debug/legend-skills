"""Put every source on one wall clock and record the measured offsets.

Clock model (lessons: references/lessons.md, "Clock alignment"):
* Wispr = Mac clock: position -> epoch from live.ndjson (startEpochMs - startRecordingMs),
  split at pause/resume markers.
* Optional gap_fix: a Wispr recording that lost audio across a break (zero-filled stretch): after the
  break it is shifted by the jump J seen against Plaud, plus a small rate r chosen so that the
  following Wispr recording (its own Mac-clock start) lines up.
* Plaud / QuickTime(OBS): dense probes every 60 s against the overlapping Wispr mic channel
  (log-energy envelope cross-correlation +-25 s, refined by GCC-PHAT +-60 ms) give knots
  (source position -> epoch); between knots the map is linear, so Plaud's ~0.3 s drop-outs
  are absorbed.
* A source with no overlapping Mac recording (borrow_offset) reuses the offset/drift measured on a
  recording from the same device.
Settings come from meeting.json "align" (see config.py). Writes WORK/offsets.json
({src: {"pieces": [[pos_a, pos_b, epoch_a, epoch_b], ...], ...}}) and WORK/probes.json.
Usage: python align.py
"""
from __future__ import annotations

import json

import numpy as np
import soundfile as sf

from config import CFG, SOURCES, SRC, WORK, hms, nominal_start_epoch_ms, source_duration_s

SR = 16000
HOP = 160  # 10 ms envelope frames
ALIGN = CFG.get("align", {})
PAIRS = [tuple(p) for p in ALIGN.get("pairs", [])]   # (target, Wispr reference)
BORROW = ALIGN.get("borrow_offset", {})              # target -> donor recorded by the same device
GAP = ALIGN.get("gap_fix")                           # Wispr recording with a zero-filled break (found by zero-run scan)


def wispr_bases(src: str) -> list[tuple[float, float]]:
    """[(rec_ms_start, epoch_base_ms)]: epoch = base + rec_ms inside each recorded piece."""
    rows = [json.loads(line) for line in open(SRC / "wispr" / SOURCES[src]["id"] / "live.ndjson") if line.strip()]
    segs = [r for r in rows if "startEpochMs" in r]
    pieces, paused_at = [(0.0, float(segs[0]["startEpochMs"] - segs[0]["startRecordingMs"]))], None
    for r in rows:
        if r.get("marker") == "paused":
            paused_at = r["epochMs"]
        elif r.get("marker") == "resumed" and paused_at is not None:
            rec_ms = paused_at - pieces[-1][1]
            later = [s for s in segs if s["startRecordingMs"] >= rec_ms]  # marker leads audio by ~0.2 s
            base = later[0]["startEpochMs"] - later[0]["startRecordingMs"] if later else r["epochMs"] - rec_ms
            pieces.append((float(rec_ms), float(base)))
            paused_at = None
    for s in segs:
        b = [p for p in pieces if s["startRecordingMs"] >= p[0]][-1][1]
        assert abs(s["startEpochMs"] - s["startRecordingMs"] - b) < 50, (src, s["id"])
    return pieces


def load(src: str) -> np.ndarray:
    name = f"{src}.ch1" if SOURCES[src]["kind"] in ("wispr", "quicktime") else src
    return sf.read(WORK / "wav" / f"{name}.wav", dtype="float32")[0]


def envelope(x: np.ndarray) -> np.ndarray:
    n = len(x) // HOP
    e = np.log10(np.mean(x[: n * HOP].reshape(n, HOP) ** 2, axis=1) + 1e-9)
    e = e - np.convolve(e, np.ones(100) / 100, mode="same")  # drop slow gain differences
    return (e - e.mean()) / (e.std() + 1e-9)


def xcorr_lag(a: np.ndarray, b: np.ndarray, max_lag: int) -> tuple[int, float]:
    """Lag L maximising sum a[i] * b[i + L] for 0 <= L <= max_lag; returns (L, peak/second peak)."""
    nfft = 1 << (len(a) + len(b) - 1).bit_length()
    r = np.fft.irfft(np.conj(np.fft.rfft(a, nfft)) * np.fft.rfft(b, nfft), nfft)[: max_lag + 1]
    i = int(np.argmax(r))
    mask = np.abs(np.arange(len(r)) - i) > 20
    second = np.max(r[mask]) if mask.any() else 0.0
    return i, float(r[i] / (second + 1e-9))


def gcc_phat(a: np.ndarray, b: np.ndarray, max_lag: int) -> int:
    nfft = 1 << (len(a) + len(b) - 1).bit_length()
    cross = np.conj(np.fft.rfft(a, nfft)) * np.fft.rfft(b, nfft)
    r = np.fft.irfft(cross / (np.abs(cross) + 1e-12), nfft)
    vals = np.concatenate([r[-max_lag:], r[: max_lag + 1]])
    return int(np.argmax(vals)) - max_lag


def dense_probes(tgt: str, ref: str, start_delta: float, win=45.0, margin=25.0, step=60.0) -> list[dict]:
    """delta = tgt_pos - ref_pos of the same sound, every `step` s of the reference."""
    xr, xt = load(ref), load(tgt)
    delta, out = start_delta, []
    for ref_t in np.arange(5.0, len(xr) / SR - win - 5, step):
        tgt_t = ref_t + delta
        if tgt_t - margin < 0 or tgt_t + win + margin > len(xt) / SR:
            continue
        a = xr[int(ref_t * SR): int((ref_t + win) * SR)]
        lo = int((tgt_t - margin) * SR)
        b = xt[lo: lo + int((win + 2 * margin) * SR)]
        if np.sqrt(np.mean(a ** 2)) < 3e-4 or np.sqrt(np.mean(b ** 2)) < 3e-4:
            continue
        lag, ratio = xcorr_lag(envelope(a), envelope(b), int(2 * margin * 100))
        b0 = lo + lag * HOP
        fine = gcc_phat(a, xt[b0: b0 + len(a)], int(0.06 * SR))
        d = (b0 + fine) / SR - ref_t
        out.append({"ref_t": float(ref_t + win / 2), "tgt_t": float(ref_t + win / 2 + d), "delta": d, "ratio": round(ratio, 2)})
        if ratio >= 2.0:
            delta = d
    return clean(out)


def clean(probes: list[dict]) -> list[dict]:
    """Mark usable probes: clear peak and not a lone outlier against both neighbours."""
    good = [p for p in probes if p["ratio"] >= 2.0]
    for i, p in enumerate(good):
        nb = [q["delta"] for q in good[max(0, i - 2): i] + good[i + 1: i + 3]]
        p["used"] = not (len(nb) >= 2 and np.std(nb) < 0.1 and abs(p["delta"] - np.median(nb)) > 0.25)
    for p in probes:
        p.setdefault("used", False)
    return probes


def nominal_delta(tgt: str, ref_base_ms: float) -> float:
    return (ref_base_ms - nominal_start_epoch_ms(tgt)) / 1000


class PieceMap:
    """Piecewise-linear position(ms) -> epoch(ms)."""

    def __init__(self, pieces):
        self.pieces = sorted(pieces)

    def __call__(self, pos_ms: float) -> float:
        for a, b, ea, eb in self.pieces:
            if a <= pos_ms <= b:
                return ea + (pos_ms - a) * ((eb - ea) / (b - a) if b > a else 1.0)
        a, b, ea, eb = self.pieces[0] if pos_ms < self.pieces[0][0] else self.pieces[-1]
        return (ea + pos_ms - a) if pos_ms < a else (eb + pos_ms - b)


def wispr_map(src: str, dur_ms: float) -> list[list[float]]:
    bases = wispr_bases(src)
    pieces = []
    for i, (rs, base) in enumerate(bases):
        re_ = bases[i + 1][0] if i + 1 < len(bases) else dur_ms
        pieces.append([rs, re_, base + rs, base + re_])
    return pieces


def knots_to_pieces(knots: list[tuple[float, float]], dur_ms: float) -> list[list[float]]:
    """Through (pos_ms, epoch_ms) knots; slope 1 before the first and after the last knot."""
    knots = sorted(knots)
    pts = [(0.0, knots[0][1] - knots[0][0])] + knots + [(dur_ms, knots[-1][1] + dur_ms - knots[-1][0])]
    return [[a[0], b[0], a[1], b[1]] for a, b in zip(pts, pts[1:]) if b[0] > a[0]]


def apply_gap_fix(maps: dict, probes: dict, offs: dict, dur: dict):
    """gap_fix: the Wispr recording `src` lost audio across a break (`break_s`). After it, shift by the jump J
    seen against the Plaud recording `via`, plus a rate r so that the next Wispr recording `next` (its own
    Mac-clock start) lines up."""
    src, via, nxt = GAP["src"], GAP["via"], GAP["next"]
    brk = GAP["break_s"]
    pw = [p for p in probes[(via, src)] if p["used"]]
    before = [p for p in pw if p["ref_t"] < brk[0]]
    after = [p for p in pw if p["ref_t"] > brk[1]]
    J = after[0]["delta"] - before[-1]["delta"]
    pn = [p for p in probes[(via, nxt)] if p["used"]]
    via_at_next_start = pn[0]["tgt_t"] - pn[0]["ref_t"]                      # via pos (s) at `next` pos 0
    last = after[-1]
    pos_there = last["ref_t"] + (via_at_next_start - last["tgt_t"])           # src pos (s) at that moment
    b_src, b_next = maps[src].pieces[0][2], maps[nxt].pieces[0][2]
    want = (b_next - b_src) / 1000                                           # s from src base to `next` start
    r = (want - pos_there - J) / (pos_there - brk[1])
    s0, s1 = brk[1] * 1000, dur[src]
    e_pre_end = b_src + brk[0] * 1000
    e_post = lambda pos_ms: b_src + pos_ms + J * 1000 + r * (pos_ms - s0)  # noqa: E731
    maps[src] = PieceMap([[0.0, brk[0] * 1000, b_src, e_pre_end],
                          [brk[0] * 1000, s0, e_pre_end, e_post(s0)],
                          [s0, s1, e_post(s0), e_post(s1)]])
    offs[src] = {"note": f"Wispr lost {J:.2f} s across the break; after it +{J:.2f} s and rate {r * 1e6:+.0f} ppm "
                         f"so that {nxt} (own Mac-clock start) lines up", "jump_s": J, "rate_ppm": r * 1e6}
    print(f"{src} break jump J={J:.3f} s, post-break rate r={r * 1e6:+.1f} ppm")


def skip_probe(ref: str, p: dict) -> bool:
    """Probes inside the zero-filled break (+-30 s) or after the real audio ended are not trusted."""
    return bool(GAP) and ref == GAP["src"] and (
        GAP["break_s"][0] - 30 < p["ref_t"] < GAP["break_s"][1] + 30 or p["ref_t"] > GAP["audio_end_s"] - 30)


def knot_maps(maps: dict, probes: dict, offs: dict, dur: dict):
    """Plaud / backup recordings: knots through the probes, mapped via their reference Wispr map."""
    for tgt in dict.fromkeys(t for t, _ in PAIRS):
        knots = []
        for (t, ref), pl in probes.items():
            if t != tgt:
                continue
            knots += [(p["tgt_t"] * 1000, maps[ref](p["ref_t"] * 1000)) for p in pl if p["used"] and not skip_probe(ref, p)]
        maps[tgt] = PieceMap(knots_to_pieces(knots, dur[tgt]))
        d0 = maps[tgt](0) - nominal_start_epoch_ms(tgt)
        d1 = maps[tgt](dur[tgt]) - nominal_start_epoch_ms(tgt) - dur[tgt]
        offs[tgt] = {"knots": len(knots), "offset_start_ms": round(d0), "offset_end_ms": round(d1),
                     "note": "dense probes vs Wispr mic channel"}


def borrow_offsets(maps: dict, offs: dict, dur: dict):
    """A source with no overlapping Mac recording: same device as `donor` -> reuse its start offset and average rate."""
    for tgt, donor in BORROW.items():
        p = offs[donor]
        rate = (p["offset_end_ms"] - p["offset_start_ms"]) / dur[donor]
        n0 = nominal_start_epoch_ms(tgt) + p["offset_start_ms"]
        maps[tgt] = PieceMap([[0.0, dur[tgt], n0, n0 + dur[tgt] * (1 + rate)]])
        offs[tgt] = {"offset_start_ms": p["offset_start_ms"], "rate_ppm": rate * 1e6,
                     "note": f"no overlapping Mac recording; offset and rate copied from {donor} (same device)"}


def main():
    offs, maps, probes_all = {}, {}, {}
    dur = {s: source_duration_s(s) * 1000 for s in SOURCES}
    for src, meta in SOURCES.items():
        if meta["kind"] == "wispr":
            maps[src] = PieceMap(wispr_map(src, dur[src]))
    probes = {}
    for tgt, ref in PAIRS:
        base = maps[ref].pieces[0][2]
        probes[(tgt, ref)] = dense_probes(tgt, ref, nominal_delta(tgt, base))
        used = [p for p in probes[(tgt, ref)] if p["used"]]
        print(f"{tgt}~{ref}: {len(used)}/{len(probes[(tgt, ref)])} probes used, "
              f"delta {used[0]['delta']:+.3f} -> {used[-1]['delta']:+.3f} s", flush=True)
        probes_all[f"{tgt}~{ref}"] = probes[(tgt, ref)]
    if GAP:
        apply_gap_fix(maps, probes, offs, dur)
    knot_maps(maps, probes, offs, dur)
    borrow_offsets(maps, offs, dur)
    for src in SOURCES:
        offs.setdefault(src, {})["pieces"] = [[round(v, 1) for v in pc] for pc in maps[src].pieces]
        offs[src]["start_local"] = hms(maps[src](0))
        offs[src]["end_local"] = hms(maps[src](dur[src]))
        offs[src]["nominal_start_offset_ms"] = round(maps[src](0) - nominal_start_epoch_ms(src))
        print(f"{src:5s} {offs[src]['start_local']} -> {offs[src]['end_local']}  "
              f"start vs nominal {offs[src]['nominal_start_offset_ms']:+d} ms")
    (WORK / "offsets.json").write_text(json.dumps(offs, indent=1))
    (WORK / "probes.json").write_text(json.dumps(probes_all, indent=1))


if __name__ == "__main__":
    main()
