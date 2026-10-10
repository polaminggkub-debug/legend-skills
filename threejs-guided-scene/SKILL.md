---
name: threejs-guided-scene
description: >
  Build and guard a step-by-step 3D scene (Three.js or any WebGL canvas) whose HTML labels,
  bubbles and camera tell a story one step at a time. Use when building or changing such a
  scene, when its labels overlap, sit under cards or get cut at the edge, when jumping to a
  step shows a different scene than walking to it, when things move that should stay put,
  or when writing the guard that checks it.
---

# Three.js guided scene

A guided scene is a 3D picture that changes one step at a time while a guide explains it.
The picture is pixels, but its labels are HTML laid over the canvas and its state is data.
So the guard **measures**: it reads label boxes from the DOM and thing positions from a scene
snapshot, then applies a few fixed rules. It never compares screenshots and never asks an
agent to look at the picture and judge it.

## The step contract

Every step publishes, for the guard and for nobody else:

- `things`: each thing's `id`, `place` (a named spot such as `rack-G02`) and `pos` (metres).
- `moves`: the ids this step is allowed to move.
- `mustSee`: the ids the step's story is about. Keep it short: the step's subject, never
  everything on screen. A step with no list checks only its bubble.

A thing missing from `mustSee` may be covered, cut or crowded. That is allowed: the story is
not about it.

## The six rules

Apply every rule to every step. Numbers carry their source; a number with no source is a
guess and must be labelled as one.

| Rule | Red when | Number and source |
|---|---|---|
| **stay-put** | Between step N and N+1 a thing keeps its `place` but its `pos` changes, and it is not in N+1's `moves` | 0.05 m: positions are rounded to 1 cm, so 5 cm is a real move |
| **jump-walk** | Opening step N directly (jump) gives a different set of visible `{id, place}` than pressing through from the start (walk); or both are empty | Exact match, plus a blank guard (Babylon.js equivalence tests) |
| **overlap** | Two shown labels, at least one must-see, are closer than the gap | 2 px (MapLibre `text-padding` default) |
| **frame** | A must-see label or thing runs past the picture's edge | 0 px, strict containment (Plotly `assertElemInside`) |
| **card-gap** | A must-see label comes nearer than the gap to a card laid over the picture (clock, KPI, progress) | 8 px: project rule; no reference project sets one |
| **steady** | While things move (any thing's position changed since the last frame), a shown label changes its placement offset or flips between shown and hidden | Exact, 0 px: labels are placed at rest and ride with their anchor during a move (owner report 2026-10-11: labels jumped and flickered mid-move) |

Two scope rules sit over all six:

- **Covered picture.** When a dialog covers the whole picture, the learner sees none of it:
  skip overlap, frame and card-gap for that step. stay-put and jump-walk still run, because
  they read data.
- **Priority.** Labels come in classes: zone > line or machine > rack or shelf > thing.
  When two labels meet, the lower class gives way (moves or hides). The guard reports the
  lower one.

## Building a scene that passes the first time

- Frame the camera from what must be seen: fit the must-see things plus a margin, then
  shrink the frame by the cards' boxes and the step's dialog. Hand-tuning a camera per step
  until it passes is the loop to avoid.
- Place labels by priority and let losers give way (MapLibre's approach: hide or move the
  loser, never stack it).
- Place labels only when the scene is at rest. During a move every label keeps its last
  offset and visibility and rides with its anchor; re-place once the move ends. Placing every
  frame makes labels jump and flicker (in one measured demo it took a third of each
  frame's work).
- One label per pile (`AX1–AX10 · 100`), not one per box.
- The jump route must build the same state as the walk: derive both from one step reducer.

## Proving a rule works

A rule is proven when it goes **red** on a real bug's "before" commit and green on its
"after" commit. When the bug cannot be shown any more, plant one (mutation): move the camera,
push a label under a card, and confirm the guard goes red. A rule that stays green on a
planted bug has a hole.

## Done

The agent's picture work is done when the end-to-end tests and the guard are both green.
The agent stops there: it sends the owner one picture per changed step and does not review
the screenshots itself for further fixes. The owner looks once and judges whether the
picture tells the story. A problem the owner finds that the guard missed becomes a new rule,
proven red by a planted bug, so the guard catches it next time.

If the same red survives two fix attempts, stop and send the owner the before and after
pictures with the guard's message.

## Example guard

A runnable example (probe, sweep, judge, fixtures and tests) lives in
[`example/`](example/). Read [`example/README.md`](example/README.md) before writing a guard
for a new project.
