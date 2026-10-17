"""Query REA `inspect-managed-members --format json` output without loading it into context.

Usage:
  python3 -I managed_evidence.py dump <members.json> <out-dir>
      Writes <name>-types.txt (type: methods) and <name>-strings.txt (every ldstr literal).
  python3 -I managed_evidence.py where <members.json> <literal> [<literal> ...]
      Lists the methods that load each exact string literal.
  python3 -I managed_evidence.py grep <members.json> <regex>
      Lists string literals matching a case-insensitive regex, with the methods that load them.
  python3 -I managed_evidence.py callers <members.json> <method-name> [<type-substring>]
      Lists the callers of a method (direct call edges only).
  python3 -I managed_evidence.py il <members.json> <type-full-name> <method-name>
      Prints the method's IL anchors with constants, strings and member names resolved,
      e.g. `1 FromSeconds Settle` for `static readonly TimeSpan Settle = TimeSpan.FromSeconds(1)`.

Caller names of compiler-generated state machines (async, lambdas) omit the outer type:
`<SendAsync>d__12.MoveNext` belongs to whichever type declares SendAsync.
"""
import json
import re
import sys


def load(path):
    data = json.load(open(path))
    return data.get('normalized_result', data)


def tok(value):
    return int(value, 16) if isinstance(value, str) else value


class Index:
    def __init__(self, r):
        self.r = r
        self.strings = {tok(s['token']): s['value'] for s in r['user_strings']['literals']}
        self.names = {}
        for m in r['member_refs']:
            self.names[tok(m['token'])] = f"{m['parent_name']}::{m['name']}"
        for m in r['methods']:
            self.names[tok(m['token'])] = f"{m['declaring_type']}::{m['name']}"
        for f in r['fields']:
            self.names[tok(f['token'])] = f"{f['declaring_type']}.{f['name']}"

    def loads(self):
        """Yield (literal, method) for every ldstr."""
        for m in self.r['methods']:
            for a in m['body'].get('anchors') or []:
                if a['opcode'] == 'ldstr':
                    yield self.strings.get(tok(a['operand'])), m

    def operand(self, a):
        if a['opcode'].startswith('ldc'):
            return a['operand']
        if a['opcode'] == 'ldstr':
            return repr(self.strings.get(tok(a['operand'])))
        return self.names.get(tok(a['operand']), a['operand'])


def label(m):
    return f"{m['declaring_type']}::{m['name']}"


def dump(r, out):
    name = r['module']['name'].removesuffix('.dll').removesuffix('.exe')
    with open(f'{out}/{name}-types.txt', 'w') as f:
        for t in r['types']:
            methods = [m['name'] for m in r['methods'] if m['declaring_type_token'] == t['token']]
            f.write(f"{t['full_name']}: {', '.join(methods)}\n")
    with open(f'{out}/{name}-strings.txt', 'w') as f:
        for s in r['user_strings']['literals']:
            f.write(repr(s['value']) + '\n')
    print(f"{name}: {len(r['types'])} types, {len(r['user_strings']['literals'])} strings, "
          f"coverage {r['coverage']['state']}")


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    cmd, r = argv[1], load(argv[2])
    ix = Index(r)
    if cmd == 'dump':
        dump(r, argv[3])
    elif cmd == 'where':
        wanted = set(argv[3:])
        for value, m in ix.loads():
            if value in wanted:
                print(f'{value!r} <- {label(m)}')
    elif cmd == 'grep':
        pattern = re.compile(argv[3], re.I)
        for value, m in ix.loads():
            if value is not None and pattern.search(value):
                print(f'{value!r} <- {label(m)}')
    elif cmd == 'callers':
        target, owner = argv[3], (argv[4] if len(argv) > 4 else '')
        for e in r['call_edges']:
            if e['target_name'] == target and owner in (e['target_declaring_type'] or ''):
                print(f"{e['caller']} -> {e['target_declaring_type']}::{target}")
    elif cmd == 'il':
        for m in r['methods']:
            if m['declaring_type'] == argv[3] and m['name'] == argv[4]:
                print(label(m), m['body'].get('il_size'), 'bytes')
                print(' '.join(ix.operand(a) for a in m['body'].get('anchors') or []))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main(sys.argv)
