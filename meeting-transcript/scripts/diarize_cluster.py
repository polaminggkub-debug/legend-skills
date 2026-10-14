"""Cluster speakers per recording stretch, link clusters across recordings, write global turns.

1. Per recording stretch (RECS): average-linkage clustering (cosine) of the ECAPA windows with an
   adaptive cut, k-means refinement, merging of near-identical centroids and dissolving of small
   in-between (overlap) clusters — see local_clusters.
2. Links between stretches, strongest first, never joining two groups that already hold a cluster
   of the same stretch (cannot-link: clusters of one stretch are different people by construction):
   - simultaneity: two recordings of the same moment (Plaud vs Wispr) -> overlap table of labels;
   - voice similarity: cosine of cluster centroids (mutual best match >= LINK_SIM).
3. Global ids S1..Sn ordered by speaking time; ids already given to a local cluster are kept in
   WORK/diar/ids.json so a re-run never renumbers people.
4. Turns per meeting from the main stretch of each moment (MAIN), 5-window majority smoothing.
Stretches, simultaneous pairs and main stretches come from meeting.json "diarize" (see config.py).
Writes WORK/diar/turns.json and WORK/diar/clusters.json. Usage: python diarize_cluster.py
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage

from config import CFG, WORK, epoch_to_source_ms, source_to_epoch_ms

# Thresholds below encode lessons (references/lessons.md, "Diarization"); change them only with a reason.
MIN_S = 25.0      # clusters with less speech are folded into the nearest big one
MERGE_SIM = 0.75  # centroids closer than this inside one stretch are one speaker
LINK_SIM = 0.75   # centroid cosine needed for a voice link (conservative: two ids for one person are
                  # fixed by naming both the same; one id for two people is not fixable)
COVER = 0.70      # first cut where clusters >= MIN_S cover 70 % of windows (refinement then merges)
HOP = 0.75
FAR = 1e9         # "to the end of the file"
DIAR = CFG.get("diarize", {})
# key -> (src, from_s, to_s, merge_sim). A far-field recorder on the table forms one "hub" cluster similar
# to every voice, so leave it out; a stretch of a wearable mic that is far-field needs a finer merge_sim.
RECS = {k: (v[0], v[1] or 0, v[2] if v[2] is not None else FAR, v[3] if v[3] is not None else MERGE_SIM)
        for k, v in DIAR["recs"].items()}
SIMULTANEOUS = [tuple(p) for p in DIAR.get("simultaneous", [])]
# meeting -> [(rec key, from_s, to_s)] stretches that carry the speaker turns (positions in that src)
MAIN = {m: [(k, a or 0, b if b is not None else FAR) for k, a, b in rows] for m, rows in DIAR["main"].items()}


def normed(v: np.ndarray) -> np.ndarray:
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)


def adaptive_cut(sub: np.ndarray, scale: float, cover: float = COVER) -> list[np.ndarray]:
    z = linkage(sub, method="average", metric="cosine")
    for t in np.arange(0.70, 0.90, 0.01):
        lab = fcluster(z, t, criterion="distance")
        sizes = Counter(lab)
        big = [k for k, n in sizes.items() if n * HOP * scale >= MIN_S]
        if sum(sizes[k] for k in big) >= cover * len(sub):
            break
    return [normed(sub[lab == k].mean(0)) for k in big]


def local_clusters(emb: np.ndarray, merge_sim: float = MERGE_SIM) -> np.ndarray:
    sub = emb if len(emb) <= 14000 else emb[np.random.default_rng(0).choice(len(emb), 14000, replace=False)]
    cents = adaptive_cut(sub, len(emb) / len(sub))
    for _ in range(8):  # k-means style refinement + merging of near-identical centroids
        lab = np.argmax(emb @ np.stack(cents).T, axis=1)
        cents = [normed(emb[lab == k].mean(0)) for k in range(len(cents)) if (lab == k).sum() * HOP >= MIN_S]
        weights = [int((np.argmax(emb @ np.stack(cents).T, axis=1) == k).sum()) for k in range(len(cents))]
        while len(cents) > 1:
            sim = np.stack(cents) @ np.stack(cents).T - 2 * np.eye(len(cents))
            i, j = np.unravel_index(np.argmax(sim), sim.shape)
            if sim[i, j] < merge_sim:
                break
            merged = normed(cents[i] * weights[i] + cents[j] * weights[j])
            w = weights[i] + weights[j]
            cents = [c for k, c in enumerate(cents) if k not in (i, j)] + [merged]
            weights = [x for k, x in enumerate(weights) if k not in (i, j)] + [w]
    lab = np.argmax(emb @ np.stack(cents).T, axis=1)
    cents = [normed(emb[lab == k].mean(0)) for k in range(len(cents))]
    for k in sorted(range(len(cents)), key=lambda k: (lab == k).sum()):  # dissolve overlap clusters
        sims = sorted((float(cents[k] @ cents[j]) for j in range(len(cents)) if j != k and cents[j] is not None), reverse=True)
        if cents[k] is not None and len(sims) >= 2 and (lab == k).mean() < 0.15 and sims[0] >= 0.70 and sims[1] >= 0.68:
            cents[k] = None
    live = [k for k in range(len(cents)) if cents[k] is not None]
    lab = np.array(live)[np.argmax(emb @ np.stack([cents[k] for k in live]).T, axis=1)]
    order = [k for k, _ in Counter(lab).most_common()]
    return np.array([order.index(k) for k in lab])


def smooth(lab: np.ndarray, t0: np.ndarray, k: int = 5) -> np.ndarray:
    out = lab.copy()
    for i in range(len(lab)):
        near = [lab[j] for j in range(max(0, i - k // 2), min(len(lab), i + k // 2 + 1)) if abs(t0[j] - t0[i]) <= HOP * k]
        out[i] = Counter(near).most_common(1)[0][0]
    return out


def label_at(rec: dict, pos_s: float):
    i = np.searchsorted(rec["t0"] + 0.75, pos_s)
    for j in (i - 1, i, i + 1):
        if 0 <= j < len(rec["t0"]) and rec["t0"][j] + 0.375 <= pos_s <= rec["t0"][j] + 1.125:
            return rec["lab"][j]
    return None


class Groups:
    """Union-find with cannot-link: a group may hold at most one cluster per stretch."""

    def __init__(self, keys):
        self.p = {k: k for k in keys}
        self.members = {k: {k} for k in keys}

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return True
        if {m[0] for m in self.members[ra]} & {m[0] for m in self.members[rb]}:
            return False
        self.p[ra] = rb
        self.members[rb] |= self.members.pop(ra)
        return True


def candidate_links(recs: dict, cents: dict) -> tuple[list[dict], dict]:
    links = []
    for a, b in SIMULTANEOUS:
        table = defaultdict(float)
        src_a, src_b = RECS[a][0], RECS[b][0]
        for t, la in zip(recs[a]["t0"], recs[a]["lab"]):
            pos_b = epoch_to_source_ms(src_b, source_to_epoch_ms(src_a, (t + 0.75) * 1000))
            lb = label_at(recs[b], pos_b / 1000) if pos_b is not None else None
            if lb is not None:
                table[(la, lb)] += HOP
        for (la, lb), v in table.items():
            sa = v / sum(x for (i, _), x in table.items() if i == la)
            sb = v / sum(x for (_, j), x in table.items() if j == lb)
            if v >= 20 and sa >= 0.5 and sb >= 0.4:
                links.append({"a": (a, int(la)), "b": (b, int(lb)), "kind": "simultaneous", "overlap_s": round(v),
                              "score": 1 + min(sa, sb), "share_a": round(sa, 2), "share_b": round(sb, 2)})
    keys = list(cents)
    sim = {(x, y): float(cents[x] @ cents[y]) for x in keys for y in keys if x[0] != y[0]}
    for x in keys:
        for other in RECS:
            cand = [(sim[(x, y)], y) for y in keys if y[0] == other and other != x[0]]
            if not cand:
                continue
            s, y = max(cand)
            back = max((sim[(y, z)], z) for z in keys if z[0] == x[0])[1]
            if s >= LINK_SIM and back == x and x < y:
                links.append({"a": x, "b": y, "kind": "voice", "cos": round(s, 3), "score": s})
    return sorted(links, key=lambda ln: -ln["score"]), sim


def assign_ids(groups: dict, secs: dict) -> dict:
    """Keep ids from ids.json; new groups get the next numbers by speaking time."""
    path = WORK / "diar" / "ids.json"
    anchored = json.loads(path.read_text()) if path.exists() else {}
    gid, used = {}, set()
    for root, members in groups.items():
        old = {anchored[f"{m[0]}:{m[1]}"] for m in members if f"{m[0]}:{m[1]}" in anchored}
        if len(old) == 1 and old.isdisjoint(used):
            gid[root] = old.pop()
            used.add(gid[root])
    nxt = max([int(v[1:]) for v in used] + [0]) + 1
    for root in sorted((r for r in groups if r not in gid), key=lambda r: -sum(secs[m] for m in groups[r])):
        gid[root] = f"S{nxt}"
        nxt += 1
    out = {f"{m[0]}:{m[1]}": gid[r] for r, ms in groups.items() for m in ms}
    path.write_text(json.dumps(out, indent=1))
    return out


def turns_for(recs: dict, ids: dict) -> dict:
    turns = {}
    for meeting, parts in MAIN.items():
        out = []
        for key, lo, hi in parts:
            src, r = RECS[key][0], recs[key]
            for t, lab in zip(r["t0"], r["lab"]):
                c = t + 0.75
                if lo <= c <= hi:
                    a = source_to_epoch_ms(src, (c - HOP / 2) * 1000)
                    b = source_to_epoch_ms(src, (c + HOP / 2) * 1000)
                    spk = ids[f"{key}:{lab}"]
                    if out and out[-1][2] == spk and a - out[-1][1] < 1500:
                        out[-1][1] = max(out[-1][1], b)
                    else:
                        out.append([a, b, spk])
        turns[meeting] = sorted(out)
    return turns


def main():
    recs, data = {}, {}
    for key, (src, lo, hi, msim) in RECS.items():
        if src not in data:
            data[src] = np.load(WORK / "diar" / f"{src}.npz")
        d = data[src]
        m = (d["t0"] >= lo) & (d["t0"] < hi)
        lab = smooth(local_clusters(d["emb"][m], msim), d["t0"][m])
        recs[key] = {"t0": d["t0"][m], "emb": d["emb"][m], "lab": lab}
        print(key, "clusters (min):", {int(k): round(n * HOP / 60, 1) for k, n in sorted(Counter(lab).items())}, flush=True)
    cents = {(s, int(k)): normed(r["emb"][r["lab"] == k].mean(0)) for s, r in recs.items() for k in np.unique(r["lab"])}
    secs = {(s, int(k)): float((r["lab"] == k).sum() * HOP) for s, r in recs.items() for k in np.unique(r["lab"])}
    groups = Groups(cents)
    links, sim = candidate_links(recs, cents)
    for ln in links:
        ln["applied"] = groups.union(ln["a"], ln["b"])
    ids = assign_ids({r: groups.members[r] for r in groups.members}, secs)
    (WORK / "diar" / "turns.json").write_text(json.dumps(turns_for(recs, ids)))
    clusters = {f"{k[0]}:{k[1]}": {"global": ids[f"{k[0]}:{k[1]}"], "speech_s": round(secs[k])} for k in cents}
    for ln in links:
        ln["a"], ln["b"] = f"{ln['a'][0]}:{ln['a'][1]}", f"{ln['b'][0]}:{ln['b'][1]}"
    simtab = {f"{x[0]}:{x[1]}|{y[0]}:{y[1]}": round(v, 3) for (x, y), v in sim.items() if x < y}
    (WORK / "diar" / "clusters.json").write_text(json.dumps(
        {"clusters": clusters, "links": links, "sim": simtab,
         "params": {"MIN_S": MIN_S, "MERGE_SIM": MERGE_SIM, "LINK_SIM": LINK_SIM, "COVER": COVER}}, indent=1))
    by = defaultdict(list)
    for k, v in clusters.items():
        by[v["global"]].append(k)
    for g in sorted(by, key=lambda g: int(g[1:])):
        print(f"{g}: {sum(clusters[k]['speech_s'] for k in by[g]) / 60:.1f} min <- {', '.join(by[g])}")
    for ln in links:
        print("link" if ln["applied"] else "REFUSED (cannot-link)", {k: v for k, v in ln.items() if k not in ("score", "applied")})


if __name__ == "__main__":
    main()
