import { spawnSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';

const lint = file => ['node_modules/eslint/bin/eslint.js', '--max-warnings', '0', file];
const types = variant => ['node_modules/typescript/lib/tsc.js', '-p', `fixtures/types/${variant}`];
const tests = ['--test', 'fixtures/behavior/contract.test.mjs'];
const cases = [
  { name: 'import boundary rejects database access', args: lint('fixtures/imports/bad.js'), status: 1, diagnostic: 'no-restricted-imports' },
  { name: 'import boundary accepts application service', args: lint('fixtures/imports/good.js'), status: 0 },
  { name: 'inline disable cannot hide import violation', args: lint('fixtures/imports/suppressed.js'), status: 1, diagnostic: 'no-restricted-imports' },
  { name: 'floating promise fails', args: lint('fixtures/async/bad.ts'), status: 1, diagnostic: '@typescript-eslint/no-floating-promises' },
  { name: 'void promise fails under ignoreVoid false', args: lint('fixtures/async/void.ts'), status: 1, diagnostic: '@typescript-eslint/no-floating-promises' },
  { name: 'awaited promise passes', args: lint('fixtures/async/good.ts'), status: 0 },
  { name: 'unchecked array access fails', args: types('bad'), status: 2, diagnostic: 'TS2532' },
  { name: 'checked array access passes', args: types('good'), status: 0 },
  { name: 'cross-tenant lookup fails contract', args: tests, env: { LAB_VARIANT: 'bad' }, status: 1, diagnostic: 'ERR_ASSERTION' },
  { name: 'tenant-scoped lookup passes contract', args: tests, env: { LAB_VARIANT: 'good' }, status: 0 },
  { name: 'stale generated artifact fails', args: ['fixtures/generated/check.mjs', 'bad'], status: 1, diagnostic: 'Generated states are stale' },
  { name: 'matching generated artifact passes', args: ['fixtures/generated/check.mjs', 'good'], status: 0 },
];

const results = cases.map(item => {
  const result = spawnSync(process.execPath, item.args, {
    cwd: import.meta.dirname,
    encoding: 'utf8',
    env: { ...process.env, ...item.env },
    timeout: 30000,
  });
  const output = (result.stdout ?? '') + (result.stderr ?? '');
  const passed = !result.error && result.status === item.status && (!item.diagnostic || output.includes(item.diagnostic));
  console.log(`${passed ? 'PASS' : 'FAIL'} | ${item.name} | expected=${item.status} actual=${result.status}`);
  if (!passed) console.log(output, result.error ?? '');
  return { ...item, actualStatus: result.status, passed, output };
});

writeFileSync(new URL('./verification.json', import.meta.url), JSON.stringify({
  observedAt: new Date().toISOString(),
  runtime: process.version,
  results,
}, null, 2) + '\n');
if (results.some(item => !item.passed)) process.exitCode = 1;
