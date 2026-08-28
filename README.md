# Legend Skills

Portable agent skills plus an optional GPT-5.6 routing profile for Codex.

| Component | Codex | Claude Code | Requirement |
|---|---:|---:|---|
| General skills | Yes | Yes | None |
| Matt guided workflow router | Yes | Yes | Stable `mattpocock/skills` suite |
| Steve Design Suite | Yes | Yes | None |
| GPT-5.6 Router | Yes | No | `gpt-5.6-luna`, `gpt-5.6-terra`, or `gpt-5.6-sol` |

## Install

Give this repository to your coding agent and say:

```text
Read gpt56-router/INSTALL_FOR_AI.md and install the components I request.
Follow every compatibility, backup, ownership, and uninstall rule.
```

Installing files from this repository requires no installer runtime. The same
instruction works on Windows, macOS, and Linux. If `matt` prerequisites are
missing, their separate upstream installation requires Node.js and `npx`.

General skills: `chris`, `formpress`, `margaret`, `matt`, `ship`, `steve`,
`ui-ux-pro-max`, and `update-all`.

`matt` uses current evidence to identify the next safe workflow action and its
approval boundary. Guided mode asks before starting an AFK-ready action;
Autopilot must be explicitly enabled for the current request and still stops at
scope, architecture, merge, deploy, Production, and destructive boundaries. On
first use Matt checks for the reviewed stable skills from
[`mattpocock/skills`](https://github.com/mattpocock/skills), asks before any
external installation, and captures tracker/spec defaults.

For a complete `matt` installation, tell the installing agent to read and
follow `matt/INSTALL_FOR_AI.md`. Copying or downloading the directory alone is
only a partial installation. The installer verifies the pinned GitHub manifest,
downloads every missing upstream dependency after one approval, and completes
configuration immediately or on the first `$matt` invocation.

## GPT-5.6 Router

Install only for Codex running GPT-5.6. If the active model is incompatible,
the agent must skip installation. If the router is already present, the agent
must recommend safe removal.

Recommended routing:

| Work | Model |
|---|---|
| Main planning, routing, synthesis | Sol medium |
| Known target, at most two files/directories | Luna high |
| Broad repository discovery and large context | Terra high |
| Implementation, debugging, tests | Terra high |
| Security, production, migration, destructive work | Sol high |
| Verified commit and push | Luna low |

Sol xhigh, max, and ultra remain manual-only. Ultra is reserved for work that
splits into at least three independent parallel tracks.

See `gpt56-router/SUBAGENT_ROUTING.md` for policy and
`gpt56-router/BENCHMARKS.md` for the reasoning behind these defaults.

## Repository rename

This project was previously named `claude-skills`. GitHub redirects old links
after the repository is renamed to `legend-skills`.
