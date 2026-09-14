import { readFileSync } from 'node:fs';
const variant = process.argv[2];
if (!['bad', 'good'].includes(variant)) throw new Error('Expected bad or good');
const source = JSON.parse(readFileSync(new URL('./source.json', import.meta.url), 'utf8'));
const expected = JSON.stringify([...source.states].sort()) + '\n';
const actual = readFileSync(new URL(`./${variant}.json`, import.meta.url), 'utf8');
if (actual !== expected) {
  console.error('Generated states are stale: regenerate from source.json');
  process.exitCode = 1;
}
