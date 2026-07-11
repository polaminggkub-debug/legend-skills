---
name: ui-ux-pro-max
description: >
  Use when Steve needs implementation-specific style, color, typography,
  interaction, accessibility, responsive, or framework guidance for UI work.
---

# UIUX Pro Max

Use after Steve establishes the user, primary task, hierarchy, and product
intent. Provide implementation guidance, not a competing product decision.

## Load one relevant reference

| Need | Reference |
|---|---|
| visual direction | `references/style.md` |
| palette/contrast | `references/color.md` |
| font/type scale | `references/typography.md` |
| controls/states/motion | `references/interaction.md` |
| accessible/responsive UI | `references/accessibility.md` |
| framework patterns | `references/stacks.md` |

For concrete catalog results, run this skill's `scripts/search.py` with the
available Python 3 launcher:

`<python> <skill-directory>/scripts/search.py "<query>" --domain <domain>`

Use `--stack <stack>` for framework guidance and `--json` for structured output.
Supported domains: `style`, `color`, `chart`, `landing`, `product`, `ux`, and
`typography`. If Python is unavailable, use the relevant reference directly.

Choose a small coherent system. State the selected tokens/patterns and why they
support Steve's decision. Do not load the entire catalog, copy trendy visuals,
or override product clarity for decoration.

Use platform-native implementation and project dependencies. If a requested
resource is absent, state it; never fabricate an installed version.
