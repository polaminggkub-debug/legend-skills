# Compact one raw `rea capture-browser-scenario` result for a model to read: API requests only (method, path,
# select, other query, body, status, rows, response key count), console lines and page errors. No DOM, no
# screenshots, no response bodies, so a capture of megabytes becomes a few KB.
# usage: web_compact.py <raw.json> [--api REGEX]  -> JSON on stdout
#   --api  which request paths count as API calls (default: Supabase/REST/GraphQL style paths)
import argparse, base64, json, re, sys, urllib.parse

ap = argparse.ArgumentParser()
ap.add_argument('raw')
ap.add_argument('--api', default=r'^/(rest|auth|functions|storage|api|graphql|rpc)(/|$)')
a = ap.parse_args()
API = re.compile(a.api)
# Values that change on every run (timestamps, UUIDs, long tokens) would make every request look new in a diff.
TS = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?')
UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)
TOK = re.compile(r'[A-Za-z0-9_-]{32,}(\.[A-Za-z0-9_-]+){0,2}')
def norm(s): return TOK.sub('<TOKEN>', UUID.sub('<UUID>', TS.sub('<TS>', s)))

n = json.load(open(a.raw))['data']['normalized_result']
steps = {s['step_index']: s['step_id'] for s in n['steps']}
content = {}
for e in n['events']['items']:
    if e['kind'] == 'network-content' and e['body']['state'] == 'captured':
        try: content[(e['source_event_sequence'], e['phase'])] = json.loads(base64.b64decode(e['body']['content']))
        except Exception: pass
reqs, out, con = {}, [], []
for e in n['events']['items']:
    k = e['kind']
    if k == 'request':
        u = urllib.parse.urlsplit(e['url']['url'])
        if not API.search(u.path): continue
        q = urllib.parse.parse_qsl(u.query, keep_blank_values=True)
        body = content.get((e['sequence'], 'request')) if '/auth/' not in u.path else None  # never keep passwords
        reqs[e['transaction_id']] = r = {'step': steps[e['step_index']], 'm': e['method'], 'path': norm(u.path),
            'select': next((v for kk, v in q if kk == 'select'), None),
            'q': norm('&'.join(f'{kk}={v}' for kk, v in q if kk != 'select'))[:160],
            'body': norm(json.dumps(body, sort_keys=True, ensure_ascii=False))[:120] if body is not None else '',
            'status': None, 'rows': None, 'keys': None}
        out.append(r)
    elif k in ('response', 'request-failed') and e['transaction_id'] in reqs:
        r = reqs[e['transaction_id']]
        if k == 'request-failed': r['status'] = 'failed:' + str(e.get('failure')); continue
        r['status'] = e['status']; j = content.get((e['sequence'], 'response'))
        if isinstance(j, list):
            r['rows'] = len(j); r['keys'] = len({kk for x in j if isinstance(x, dict) for kk in x}) or None
        elif isinstance(j, dict):
            r['keys'] = len(j)
    elif k == 'console':
        con.append({'step': steps[e['step_index']], 'level': e['level'], 'text': norm(e['text'])[:200]})
    elif k == 'page-error':
        con.append({'step': steps[e['step_index']], 'level': 'page-error', 'text': norm(e['message'])[:200]})
json.dump({'scenario': a.raw.rsplit('/', 1)[-1], 'duration_ms': n['duration_ms'],
           'steps_failed': [f"{s['step_id']}: {(s['error'] or '')[:100]}" for s in n['steps'] if s['status'] != 'completed'],
           'requests': out, 'console': con}, sys.stdout, ensure_ascii=False, indent=0)
