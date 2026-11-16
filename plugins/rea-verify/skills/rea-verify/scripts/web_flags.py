# Rule flags per build plus a small diff between two builds, from web_compact.py output. This text is the only
# runtime output a model needs to read; raw captures stay on disk as evidence.
# Flags: select=* or wide responses, the same write/RPC sent more than once in one step, repeated GETs,
# failing requests, row counts above the page size, console warnings/errors and page errors.
# usage: web_flags.py <compactDir> --new <tag> [--old <tag>] [--page-size N] <scenario>...
#   reads <compactDir>/<scenario>-<tag>.json; without --old it prints flags only.
import argparse, collections, json

ap = argparse.ArgumentParser()
ap.add_argument('dir'); ap.add_argument('scenarios', nargs='+')
ap.add_argument('--new', required=True); ap.add_argument('--old')
ap.add_argument('--page-size', type=int, default=100)
ap.add_argument('--wide', type=int, default=12, help='response key count that counts as wide')
a = ap.parse_args()

def load(s, b):
    try: return json.load(open(f'{a.dir}/{s}-{b}.json'))
    except Exception as x: return {'error': str(x), 'requests': [], 'console': [], 'steps_failed': []}
def agg(X):
    g = {}
    for r in X['requests']:
        v = g.setdefault((r['m'], r['path'], r['q'], r['body']),
                         {'n': 0, 'per_step': collections.Counter(), 'select': set(), 'keys': 0, 'rows': 0, 'status': set()})
        v['n'] += 1; v['per_step'][r['step']] += 1; v['select'].add(r['select'] or '-')
        v['keys'] = max(v['keys'], r['keys'] or 0); v['rows'] = max(v['rows'], r['rows'] or 0); v['status'].add(str(r['status']))
    return g
def fmt(k, v):
    return f"{k[0]} {k[1]} select={'|'.join(sorted(v['select']))[:70]} {k[2][:60]} {k[3][:50]} n={v['n']} keys={v['keys']} rows={v['rows']}"
def by_path(g, pick):
    t = collections.defaultdict(lambda: [0, 0, 0])  # (method, path) -> [requests, max keys, max rows]
    for k, v in g.items():
        if pick(v): x = t[(k[0], k[1])]; x[0] += v['n']; x[1] = max(x[1], v['keys']); x[2] = max(x[2], v['rows'])
    return [f"{m} {p} n={x[0]} max_keys={x[1]} max_rows={x[2]}" for (m, p), x in sorted(t.items())]
def flags(b, g, X):
    star = by_path(g, lambda v: '*' in v['select'])
    wide = by_path(g, lambda v: '*' not in v['select'] and v['keys'] >= a.wide)
    big = by_path(g, lambda v: v['rows'] > a.page_size)
    dd = collections.defaultdict(lambda: [0, 0])  # (method, path) -> [steps with a repeat, max sends in one step]
    for k, v in g.items():
        c = max(v['per_step'].values())
        if c > 1: d = dd[(k[0], k[1])]; d[0] += sum(1 for x in v['per_step'].values() if x > 1); d[1] = max(d[1], c)
    dup = [f"{m} {p} up to {d[1]}x in one step, {d[0]} steps" for (m, p), d in sorted(dd.items()) if m != 'GET']
    dupget = [f"{m} {p} up to {d[1]}x in one step, {d[0]} steps" for (m, p), d in sorted(dd.items()) if m == 'GET']
    bad = [fmt(k, v) + ' status=' + ','.join(sorted(v['status'])) for k, v in g.items()
           if any(x.startswith('failed') or x[:1] in '45' for x in v['status'])]
    con = collections.Counter((c['level'], c['text'][:140]) for c in X['console']
                              if c['level'] in ('warning', 'warn', 'error', 'page-error', 'log'))
    print(f'  {b}: select=* {len(star)}, wide {len(wide)}, rows>{a.page_size} {len(big)}, dup write/rpc {len(dup)}, '
          f'dup GET {len(dupget)}, failing {len(bad)}, console {sum(con.values())}')
    for x in star: print(f'    {b} SELECT*', x)
    for x in wide: print(f'    {b} WIDE', x)
    for x in big: print(f'    {b} BIG', x)
    for x in dup: print(f'    {b} DUP', x)
    for x in dupget[:8]: print(f'    {b} DUPGET', x)
    for x in bad[:10]: print(f'    {b} FAIL', x)
    for (lvl, t), c in con.most_common(10): print(f'    {b} CONSOLE {lvl} x{c}: {t}')

for s in a.scenarios:
    N = load(s, a.new); gn = agg(N)
    O = load(s, a.old) if a.old else None; go = agg(O) if O else {}
    print(f'## {s}: {a.new} {len(N["requests"])} api requests' + (f', {a.old} {len(O["requests"])}' if O else ''))
    for b, X in ((a.new, N),) + (((a.old, O),) if O else ()):
        if X.get('error'): print(f'  {b} capture missing: {X["error"]}')
        for f in X['steps_failed']: print(f'  {b} step failed: {f}')
    flags(a.new, gn, N)
    if O is None: continue
    flags(a.old, go, O)
    print(f'  diff (- {a.old} only / + {a.new} only / ~ changed):')
    for k in sorted(set(go) | set(gn), key=str):
        o, w = go.get(k), gn.get(k)
        if o and not w: print('   -', fmt(k, o))
        elif w and not o: print('   +', fmt(k, w))
        elif (o['n'], o['keys'], o['select']) != (w['n'], w['keys'], w['select']):
            print('   ~', fmt(k, o), '=>', f"n={w['n']} keys={w['keys']} select={'|'.join(sorted(w['select']))[:70]}")
