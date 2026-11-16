# Sweep shipped JS/CSS/HTML files for what must not ship, so a model reads hit lines instead of megabytes of bundle.
# Point it at the served build folder, or a folder of scripts saved by `rea export-web-scripts`.
# usage: bundle_sweep.py <dir> [--max 6]  -> text on stdout, one block per rule, file:offset and a short snippet
import argparse, base64, json, os, re

ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--max', type=int, default=6)
a = ap.parse_args()
RULES = {
    'jwt': r'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
    'secret-key': r'service_role|sk_(live|test)_[A-Za-z0-9]{8,}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY',
    'local-url': r'https?://(localhost|127\.0\.0\.\d|0\.0\.0\.0)(:\d+)?[^"\'\s]*',
    'private-ip': r'\b(10\.\d{1,3}|192\.168|172\.(1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b',
    'console-call': r'console\.(log|debug|info|trace)\(',
    'debugger': r'\bdebugger\b',
    'demo-test-code': r'demo[_-]?seed|seed[_-]?demo|fixture|faker|__test__|test[_-]?mode|mock[A-Z_]',
    'source-map': r'sourceMappingURL=',
    'third-party-host': r'https?://(?![^/"\']*(supabase\.co|w3\.org|localhost|127\.0\.0))[a-z0-9.-]+\.[a-z]{2,}',
}
RX = {k: re.compile(v) for k, v in RULES.items()}

def jwt_role(t):
    try: return json.loads(base64.urlsafe_b64decode(t.split('.')[1] + '==')).get('role')
    except Exception: return None

hits = {k: [] for k in RULES}; counts = {k: 0 for k in RULES}; files = 0
for root, _, names in os.walk(a.dir):
    for f in names:
        if not f.endswith(('.js', '.mjs', '.css', '.html', '.json', '.map')): continue
        p = os.path.join(root, f); files += 1
        try: s = open(p, encoding='utf-8', errors='replace').read()
        except Exception: continue
        for k, rx in RX.items():
            for m in rx.finditer(s):
                counts[k] += 1
                if len(hits[k]) < a.max:
                    t = m.group(0)
                    extra = f' role={jwt_role(t)}' if k == 'jwt' else ''
                    ctx = s[max(0, m.start() - 50):m.end() + 50].replace('\n', ' ')
                    hits[k].append(f'{os.path.relpath(p, a.dir)}:{m.start()}{extra}  …{ctx[:200]}…')
print(f'swept {files} files in {a.dir}')
for k in RULES:
    print(f'## {k}: {counts[k]} hits')
    for h in hits[k]: print('  ', h)
