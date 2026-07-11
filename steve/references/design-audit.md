# Deep design audit

Manifest routes/screens/components and relevant states. Use screenshots or a
running product when available; source alone cannot prove rendered experience.

Choose relevant lenses:

- **Hierarchy/visual system:** primary action, density, alignment, typography,
  color/contrast, spacing, iconography, responsive composition.
- **Task flow:** mental model, labels, defaults, progressive disclosure,
  interruptions, completion, recovery, back/refresh behavior.
- **Accessibility:** semantics, keyboard/focus, labels/errors, non-color cues,
  zoom/reflow, touch targets, reduced motion.
- **Consistency:** repeated patterns, token/component reuse, state behavior,
  platform conventions.

For each screen/state mark `REVIEWED`, `FINDING`, `SKIPPED — reason`, or
`COVERAGE GAP`. Verify CRITICAL/HIGH issues in the rendered UI or exact component
state. Show a concrete before/after recommendation; do not invent a numeric score.
