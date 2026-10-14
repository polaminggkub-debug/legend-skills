"""Build the speaker labelling page: $MEETING_AUDIO/speakers/index.html + clips.

For every global speaker S1..Sn: the cleanest 6-12 s stretch where only that speaker talks
(diarization turn inside one high-confidence transcript segment of that speaker, Wispr mic first),
cut from the ORIGINAL audio (read only) to S<n>.opus (+ S<n>.m4a for Safari), up to two extra short
clips from other meetings, the sentence spoken in the clip, a name box per speaker and a copy control that
copies {"S1": "name", ...} as JSON for apply_speaker_names.py.
Usage: python make_speaker_page.py
"""
from __future__ import annotations

import html
import json
import subprocess
from collections import defaultdict
from datetime import datetime

from config import AUDIO, MEETINGS, OUT, SOURCES, SPEAKERS_DIR, TITLE, WORK, epoch_to_source_ms, hms
from timeline import recordings_at

PREFER = ["wispr", "plaud", "quicktime"]


def transcript_speech() -> dict:
    out = defaultdict(list)
    for part in json.loads((OUT / "transcript" / "index.json").read_text()):
        for s in json.loads((OUT / "transcript" / f"{part['file']}.json").read_text()):
            if s.get("kind", "speech") == "speech":
                t0 = datetime.fromisoformat(s["start_local"]).timestamp() * 1000
                t1 = datetime.fromisoformat(s["end_local"]).timestamp() * 1000
                out[part["meeting"]].append({**s, "t0": t0, "t1": t1, "part": part["file"]})
    return out


def candidates(turns: dict, speech: dict) -> dict:
    """speaker -> [(score, meeting, a, b, text)] for clean single-speaker stretches."""
    cands = defaultdict(list)
    for meeting, tl in turns.items():
        for t0, t1, spk in tl:
            if t1 - t0 < 6000:
                continue
            for s in speech[meeting]:
                if s["speaker_id"] != spk or s["confidence"] != "high" or "[" in s["text"]:
                    continue
                a, b = max(t0, s["t0"]), min(t1, s["t1"])
                if b - a < 6000:
                    continue
                b = min(b, a + 12000)
                src = sorted(recordings_at(meeting, a), key=lambda x: PREFER.index(SOURCES[x]["kind"]))
                score = (b - a) / 1000 + (3 if src and SOURCES[src[0]]["kind"] == "wispr" else 0) + min(len(s["text"]), 120) / 60
                cands[spk].append((score, meeting, a, b, s["text"]))
    return cands


def fallback(speech: dict, spk: str) -> list:
    """For ids without diarization turns (e.g. a voice only on Wispr's system channel): the longest
    clean transcript segments of that speaker."""
    out = []
    for meeting, rows in speech.items():
        for s in rows:
            if s["speaker_id"] == spk and "[" not in s["text"] and s["t1"] - s["t0"] >= 3000:
                b = min(s["t1"], s["t0"] + 12000)
                out.append(((b - s["t0"]) / 1000 + (2 if s["confidence"] == "high" else 0), meeting, s["t0"], b, s["text"]))
    return out


def louder_channel(src: str, a: float, b: float) -> str:
    """Wispr files are stereo (mic, system audio): take the channel that carries the voice."""
    import numpy as np
    import soundfile as sf
    pos0, pos1 = epoch_to_source_ms(src, a) / 1000, epoch_to_source_ms(src, b) / 1000
    rms = {}
    for ch in ("ch1", "ch2"):
        x, _ = sf.read(WORK / "wav" / f"{src}.{ch}.wav", start=int(pos0 * 16000), stop=int(pos1 * 16000), dtype="float32")
        rms[ch] = float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0
    return "pan=mono|c0=c0" if rms["ch1"] >= rms["ch2"] else "pan=mono|c0=c1"


def cut(meeting: str, a: float, b: float, stem: str) -> str:
    src = sorted((x for x in recordings_at(meeting, a) if epoch_to_source_ms(x, b) is not None),
                 key=lambda x: PREFER.index(SOURCES[x]["kind"]))[0]
    pos = epoch_to_source_ms(src, a) / 1000
    files = SOURCES[src]["files"]
    part = 0
    if len(files) > 1:  # QuickTime parts are 3600 s each
        part, pos = int(pos // 3600), pos % 3600
    inp = AUDIO / files[part]
    pan = ["-af", louder_channel(src, a, b)] if SOURCES[src]["kind"] == "wispr" else ["-ac", "1"]
    for ext, codec in (("opus", ["-c:a", "libopus", "-b:a", "48k"]), ("m4a", ["-c:a", "aac", "-b:a", "96k"])):
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{pos:.2f}", "-t", f"{(b - a) / 1000:.2f}",
                        "-i", str(inp), *pan, "-ar", "48000", *codec, str(SPEAKERS_DIR / f"{stem}.{ext}")], check=True)
    return src


def main():
    SPEAKERS_DIR.mkdir(parents=True, exist_ok=True)
    turns = json.loads((WORK / "diar" / "turns.json").read_text())
    clusters = json.loads((WORK / "diar" / "clusters.json").read_text())
    speech = transcript_speech()
    cands = candidates(turns, speech)
    talk = defaultdict(float)
    where = defaultdict(set)
    for meeting, rows in speech.items():
        for s in rows:
            talk[s["speaker_id"]] += (s["t1"] - s["t0"]) / 60000
            where[s["speaker_id"]].add(meeting)
    rows, report = [], []
    for spk in sorted(talk, key=lambda k: int(k[1:])):
        best = sorted(cands.get(spk, []) or fallback(speech, spk), reverse=True)
        if not best:
            report.append(f"{spk}: no clean 6 s stretch")
            continue
        _, meeting, a, b, text = best[0]
        src = cut(meeting, a, b, spk)
        extra = []
        for _, m2, a2, b2, t2 in best[1:]:
            if m2 != meeting and m2 not in [e[0] for e in extra] and len(extra) < 2:
                cut(m2, a2, min(b2, a2 + 8000), f"{spk}_{len(extra) + 2}")
                extra.append((m2, a2, t2))
        rows.append({"spk": spk, "min": talk[spk], "meetings": sorted(where[spk]), "meeting": meeting, "a": a, "b": b,
                     "text": text, "src": src, "extra": extra,
                     "labels": sorted(k for k, v in clusters["clusters"].items() if v["global"] == spk)})
    (SPEAKERS_DIR / "index.html").write_text(page(rows))
    print(f"{len(rows)} speakers on the page; {report or 'all have clips'}")


def page(rows: list[dict]) -> str:
    def meet(m):
        return f"{MEETINGS[m]['date'][5:]} {html.escape(MEETINGS[m]['title'])}"
    cards = []
    for r in rows:
        extra = "".join(
            f'<div class="extra"><audio controls preload="none"><source src="{r["spk"]}_{i}.opus" type="audio/ogg; codecs=opus">'
            f'<source src="{r["spk"]}_{i}.m4a" type="audio/mp4"></audio> <span>{meet(m)} {hms(a)} · “{html.escape(t[:90])}”</span></div>'
            for i, (m, a, t) in enumerate(r["extra"], 2))
        cards.append(f"""
<section class="card">
  <h2>{r['spk']}</h2>
  <p class="meta">พูดรวม ~{r['min']:.0f} นาที · อยู่ใน: {'; '.join(meet(m) for m in r['meetings'])}</p>
  <audio controls preload="none"><source src="{r['spk']}.opus" type="audio/ogg; codecs=opus"><source src="{r['spk']}.m4a" type="audio/mp4"></audio>
  <p class="quote">“{html.escape(r['text'])}”<br><small>{meet(r['meeting'])} · {hms(r['a'])}–{hms(r['b'])} · จากไฟล์ {html.escape(SOURCES[r['src']]['id'])}</small></p>
  {extra}
  <label>ชื่อ: <input data-spk="{r['spk']}" placeholder="เช่น ชื่อ / ตำแหน่ง"></label>
  <p class="labels">กลุ่มเสียงที่รวมเป็นคนนี้: {', '.join(r['labels'])}</p>
</section>""")
    return f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8"><title>ใส่ชื่อผู้พูด — {html.escape(TITLE)}</title>
<style>
body{{font-family:-apple-system,"Sarabun",sans-serif;max-width:900px;margin:24px auto;padding:0 16px;color:#222}}
.card{{border:1px solid #ccc;border-radius:8px;padding:12px 16px;margin:12px 0}}
.card h2{{margin:0 0 4px}} .meta,.labels{{color:#666;font-size:13px}} .quote{{background:#f6f6f6;padding:8px;border-radius:6px}}
.extra{{font-size:13px;color:#444;margin:4px 0}} .extra audio{{height:28px;vertical-align:middle}}
input{{font-size:16px;padding:4px 8px;width:320px}} textarea{{width:100%;height:120px}}
#copy{{width:auto;font-size:16px;padding:8px 16px;margin:8px 0}}
</style></head><body>
<h1>ใส่ชื่อผู้พูด</h1>
<p>ฟังเสียงแต่ละคน (ตัวอย่างหลัก 6–12 วินาที และตัวอย่างเพิ่มจากการประชุมอื่น ถ้ามี) แล้วพิมพ์ชื่อ.
ถ้าสองหมายเลขเป็นคนเดียวกัน ใส่ชื่อเดียวกันได้. ถ้าตัวอย่างหลักกับตัวอย่างเพิ่มเป็นคนละคน ให้จดไว้ในช่องชื่อ เช่น "คุณเอ (ตัวอย่าง 2 ไม่ใช่)".
เสร็จแล้วกด <b>Copy JSON</b> บันทึกเป็นไฟล์ <code>names.json</code> แล้วรัน
<code>python3 apply_speaker_names.py names.json</code></p>
{''.join(cards)}
<input type="submit" id="copy" value="Copy JSON">
<textarea id="out" readonly></textarea>
<script>
function collect(){{const o={{}};document.querySelectorAll('input[data-spk]').forEach(i=>{{if(i.value.trim())o[i.dataset.spk]=i.value.trim()}});return JSON.stringify(o,null,1)}}
document.getElementById('copy').onclick=async()=>{{const t=collect();const ta=document.getElementById('out');ta.value=t;
try{{await navigator.clipboard.writeText(t)}}catch(e){{ta.select();document.execCommand('copy')}}}};
document.querySelectorAll('input[data-spk]').forEach(i=>i.addEventListener('input',()=>document.getElementById('out').value=collect()));
</script>
</body></html>
"""


if __name__ == "__main__":
    main()
