"""Render one transcript part (JSON array) as readable Markdown. Used by assemble.py and
apply_speaker_names.py so both always produce the same layout.
Library module, nothing to run. Usage: from render import render; render(meta, segs) -> Markdown text."""
from __future__ import annotations

from collections import Counter

SOURCE_NAMES = {
    "wispr-live": "Wispr live", "wispr-refined": "Wispr refined", "plaud": "Plaud transcript",
    "whisper-th": "Whisper Thai fine-tune", "whisper-large-v3": "Whisper large-v3",
    "whisper-th-2nd-mic": "Whisper Thai (เครื่องอัดที่ 2)",
}


def hhmmss(local_iso: str) -> str:
    return local_iso[11:19]


def render(meta: dict, segs: list[dict]) -> str:
    speech = [s for s in segs if s.get("kind", "speech") == "speech"]
    conf = Counter(s["confidence"] for s in speech)
    unsure = sum(s["text"].count("[?]") for s in speech)
    unheard = sum(s["text"].count("[ไม่ได้ยิน") for s in speech)
    speakers = Counter(s["speaker"] for s in speech)
    used = sorted({x for s in speech for x in s["sources"]})
    lines = [
        f"# {meta['date']} {meta['start_hm']} — {meta['title']}",
        "",
        f"- ช่วงเวลา: {meta['start_hms']}–{meta['end_hms']} (เวลาท้องถิ่น; คลาดเคลื่อนได้ราว ±3 วินาที)",
        f"- หัวข้อ: {meta['topic_th']}",
        f"- เสียงต้นฉบับ: {meta['recordings']}",
        f"- Transcript ที่นำมารวม: {', '.join(SOURCE_NAMES.get(x, x) for x in used)}",
        "- ผู้พูด: " + ", ".join(f"{k} ({n} ช่วง)" for k, n in speakers.most_common())
        + " — ใส่ชื่อจริงด้วย `apply_speaker_names.py names.json`",
        f"- ความเชื่อมั่น: high {conf['high']} / medium {conf['medium']} / low {conf['low']} ช่วง · "
        f"คำที่ไม่แน่ใจ `[?]` {unsure} จุด · `[ไม่ได้ยิน]` {unheard} จุด",
        f"- `start_ms` ใน JSON นับจาก {meta['origin_local']} ({meta['origin_note']})",
        "",
        "สัญลักษณ์: ⟨medium⟩ / ⟨low⟩ = ความเชื่อมั่นของช่วงนั้น (ไม่มีเครื่องหมาย = high); `[?]` = คำที่ไม่แน่ใจ;"
        " `[ไม่ได้ยิน]` = มีเสียงพูดแต่ฟังไม่ออก; 📷 = owner กดปุ่มถ่ายภาพใน Plaud ณ จุดนั้น",
        "",
        "---",
        "",
    ]
    for s in segs:
        t = hhmmss(s["start_local"])
        kind = s.get("kind", "speech")
        if kind == "mark":
            lines.append(f"> 📷 **[{t}]** {s['text']}")
        elif kind == "silence":
            lines.append(f"> ⏸ **[{t}–{hhmmss(s['end_local'])}]** {s['text']}")
        else:
            tag = "" if s["confidence"] == "high" else f" ⟨{s['confidence']}⟩"
            lines.append(f"**[{t}] {s['speaker']}:** {s['text']}{tag}")
        lines.append("")
    return "\n".join(lines)
