# Trace one finding from minified code back to its source file:line with `rea trace-web-source-location`.
# Input: scripts exported by `rea export-web-scripts` from a capture of the source-map build (same commit, built with
# --sourcemap, never deployed), served at MAP_URL with its .map files in MAP_DIR.
# Finds the n-th match of <literal> in the exported script whose URL ends with <url-suffix>, traces that position,
# and appends a trimmed result to $EVIDENCE/rea-trace.json.
# usage: trace.py <id> <label> <exportDir> <url-suffix> <literal> [occurrence]
# env:   MAP_DIR      folder with the build's .map files (required, e.g. $WORK/builds/map/assets)
#        MAP_URL      URL that folder is served at (required, e.g. http://127.0.0.1:4473/assets)
#        EVIDENCE     report evidence folder (default ./evidence)
#        SOURCE_ROOT  cut reported source paths to start here, e.g. apps/web/ (optional)
#        WORK         gets rea-commands.txt (default ~/rea-work)
import json, os, subprocess, sys

if len(sys.argv) < 6:
    sys.exit(__doc__ or 'usage: trace.py <id> <label> <exportDir> <url-suffix> <literal> [occurrence]')
fid, label, exp, suffix, lit = sys.argv[1:6]
occ = int(sys.argv[6]) if len(sys.argv) > 6 else 0
map_dir, map_url = os.environ['MAP_DIR'], os.environ['MAP_URL'].rstrip('/')
evid = os.environ.get('EVIDENCE', 'evidence')
root = os.environ.get('SOURCE_ROOT', '')
work = os.path.expanduser(os.environ.get('WORK', '~/rea-work'))

man_path = f'{exp}/manifest.json'
man = json.load(open(man_path))
idx = next(i for i, s in enumerate(man['scripts'])
           if s['url'].endswith(suffix) and s['content']['state'] == 'exported')
ent = man['scripts'][idx]
served = open(f"{exp}/files/{ent['content']['relative_path']}", encoding='utf-8').read()
off = -1
for _ in range(occ + 1):
    off = served.index(lit, off + 1)
line0 = served.count('\n', 0, off)
col = off - (served.rfind('\n', 0, off) + 1)

base = os.path.basename(suffix)
cmd = ['rea', 'trace-web-source-location', man_path, str(idx), f'{map_dir}/{base}.map', f'{map_url}/{base}.map',
       str(line0 + 1), str(col), '--format', 'json', '--full-output']
p = subprocess.run(cmd, capture_output=True, text=True)
res = json.loads(p.stdout or '{}')
os.makedirs(work, exist_ok=True)
with open(f'{work}/rea-commands.txt', 'a') as f:
    f.write(' '.join(cmd) + f' | exit {p.returncode}\n')

nr = res.get('data', {}).get('normalized_result') if res.get('ok') else None
maps = []
for m in (nr or {}).get('matches', []):
    op = m.get('original_position') or {}
    src = m.get('reported_source') or ''
    if root and root in src:
        src = src[src.find(root):]
    maps.append({'state': m['state'], 'source': src, 'line': op.get('line'), 'column': op.get('column'), 'name': m.get('name')})
out = {'id': fid, 'label': label, 'exit_code': p.returncode, 'script_url': ent['url'], 'literal': lit,
       'generated': {'line': line0 + 1, 'column': col}, 'mappings': maps,
       'diagnostics': None if nr else (res.get('error') or p.stderr[-400:])}

os.makedirs(evid, exist_ok=True)
fp = f'{evid}/rea-trace.json'
doc = json.load(open(fp)) if os.path.exists(fp) else []
doc.append(out)
json.dump(doc, open(fp, 'w'), ensure_ascii=False, indent=1)
m = maps[0] if maps else {}
print(fid, label, 'exit', p.returncode, '->', m.get('source'), m.get('line'), m.get('column'))
