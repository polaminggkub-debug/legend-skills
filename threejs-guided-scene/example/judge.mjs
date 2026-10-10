// Guided-scene guard: the judge. Pure: facts in, misses out. No browser, no pixels.
// Usage: node judge.mjs facts.json   (exit code 1 when any rule is red)
// facts.json = { walk: [step facts...], jump: [step facts...] }, as written by sweep.spec.ts.
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

export const MOVE = 0.05 // m. Positions are rounded to 1 cm, so 5 cm is a real move.
export const LABEL_GAP = 2 // px. MapLibre text-padding default.
export const CARD_GAP = 8 // px. Project rule; no reference project sets one.
export const EDGE = 0 // px. Strict containment, as Plotly's assertElemInside.
const CLASS_RANK = { zone: 4, machine: 3, rack: 2, thing: 1, bubble: 5 }

const grow = (r, by) => [r[0] - by, r[1] - by, r[2] + by, r[3] + by]
const meets = (a, b) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3]
const inside = (r, s) => r[0] >= s[0] - EDGE && r[1] >= s[1] - EDGE && r[2] <= s[2] + EDGE && r[3] <= s[3] + EDGE
const mustSeeOf = (row) => new Set(row.scene.mustSee ?? [])
const isMust = (row, l) => l.kind === 'bubble' || mustSeeOf(row).has(l.id)

// overlap, frame, card-gap: what the learner can see on the picture.
export function pictureMisses(row) {
  if (row.pictureCovered) return []
  const miss = []
  const add = (rule, detail) => miss.push({ rule, step: row.step, detail })
  const shown = row.labels.filter((l) => l.shown)
  for (const l of shown.filter((l) => isMust(row, l))) {
    if (!inside(l.rect, row.stage)) add('frame', `"${l.text}" runs past the picture edge`)
    for (const c of row.cards ?? [])
      if (meets(grow(l.rect, CARD_GAP), c.rect)) add('card-gap', `"${l.text}" within ${CARD_GAP}px of card "${c.name}"`)
  }
  for (const t of row.scene.things.filter((t) => t.rect && mustSeeOf(row).has(t.id)))
    if (!inside(t.rect, row.stage)) add('frame', `thing ${t.id} is cut at the picture edge`)
  for (let i = 0; i < shown.length; i++)
    for (let j = i + 1; j < shown.length; j++) {
      const [a, b] = [shown[i], shown[j]]
      if (!isMust(row, a) && !isMust(row, b)) continue
      if (!meets(grow(a.rect, LABEL_GAP), b.rect)) continue
      const [lose, win] = (CLASS_RANK[a.kind] ?? 0) <= (CLASS_RANK[b.kind] ?? 0) ? [a, b] : [b, a]
      add('overlap', `"${lose.text}" (${lose.kind}) should give way to "${win.text}" (${win.kind})`)
    }
  return miss
}

// stay-put: walking from step N to N+1, a thing that keeps its place keeps its position.
export function stayPutMisses(walk) {
  const miss = []
  for (let k = 1; k < walk.length; k++) {
    const [before, after] = [walk[k - 1], walk[k]]
    const prev = new Map(before.scene.things.map((t) => [t.id, t]))
    const allowed = new Set(after.scene.moves ?? [])
    for (const t of after.scene.things) {
      const p = prev.get(t.id)
      if (!p || p.place !== t.place || allowed.has(t.id)) continue
      const d = Math.hypot(...t.pos.map((v, i) => v - p.pos[i]))
      if (d >= MOVE)
        miss.push({ rule: 'stay-put', step: after.step, detail: `${t.id} moved ${d.toFixed(2)} m inside ${t.place}` })
    }
  }
  return miss
}

// jump-walk: the shortcut (?step=N) must build the scene the walk built.
export function jumpWalkMisses(walk, jump) {
  const key = (row) =>
    row.scene.things
      .filter((t) => t.visible)
      .map((t) => `${t.id}@${t.place}`)
      .sort()
  const byStep = new Map(walk.map((r) => [r.step, r]))
  const miss = []
  for (const j of jump) {
    const w = byStep.get(j.step)
    if (!w) continue
    const [a, b] = [key(w), key(j)]
    if (a.length === 0 && b.length === 0) {
      miss.push({ rule: 'jump-walk', step: j.step, detail: 'both routes show an empty scene' })
      continue
    }
    const onlyWalk = a.filter((x) => !b.includes(x))
    const onlyJump = b.filter((x) => !a.includes(x))
    if (onlyWalk.length || onlyJump.length)
      miss.push({
        rule: 'jump-walk',
        step: j.step,
        detail: `walk ${a.length} things, jump ${b.length}; only walk: ${onlyWalk.join(', ') || '-'}; only jump: ${onlyJump.join(', ') || '-'}`,
      })
  }
  return miss
}

export function judge({ walk = [], jump = [] }) {
  return [...walk.flatMap(pictureMisses), ...stayPutMisses(walk), ...jumpWalkMisses(walk, jump)]
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const misses = judge(JSON.parse(readFileSync(process.argv[2], 'utf8')))
  for (const m of misses) console.log(`RED  step ${m.step}  ${m.rule}: ${m.detail}`)
  console.log(misses.length ? `${misses.length} red` : 'green: every rule passed')
  process.exitCode = misses.length ? 1 : 0
}
