# Example guard

What a guard built from the skill looks like. Three parts, so the rules stay testable without
a browser:

```
probe.js        runs in the page: label boxes, cards, scene snapshot  ->  facts
sweep.spec.ts   Playwright: walk every step, jump to every step, collect facts
judge.mjs       pure: facts  ->  red misses (the five rules)
```

## Try it without a browser

```bash
node threejs-guided-scene/example/judge.mjs threejs-guided-scene/example/fixtures/green.json
```

```bash
node threejs-guided-scene/example/judge.mjs threejs-guided-scene/example/fixtures/red.json
```

The red facts are the green ones with three planted bugs. The judge exits 1 and prints:

```text
RED  step 1  card-gap: "B1 · 100" within 8px of card "clock"
RED  step 3  stay-put: B2 moved 0.72 m inside rack-A
RED  step 3  jump-walk: walk 2 things, jump 1; only walk: B2@rack-A; only jump: -
3 red
```

## Run the tests

```bash
node --test threejs-guided-scene/example/
```

Each test plants one bug into the green facts and expects exactly its rule to go red, and
the scope tests prove what stays green: a label outside `mustSee` under a card, and a picture
under a full-screen dialog.

## Put it in your app

1. Publish `window.__scene` every frame: `{ things: [{ id, place, pos, visible, screen? }],
   moves, mustSee }`. `screen` is the thing's on-screen box, if you want bodies checked too.
2. Mark the overlay: `data-scene-stage` on the canvas container, `data-scene-label` with
   `data-id` and `data-kind` on each label and bubble, `data-scene-card` with `data-name` on
   each card over the picture. Or change the selectors in `probe.js`.
3. Set `FIRST`, `LAST`, `stepUrl` and `pressNext` in `sweep.spec.ts`.
4. Run the sweep in CI next to your end-to-end tests. Both green means done.

## Facts format

One row per step and route:

```json
{
  "step": 3,
  "route": "walk",
  "pictureCovered": false,
  "stage": [0, 0, 1000, 500],
  "cards": [{ "name": "clock", "rect": [10, 10, 200, 60] }],
  "labels": [{ "id": "B1", "kind": "thing", "text": "B1 · 100", "rect": [800, 280, 850, 295], "shown": true }],
  "scene": {
    "things": [{ "id": "B1", "place": "dock", "pos": [8, 0, 0], "visible": true }],
    "moves": [],
    "mustSee": ["B1"]
  }
}
```

Rectangles are `[left, top, right, bottom]` in CSS pixels; positions are metres.
