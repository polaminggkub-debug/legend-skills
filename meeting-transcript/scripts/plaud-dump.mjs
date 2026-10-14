// Dump Plaud file info and transcript blocks for given file ids via the Plaud MCP server (JSON-RPC over stdio).
// Usage: node plaud-dump.mjs <outDir> [--server "<command> <args...>"] [<file id>...]
//   writes <outDir>/tools.json and, per id, <outDir>/<id>/get_file.json and transcript.<block>.p<N>.json;
//   prints only a summary. With no ids it just lists the server's tools.
// Server command: --server, else the command/args of `claude mcp get plaud`, else `npx -y @plaud-ai/mcp@latest`.
// Login is handled by the server itself; this script never reads, prints or stores tokens.
import { spawn, execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const args = process.argv.slice(2);
const flag = args.indexOf('--server');
const serverSpec = flag >= 0 ? args.splice(flag, 2)[1] : null;
const [outDir, ...ids] = args;
if (!outDir) { console.error('Usage: node plaud-dump.mjs <outDir> [--server "<command> <args...>"] [<file id>...]'); process.exit(2); }

// Only the "Command:" and "Args:" lines of `claude mcp get plaud` are used; everything else is dropped unread.
function serverFromClaude() {
  try {
    const text = execFileSync('claude', ['mcp', 'get', 'plaud'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    const command = text.match(/^\s*Command:\s*(.+)$/m)?.[1].trim();
    const argv = text.match(/^\s*Args:\s*(.*)$/m)?.[1].trim();
    return command ? [command, ...(argv ? argv.split(/\s+/) : [])] : null;
  } catch { return null; }
}
const [cmd, ...cmdArgs] = serverSpec ? serverSpec.split(/\s+/) : serverFromClaude() ?? ['npx', '-y', '@plaud-ai/mcp@latest'];

const srv = spawn(cmd, cmdArgs, { stdio: ['pipe', 'pipe', 'inherit'] });
let buf = '', nextId = 1;
const pending = new Map();
srv.stdout.on('data', (d) => {
  buf += d;
  let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i); buf = buf.slice(i + 1);
    if (!line.trim()) continue;
    const msg = JSON.parse(line);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  }
});
const rpc = (method, params) => new Promise((res) => {
  const id = nextId++; pending.set(id, res);
  srv.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
});

await rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'dump', version: '1' } });
srv.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
const tools = (await rpc('tools/list', {})).result.tools;
mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, 'tools.json'), JSON.stringify(tools, null, 2));
console.log('tools:', tools.map((t) => t.name).join(', '));

// Name of a tool's first argument (the file id), read from its input schema.
const argName = (t) => Object.keys(tools.find((x) => x.name === t)?.inputSchema?.properties ?? {})[0];

for (const id of ids) {
  const dir = join(outDir, id); mkdirSync(dir, { recursive: true });
  if (argName('get_file')) {
    const r = await rpc('tools/call', { name: 'get_file', arguments: { [argName('get_file')]: id } });
    writeFileSync(join(dir, 'get_file.json'), JSON.stringify(r, null, 2));
    console.log(id, 'get_file saved');
  }
  for (const block of ['transaction', 'transaction_polish', 'outline', 'mark_memo']) {
    let cursor, page = 0, n = 0;
    do {
      const callArgs = { file_id: id, block, limit: 500, ...(cursor ? { cursor } : {}) };
      const r = await rpc('tools/call', { name: 'get_transcript', arguments: callArgs });
      writeFileSync(join(dir, `transcript.${block}.p${page}.json`), JSON.stringify(r, null, 2));
      const text = (r.result?.content ?? []).map((c) => c.text ?? '').join('');
      const m = text.match(/"next_cursor":\s*"([^"]+)"/); cursor = m ? m[1] : undefined;
      const t = text.match(/"total":\s*(\d+)/); n = t ? +t[1] : n; page++;
    } while (cursor);
    console.log(id, block, 'pages', page, 'total', n);
  }
}
srv.kill();
