"""Write notes/coverage.md: per meeting, minute-by-minute coverage, weak minutes, offsets, winners.

Minute counts:
- recordings: how many audio files were recording during the minute;
- transcript sources: how many of PL/WL/WR/TH/V3/TA have text in the minute (WL and WR are two
  readings of the same Wispr audio but different engines, so they count separately here);
- low / unheard: minutes whose merged speech is mostly low-confidence, or holds `[ไม่ได้ยิน]`.
Usage: python coverage.py  (needs WORK data; run on the machine that ran the pipeline)
"""
from __future__ import annotations

import json
from collections import Counter

from config import MEETINGS, OUT, SOURCES, TITLE, WORK, hms, nominal_start_epoch_ms, source_duration_s, source_to_epoch_ms
from timeline import asr_segments, diar_turns, meeting_spans, recordings_at, service_segments

TAGS = ["PL", "WL", "WR", "TH", "V3", "TA"]
FULL = {"wispr-live": "WL", "wispr-refined": "WR", "plaud": "PL", "whisper-th": "TH", "whisper-large-v3": "V3",
        "whisper-th-2nd-mic": "TA"}


def transcript_rows(meeting: str) -> list[dict]:
    rows = []
    for part in json.loads((OUT / "transcript" / "index.json").read_text()):
        if part["meeting"] == meeting:
            rows += json.loads((OUT / "transcript" / f"{part['file']}.json").read_text())
    return rows


def ranges(minutes: list[float]) -> str:
    """Compress minute starts (epoch ms) into 'HH:MM–HH:MM' ranges."""
    out, run = [], []
    for m in sorted(minutes):
        if run and m - run[-1] > 60_000:
            out.append(run)
            run = []
        run.append(m)
    if run:
        out.append(run)
    return ", ".join(f"{hms(r[0])[:5]}–{hms(r[-1] + 60_000)[:5]}" for r in out) or "—"


def uncovered_speech(meeting: str, speech: list[dict], to_ms) -> list[tuple[float, float]]:
    """Voice-activity turns (diarization) with no merged segment within 2 s, merged when < 3 s apart."""
    spans = sorted((to_ms(r["start_local"]) - 2000, to_ms(r["end_local"]) + 2000) for r in speech)
    out = []
    for t0, t1, _ in diar_turns(meeting):
        if any(a < t1 and b > t0 for a, b in spans):
            continue
        if out and t0 - out[-1][1] < 3000:
            out[-1] = (out[-1][0], max(out[-1][1], t1))
        else:
            out.append((t0, t1))
    return [(a, b) for a, b in out if b - a >= 10_000]


def meeting_section(meeting: str, origin_rows: list[dict]) -> list[str]:
    spans = meeting_spans(meeting)
    segs = service_segments(meeting) + asr_segments(meeting)
    speech = [r for r in origin_rows if r.get("kind", "speech") == "speech"]
    from datetime import datetime
    to_ms = lambda iso: datetime.fromisoformat(iso).timestamp() * 1000  # noqa: E731
    rec_count, tx_count, low_min, unheard_min, silent_min, total = Counter(), Counter(), [], [], [], 0
    for a, b in spans:
        t = a
        while t < b:
            u = min(b, t + 60_000)
            total += (u - t) / 60_000
            rec_count[min(3, len(recordings_at(meeting, (t + u) / 2)))] += (u - t) / 60_000
            tx = {s["tag"] for s in segs if s["start"] < u and s["end"] > t}
            tx_count[min(3, len(tx))] += (u - t) / 60_000
            inside = [r for r in speech if to_ms(r["start_local"]) < u and to_ms(r["end_local"]) > t]
            if not inside:
                silent_min.append(t)
            else:
                dur = lambda r: max(1.0, to_ms(r["end_local"]) - to_ms(r["start_local"]))  # noqa: E731
                low = sum(dur(r) for r in inside if r["confidence"] == "low")
                if low > 0.5 * sum(dur(r) for r in inside):
                    low_min.append(t)
                if any("[ไม่ได้ยิน" in r["text"] for r in inside):
                    unheard_min.append(t)
            t = u
    wins = Counter(FULL.get(x, x) for r in speech for x in r["sources"])
    missing = uncovered_speech(meeting, speech, to_ms)
    m = MEETINGS[meeting]
    lines = [f"## {m['date']} {hms(spans[0][0])[:5]} — {m['title']} (`{meeting}`)", "",
             f"- ช่วงที่มีการอัด: " + ", ".join(f"{hms(a)}–{hms(b)}" for a, b in spans) + f" (รวม {total:.1f} นาที)",
             "- เครื่องอัด: " + ", ".join(f"{SOURCES[s]['kind']} `{SOURCES[s]['id']}`" for s in m["sources"]),
             f"- นาทีที่มีเครื่องอัด 1 / 2 / 3+ เครื่อง: {rec_count[1]:.1f} / {rec_count[2]:.1f} / {rec_count[3]:.1f}",
             f"- นาทีที่มี transcript 0 / 1 / 2 / 3+ แหล่ง: {tx_count[0]:.1f} / {tx_count[1]:.1f} / {tx_count[2]:.1f} / {tx_count[3]:.1f}",
             f"- นาทีที่ไม่มีเสียงพูด ({len(silent_min)}): {ranges(silent_min)}",
             f"- นาทีที่ส่วนใหญ่ความเชื่อมั่น low ({len(low_min)}): {ranges(low_min)}",
             f"- นาทีที่มี `[ไม่ได้ยิน]` ({len(unheard_min)}): {ranges(unheard_min)}",
             f"- segment ที่รวมแล้ว {len(speech)} ช่วง: high {sum(r['confidence'] == 'high' for r in speech)} / "
             f"medium {sum(r['confidence'] == 'medium' for r in speech)} / low {sum(r['confidence'] == 'low' for r in speech)}",
             "- แหล่งที่ถูกใช้ (จำนวน segment ที่อ้างแหล่งนั้น): " + ", ".join(f"{k} {v}" for k, v in wins.most_common()),
             f"- เสียงพูดที่ตัวตรวจจับเสียง (VAD) ได้ยินแต่ไม่มีใน transcript ≥10 วินาที ({len(missing)} ช่วง): "
             + (", ".join(f"{hms(a)}–{hms(b)}" for a, b in missing) or "—"), ""]
    return lines


def offsets_section() -> list[str]:
    offs = json.loads((WORK / "offsets.json").read_text())
    probes = json.loads((WORK / "probes.json").read_text())
    lines = ["## การวางเวลาให้ตรงกัน (offsets)", "",
             "| ไฟล์ | เวลาเริ่มตามไฟล์/manifest | เวลาเริ่มที่ใช้ | ต่างกัน | วิธี |", "|---|---|---|---|---|"]
    for src in SOURCES:
        o = offs[src]
        lines.append(f"| {SOURCES[src]['kind']} `{SOURCES[src]['id']}` | {hms(nominal_start_epoch_ms(src))} | "
                     f"{o['start_local']} | {o['nominal_start_offset_ms'] / 1000:+.2f} s | {o.get('note', 'Wispr live: startEpochMs − startRecordingMs')} |")
    lines += ["", "Probe ทุก 60 วินาที (envelope cross-correlation ±25 s แล้ว GCC-PHAT ±60 ms):", ""]
    for pair, pl in probes.items():
        used = [p for p in pl if p.get("used")]
        if used:
            lines.append(f"- `{pair}`: ใช้ {len(used)}/{len(pl)} จุด, delta {used[0]['delta']:+.3f} → {used[-1]['delta']:+.3f} s")
    lines += ["", "Plaud มักทำเสียงหายเป็นช่วงสั้น ๆ ระหว่างอัด — การวางเวลาใช้จุด probe ทุก 60 วินาทีจึงไม่สะสมคลาดเคลื่อน; "
              "ไฟล์ที่ไม่มีเครื่อง Mac อัดพร้อมกัน (borrow_offset) ใช้ค่าชดเชยของเครื่องเดียวกัน เวลาอาจคลาดได้ไม่กี่วินาที", ""]
    return lines


def main():
    lines = [f"# Coverage: {TITLE}", "",
             "สร้างด้วย `coverage.py` นับเป็นนาทีบนเวลาจริง (เวลาท้องถิ่น) ตลอดช่วงที่มีเครื่องอัด", "",
             "คำอธิบาย: \"เครื่องอัด\" = ไฟล์เสียงที่อัดอยู่ในนาทีนั้น; \"transcript\" = จำนวนแหล่งข้อความที่มีคำในนาทีนั้น "
             "(PL = Plaud, WL = Wispr live, WR = Wispr refined, TH = Whisper Thai, V3 = Whisper large-v3, TA = Whisper Thai บนเครื่องอัดที่ 2)", ""]
    for meeting in MEETINGS:
        lines += meeting_section(meeting, transcript_rows(meeting))
    lines += offsets_section()
    (OUT / "notes").mkdir(exist_ok=True)
    (OUT / "notes" / "coverage.md").write_text("\n".join(lines))
    print("coverage.md written")


if __name__ == "__main__":
    main()
