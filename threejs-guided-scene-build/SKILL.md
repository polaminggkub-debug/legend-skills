---
name: threejs-guided-scene-build
description: >
  Write the code of a step-by-step 3D scene (Three.js or any WebGL canvas with HTML labels)
  so it passes the threejs-guided-scene guard on the first run and keeps passing as the data
  grows. Use before writing or changing such a scene's state, slots, camera, labels, or
  overflow display, or when a place holds more things than it can show.
---

# Build a guided scene that passes its guard

The guard ([`threejs-guided-scene`](../threejs-guided-scene/SKILL.md)) checks five rules:
stay-put, jump-walk, overlap, frame, card-gap. This skill gives one algorithm per rule. Each
algorithm makes its rule true **by construction**: it holds for any data, so the scene keeps
passing at 10 boxes or 1,000,000. Take the guard's numbers (label gap, card gap, move) from
its code by import, never by copying.

Work through the steps in order. Each ends on a check you can answer yes or no.

## 1. Model the scene as data

- **Place**: a named spot with a footprint and a `capacity` (how many things it can show),
  e.g. a shelf that shows 5 boxes.
- **Thing**: `id` and `place`. It has no position of its own.
- **Step**: data, not code: `{ set: { thingId: placeId }, mustSee: [ids], bubble? }`.

Done when: no step changes the scene except through `set`.

## 2. One fold for every route (jump-walk)

`sceneAt(n)` starts from the initial scene and applies steps 1..n in order, returning a new
value each time (never mutating). Walking to step n animates from `sceneAt(n - 1)` to
`sceneAt(n)`; jumping renders `sceneAt(n)`. The renderer only draws what `sceneAt` returns;
it never keeps its own copy of where things are.

1D example: steps "B1 → shelf A", "B2 → shelf A". Walk and jump both call `sceneAt(2)`, so
both show B1 and B2 on shelf A.

Done when: `sceneAt` is the only code that builds scene state.

## 3. Stable slots (stay-put)

Inside `sceneAt`, a thing gets a slot number when it enters a place: the lowest free slot.
It keeps that number until it leaves. Its position is a pure function of `(place, slot)`.
Never re-sort or re-pack a place's contents.

1D example, slot width 5: B1 takes slot 0 at 0–5, B2 slot 1 at 5–10. B1 leaves; B3 enters
and takes slot 0. B2 stays at 5–10 the whole time.

`moves` for step n is computed, never hand-written: the ids whose place differs between
`sceneAt(n - 1)` and `sceneAt(n)`.

Done when: a thing's position is read from its slot and nowhere else.

## 4. Overflow stack (a place holds more than it shows)

When a place holds no more than its capacity, draw each thing in its slot. When it holds
more, draw one **stack** instead: three boxes offset like a Mac Dock stack, inside the
place's footprint. The stack carries two labels:

- above: the code range, first to last in id order, e.g. `A1–A1,000,000`
- below: the count, e.g. `1,000,000 BOX`

Clicking the stack opens the full list. Both labels are must-see whenever the place is.
The number of bodies drawn is at most `capacity` per place, whatever the data holds.

Done when: no place draws more bodies than its capacity.

## 5. Labels by the grouping ladder

Build the label set at the finest level that fits, climbing only when it does not:

| Level | One label per | Text |
|---|---|---|
| 0 | thing | `A1 · 100` |
| 1 | place or pile | `A1–A10` and `10 BOX` |
| 2 | zone | `A1–A1,000,000` and `1,000,000 BOX` |
| 3 | scene | one summary label |

"Fits" means step 6 frames it and step 7 places every must-see label. Level 3 is one label,
so a level that fits always exists. Group by the step's story: a must-see thing keeps its
own label at level 0 while unrelated things group.

Done when: the scene uses the lowest level at which steps 6 and 7 both succeed.

## 6. Camera fit to the safe area (frame, card-gap)

1. Start from the picture's rectangle.
2. For each card over the picture (clock, KPI, progress), cut the side that loses the least
   area, keeping the card gap. Do the same for a docked dialog or guide that leaves part of
   the picture visible. What remains is the **safe area**.
3. Bound everything must-see: bodies plus their label boxes (labels keep a fixed size in
   pixels, so add their pixel size after projecting).
4. Choose the zoom that fits the bounds inside the safe area and centre them in it.

1D example: picture 0–100, a card at 0–20, card gap 8. Safe area 28–100, width 72. Must-see
bounds 36 wide, so zoom 2 puts them at 28–100.

If the bounds cannot fit at the smallest readable zoom, climb the ladder (step 5) and fit
again. Never hand-tune a camera per step; a step names its subjects, the fit does the rest.

Done when: every step's camera comes from this fit.

## 7. Label placement by priority (overlap)

1. Sort labels: bubble, then must-see, then zone, machine or line, rack or shelf, thing.
2. Take each label in that order. Try its candidate positions (above, right, left, below,
   then farther rings). Accept the first whose box, grown by the label gap, meets no
   accepted box and stays inside its area: the safe area for must-see labels, the picture
   for the rest.
3. A label that fits nowhere: hide it if it is not must-see; climb the ladder if it is.

1D example: label A at 1–5. Label B, 5 wide, tries 4–9 and meets A (gap 2). It tries 8–13
next and fits there.

Measure each label's real size from the DOM (or `measureText` with the real font) once per
text. Never estimate sizes from character counts. Use a grid index so placement stays near
linear in the number of labels.

Done when: every shown label was accepted by this loop.

## 8. Publish the contract

Every frame, publish `window.__scene` with `things` (id, place, position, visible, screen
box), the computed `moves`, and the step's `mustSee`, plus the overlay attributes the guard's
probe reads. Keep the layout functions (slots, ladder, fit, placement) pure, with projection
and text measurement passed in, so tests can run them in Node.

Done when: the guard's sweep reads every field it needs without touching app code.

## 9. Prove it

1. The guard's sweep is green on every step.
2. A property test runs the pure layout on random scenes from 1 to 10,000 things, plus a
   place holding 1,000,000, and the guard's judge is green on every one.
3. A planted bug per rule turns the judge red: re-pack a shelf, build jump state outside
   `sceneAt`, skip the card cut, skip the collision check.

The work is done when end-to-end tests and the guard are both green. Send the owner one
picture per changed step; the owner judges whether the picture tells the story.
