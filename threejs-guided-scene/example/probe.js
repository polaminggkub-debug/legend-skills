// Guided-scene guard: the in-page probe. Read-only: it measures and never changes the app.
// Inject it with Playwright's page.addInitScript({ path }) and call window.__guard.facts().
//
// It expects the app to mark up four things (rename the selectors to fit your app):
//   [data-scene-stage]                  the element the canvas fills
//   [data-scene-label]                  each HTML label/bubble over the canvas, with
//                                       data-id (thing or zone id) and data-kind
//                                       (zone | machine | rack | thing | bubble)
//   [data-scene-card]                   each card laid over the picture, with data-name
//   window.__scene                      { things: [{ id, place, pos: [x,y,z], visible }],
//                                         moves: [ids], mustSee: [ids] }, set every frame
// Thing bodies: if __scene.things[i].screen is [l,t,r,b], frame checks the body too.
// Label placement: the app puts each label at its anchor (left/top) and applies its placement
// offset as CSS `translate`, so the steady rule can tell a placement jump from riding along.
;(() => {
  const DIALOG = '[role="dialog"], dialog[open]'
  const r1 = (v) => Math.round(v * 10) / 10
  const rect = (el) => {
    const b = el.getBoundingClientRect()
    return [r1(b.left), r1(b.top), r1(b.right), r1(b.bottom)]
  }
  const shown = (el) => {
    const s = getComputedStyle(el)
    return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) > 0.05
  }
  // The picture is covered when its centre and four inner corners all hit a dialog.
  const pictureCovered = (stage) => {
    const [l, t, r, b] = rect(stage)
    const pts = [[(l + r) / 2, (t + b) / 2], [l + 4, t + 4], [r - 4, t + 4], [l + 4, b - 4], [r - 4, b - 4]]
    return pts.every(([x, y]) => document.elementFromPoint(x, y)?.closest(DIALOG))
  }
  // A label under a dialog is not shown, whatever its style says. Labels and cards over it
  // still count as shown: overlap and card-gap are there to catch exactly that.
  const onTop = (el) => {
    const [l, t, r, b] = rect(el)
    const hit = document.elementFromPoint((l + r) / 2, (t + b) / 2)
    return !hit?.closest(DIALOG)
  }

  let recording = null
  const sampleMotion = (last) => {
    if (!recording) return
    const now = JSON.stringify((window.__scene?.things ?? []).map((t) => t.pos))
    recording.push({
      moving: last !== undefined && now !== last,
      labels: [...document.querySelectorAll('[data-scene-label]')].map((el) => [el.dataset.id, el.style.translate || 'none', shown(el)]),
    })
    requestAnimationFrame(() => sampleMotion(now))
  }

  window.__guard = {
    // Samples every frame from now until stopMotion(): the steady rule's input.
    startMotion: () => {
      recording = []
      requestAnimationFrame(() => sampleMotion())
    },
    stopMotion: () => {
      const frames = recording ?? []
      recording = null
      return frames
    },
    // Resolves when the scene has held still for two frames (no animation in flight).
    settle: async () => {
      let still = 0
      let last = ''
      for (let i = 0; i < 600 && still < 2; i++) {
        await new Promise((r) => requestAnimationFrame(r))
        const now = JSON.stringify(window.__scene?.things ?? null)
        still = now === last ? still + 1 : 0
        last = now
      }
      return still >= 2
    },
    facts: () => {
      const stage = document.querySelector('[data-scene-stage]')
      const scene = window.__scene ?? { things: [], moves: [], mustSee: [] }
      return {
        pictureCovered: stage ? pictureCovered(stage) : true,
        stage: stage ? rect(stage) : [0, 0, 0, 0],
        cards: [...document.querySelectorAll('[data-scene-card]')].map((c) => ({ name: c.dataset.name, rect: rect(c) })),
        labels: [...document.querySelectorAll('[data-scene-label]')].map((el) => ({
          id: el.dataset.id,
          kind: el.dataset.kind,
          text: el.textContent.trim().slice(0, 60),
          rect: rect(el),
          shown: shown(el) && onTop(el),
        })),
        scene: {
          things: scene.things.map(({ id, place, pos, visible, screen }) => ({ id, place, pos, visible, rect: screen })),
          moves: scene.moves ?? [],
          mustSee: scene.mustSee ?? [],
        },
      }
    },
  }
})()
