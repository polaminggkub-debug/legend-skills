# threejs-guided-scene-build

The authoring half of [`threejs-guided-scene`](../threejs-guided-scene/README.md). The guard
checks a step-by-step 3D scene with six measured rules; this skill tells an agent how to
write the scene so those rules hold by construction, at any data size.

| Guard rule | Algorithm in this skill |
|---|---|
| jump-walk | One pure fold, `sceneAt(n)`, used by both walk and jump |
| stay-put | Stable slots: a thing keeps its slot until it leaves the place |
| frame, card-gap | Camera fit to the safe area (picture minus HUD cards and docked dialogs) |
| overlap | Greedy label placement by priority with a collision grid |
| (scale) | Grouping ladder: thing, pile, zone, one label; overflow stack per place |

## Overflow stack

A place that holds more than it can show draws a Dock-style stack of three boxes inside its
footprint, with the id range above (`A1–A1,000,000`) and the count below (`1,000,000 BOX`).
Clicking it opens the full list. The number of bodies drawn never exceeds the place's
capacity, so the scene stays fast and inside the guard at a million things.

## Status

The algorithms come from the guard's proven rules and from MapLibre (label collision),
camera-controls (`fitToBox` with padding) and Mac Dock stacks. A scoring harness that runs a
written scene against the guard on random worlds (10 to 1,000,000 things) is being used to
evaluate the skill; results will be added here.
