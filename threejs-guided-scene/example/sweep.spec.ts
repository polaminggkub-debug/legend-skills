// Guided-scene guard: the sweep. Collects the probe's facts for every step by two routes,
// then hands them to the judge. Adapt the three constants to your app.
//   walk: open step FIRST and press the guide's next control step by step (the real route)
//   jump: open each step directly by URL (the shortcut the guide's "go to step" uses)
// Run: npx playwright test sweep.spec.ts   (fails when the judge finds any red)
import { expect, test, type Page } from '@playwright/test'
import { writeFileSync } from 'node:fs'
import path from 'node:path'
import { judge } from './judge.mjs'

const FIRST = 1
const LAST = Number(process.env.GUARD_LAST_STEP ?? 12)
const stepUrl = (n: number) => `/?step=${n}`
const pressNext = (page: Page) => page.getByRole('button', { name: 'Next' }).click()

// Motion stays on: the steady rule needs the moves to play. Every other rule reads the scene after it settles.
test.use({ viewport: { width: 1440, height: 900 }, reducedMotion: 'no-preference' })
test.beforeEach(async ({ page }) => {
  await page.addInitScript({ path: path.join(import.meta.dirname, 'probe.js') })
})

async function factsAt(page: Page, step: number, route: 'walk' | 'jump') {
  const settled = await page.evaluate(() => (window as any).__guard.settle())
  expect(settled, `step ${step} (${route}) never held still`).toBe(true)
  return { step, route, ...(await page.evaluate(() => (window as any).__guard.facts())) }
}

test('guided scene: every step passes the six rules', async ({ page }) => {
  test.setTimeout(10 * 60_000)
  const walk = []
  await page.goto(stepUrl(FIRST))
  let motion: unknown[] = []
  for (let n = FIRST; n <= LAST; n++) {
    walk.push({ ...(await factsAt(page, n, 'walk')), motion })
    if (n === LAST) break
    await page.evaluate(() => (window as any).__guard.startMotion())
    await pressNext(page)
    await page.evaluate(() => (window as any).__guard.settle())
    motion = await page.evaluate(() => (window as any).__guard.stopMotion())
  }
  const jump = []
  for (let n = FIRST; n <= LAST; n++) {
    await page.goto(stepUrl(n))
    jump.push(await factsAt(page, n, 'jump'))
  }
  writeFileSync(test.info().outputPath('facts.json'), JSON.stringify({ walk, jump }, null, 1))
  const misses = judge({ walk, jump })
  expect(misses.map((m) => `step ${m.step} ${m.rule}: ${m.detail}`)).toEqual([])
})
