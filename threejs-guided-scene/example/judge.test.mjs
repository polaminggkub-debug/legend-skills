// Proves each rule the way the skill says: plant one bug into green facts and expect red.
// Run: node --test example/
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { judge } from './judge.mjs'

const green = () => JSON.parse(readFileSync(new URL('./fixtures/green.json', import.meta.url), 'utf8'))
const rules = (facts) => judge(facts).map((m) => `${m.step} ${m.rule}`)
const label = (row, id) => row.labels.find((l) => l.id === id)
const thing = (row, id) => row.scene.things.find((t) => t.id === id)

test('green facts pass every rule', () => {
  assert.deepEqual(rules(green()), [])
})

test('stay-put: a box that drops a shelf without being moved is red', () => {
  const f = green()
  thing(f.walk[2], 'B2').pos = [2, 0.08, 0]
  assert.deepEqual(rules(f), ['3 stay-put'])
})

test('stay-put: a box the step moves is allowed to change place', () => {
  const f = green()
  assert.ok(f.walk[1].scene.moves.includes('B1'))
  assert.deepEqual(rules(f), [])
})

test('jump-walk: a shortcut that builds one box fewer is red', () => {
  const f = green()
  f.jump[2].scene.things = f.jump[2].scene.things.filter((t) => t.id !== 'B2')
  assert.deepEqual(rules(f), ['3 jump-walk'])
})

test('jump-walk: two empty scenes are red, not equal', () => {
  const f = green()
  f.walk[0].scene.things = []
  f.jump[0].scene.things = []
  f.walk[0].scene.mustSee = []
  assert.ok(rules(f).includes('1 jump-walk'))
})

test('overlap: two labels closer than 2 px are red, and the lower class gives way', () => {
  const f = green()
  label(f.walk[0], 'store').rect = [300, 170, 370, 182]
  const m = judge(f).find((x) => x.rule === 'overlap')
  assert.match(m.detail, /"B1 · 100" \(thing\) should give way to "Store" \(zone\)/)
})

test('frame: a must-see label past the picture edge is red', () => {
  const f = green()
  label(f.walk[1], 'B1').rect = [980, 280, 1030, 295]
  assert.deepEqual(rules(f), ['2 frame'])
})

test('frame: a must-see thing cut at the picture edge is red', () => {
  const f = green()
  thing(f.walk[2], 'B1').rect = [980, 300, 1020, 340]
  assert.deepEqual(rules(f), ['3 frame'])
})

test('card-gap: a must-see label 8 px or nearer to a card is red', () => {
  const f = green()
  label(f.walk[0], 'B1').rect = [150, 64, 200, 79]
  assert.deepEqual(rules(f), ['1 card-gap'])
})

test('must-see: a label the story is not about may sit under a card', () => {
  const f = green()
  label(f.walk[0], 'B2').rect = [150, 40, 200, 55]
  assert.deepEqual(rules(f), [])
})

test('covered picture: a full-screen dialog skips the picture rules', () => {
  const f = green()
  f.walk[0].pictureCovered = true
  label(f.walk[0], 'B1').rect = [150, 40, 200, 55]
  assert.deepEqual(rules(f), [])
})

test('covered picture: stay-put still runs under a dialog', () => {
  const f = green()
  f.walk[2].pictureCovered = true
  thing(f.walk[2], 'B2').pos = [2, 0.08, 0]
  assert.deepEqual(rules(f), ['3 stay-put'])
})
