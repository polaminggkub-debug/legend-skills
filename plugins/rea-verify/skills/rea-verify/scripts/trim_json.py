# Trim one raw REA JSON result to evidence size: every list keeps its first N items (plus a count of the rest) and
# every string its first M characters, so megabytes become kilobytes while the shape and the leading facts stay.
# usage: trim_json.py <raw.json> [--items 40] [--chars 300]  -> JSON on stdout
import argparse, json, sys

ap = argparse.ArgumentParser()
ap.add_argument('raw'); ap.add_argument('--items', type=int, default=40); ap.add_argument('--chars', type=int, default=300)
a = ap.parse_args()

def trim(x):
    if isinstance(x, dict): return {k: trim(v) for k, v in x.items()}
    if isinstance(x, list):
        out = [trim(v) for v in x[:a.items]]
        if len(x) > a.items: out.append(f'... {len(x) - a.items} more of {len(x)}')
        return out
    if isinstance(x, str) and len(x) > a.chars: return x[:a.chars] + f'... ({len(x)} chars)'
    return x

json.dump(trim(json.load(open(a.raw))), sys.stdout, ensure_ascii=False, indent=1)
