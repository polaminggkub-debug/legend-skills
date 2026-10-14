"""Re-decide doubtful speaker ids in one transcript part, using lines the owner checked by ear.

    python relabel_by_anchors.py part.json audio.wav pos_key anchors.json out.json

anchors.json: {"S4": ["14:19:15", ...], "S3": [...], "trust": ["S4"], "doubt": ["S3", "S6"]}
  - each listed time is a segment start (HH:MM:SS) whose speaker the owner confirmed;
  - every segment of a "trust" id also seeds that id;
  - only segments of a "doubt" id, or marked "speaker_unsure", may change; unsure ones never seed.
Seeded k-means over ECAPA embeddings of each segment; a segment moves only when the new id wins by
MARGIN cosine. Prints a leave-one-out check on the owner's anchors. Writes {index: {...}} to out.json;
apply it on the Mac. CPU only; threads from env EMB_THREADS (default 8); model cache WORK/sb-ecapa.
An id with no member in a round has no centroid and is skipped for that round (no NaN).
Usage: python relabel_by_anchors.py part.json audio.wav pos_key anchors.json out.json
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
import torch

from config import WORK

# MARGIN: a segment moves only if the new id beats the old one by this cosine (conservative linking, lessons.md)
SR, MIN_S, MARGIN, ROUNDS = 16000, 1.0, 0.05, 5


def load(path_json, wav, key):
    segs = json.load(open(path_json, encoding="utf-8"))
    x, sr = sf.read(wav, dtype="float32")
    assert sr == SR, sr
    out = []
    for i, s in enumerate(segs):
        t0 = s.get("audio_pos_s", {}).get(key, s["start_ms"] / 1000)
        dur = (s["end_ms"] - s["start_ms"]) / 1000
        if dur >= MIN_S:
            out.append((i, x[int(t0 * SR):int((t0 + dur) * SR)]))
    return segs, out


def embed(chunks):
    from speechbrain.inference.speaker import EncoderClassifier
    torch.set_num_threads(int(os.environ.get("EMB_THREADS", "8")))
    clf = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                         savedir=str(WORK / "sb-ecapa"), run_opts={"device": "cpu"})
    embs = []
    with torch.no_grad():
        for _, a in chunks:
            e = clf.encode_batch(torch.from_numpy(a)[None]).squeeze().numpy()
            embs.append(e / np.linalg.norm(e))
    return np.stack(embs)


def similarities(ids, E, labels):
    """Cosine of every segment to each id's centroid. An id with no member has no centroid: its column is
    -1 (the lowest cosine), so it never wins the round."""
    sim = np.full((len(E), len(ids)), -1.0)
    for j, k in enumerate(ids):
        members = E[labels == k]
        if len(members):
            c = members.mean(0)
            sim[:, j] = E @ (c / np.linalg.norm(c))
    return sim


def doubtful(s, anchors):
    return s.get("speaker_unsure") or s["speaker_id"] in anchors["doubt"]


def assign(segs, idx, E, anchors, skip=None):
    ids = [k for k in anchors if k not in ("trust", "doubt")]
    pos = {i: n for n, i in enumerate(idx)}
    seed = {}
    for k in ids:
        for t in anchors[k]:
            i = max(j for j, s in enumerate(segs) if s["start_local"][11:19] <= t)
            if i in pos and i != skip:
                seed[pos[i]] = k
    for n, i in enumerate(idx):
        if segs[i]["speaker_id"] in anchors["trust"] and not doubtful(segs[i], anchors) and n not in seed and i != skip:
            seed.setdefault(n, segs[i]["speaker_id"])
    lab = np.array([seed.get(n, "") for n in range(len(idx))], dtype=object)
    for _ in range(ROUNDS):
        sim = similarities(ids, E, lab)
        new = lab.copy()
        for n, i in enumerate(idx):
            if n in seed or not doubtful(segs[i], anchors):
                continue
            new[n] = ids[int(sim[n].argmax())]
        lab = new
    return ids, sim, lab


def main():
    part, wav, key, anchors_p, out_p = sys.argv[1:6]
    anchors = json.load(open(anchors_p, encoding="utf-8"))
    segs, chunks = load(part, wav, key)
    idx = [i for i, _ in chunks]
    E = embed(chunks)
    ids, sim, lab = assign(segs, idx, E, anchors)
    out = {}
    for n, i in enumerate(idx):
        old = segs[i]["speaker_id"]
        if not doubtful(segs[i], anchors):
            continue
        order = np.argsort(-sim[n])
        best, second = ids[order[0]], ids[order[1]]
        margin = float(sim[n][order[0]] - sim[n][order[1]])
        out[i] = {"time": segs[i]["start_local"][11:19], "old": old,
                  "new": best if margin >= MARGIN else old, "best": best, "second": second,
                  "margin": round(margin, 3), "sure": margin >= MARGIN}
    # leave-one-out on the owner's anchors: hide each one, re-run, see where it lands
    pos = {i: n for n, i in enumerate(idx)}
    loo = []
    for k in ids:
        for t in anchors[k]:
            i = max(j for j, s in enumerate(segs) if s["start_local"][11:19] <= t)
            if i not in pos:
                continue
            _, s2, _ = assign(segs, idx, E, anchors, skip=i)
            loo.append((t, k, ids[int(s2[pos[i]].argmax())]))
    json.dump({"segments": out, "loo": loo}, open(out_p, "w"), ensure_ascii=False, indent=1)
    moved = sum(1 for v in out.values() if v["new"] != v["old"])
    print(f"doubtful segments {len(out)}, moved {moved}, unsure {sum(not v['sure'] for v in out.values())}")
    print("leave-one-out:", sum(a == b for _, a, b in loo), "/", len(loo), loo)


if __name__ == "__main__":
    main()
