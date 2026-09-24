# Deep design audit

List screens/components and relevant states. Audit screenshots of the running
product; source alone cannot prove rendered experience.

Choose relevant lenses:

- **Hierarchy/visual system:** primary action, density, alignment, typography,
  color/contrast, spacing, iconography, responsive composition.
- **Task flow:** mental model, labels, defaults, progressive disclosure,
  interruptions, completion, recovery, back/refresh behavior.
- **Accessibility:** semantics, keyboard/focus, labels/errors, non-color cues,
  zoom/reflow, touch targets, reduced motion.
- **Consistency:** repeated patterns, token/component reuse, state behavior,
  platform conventions.

Mark each screen/state `REVIEWED`, `FINDING`, `SKIPPED — reason`, or
`COVERAGE GAP`. Verify CRITICAL/HIGH issues in the rendered UI. Give a concrete
before/after recommendation; no numeric score.
