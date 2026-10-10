# Agent guard overhead research, 2026-10

Collected 2026-10-11 (Asia/Bangkok) after the owner reported that more guards
around coding agents made runs slower and loop (run → fail → run), while no
guards let the agent skip steps. "Carried by" names the skill file that holds
the rule: `guard` = references/guardrails-and-ci.md, `SKILL` = SKILL.md,
`speed` = references/test-speed.md.

No study found measures guard count against agent speed directly. The rules
combine the findings below; treat that link as inference.

## Findings

| # | Finding | Kind | Source | Carried by |
|---|---|---|---|---|
| 1 | Instruction compliance falls as simultaneous instructions grow (10–500); the best model met about 68% at 500, with bias toward earlier ones | Paper (NeurIPS 2025 listing) | [IFScale, arXiv 2507.11538](https://arxiv.org/abs/2507.11538) | guard: keep the set small |
| 2 | Strict all-instructions success drops with each added instruction, including code tasks | Paper (Findings of EMNLP 2025) | [ManyIFEval / StyleMBPP, arXiv 2509.21051](https://arxiv.org/abs/2509.21051) | guard: keep the set small |
| 3 | Context files did not significantly raise success; LLM-written ones lowered it and raised cost by over 20%; agents follow the added requirements | Paper (ICLR 2026 listing) | [Evaluating AGENTS.md, arXiv 2602.11988](https://arxiv.org/abs/2602.11988) | guard: prose rules advisory |
| 4 | Reliability falls as input length grows, even on simple tasks | Industry report, 2025-07 | [Chroma, Context Rot](https://research.trychroma.com/context-rot) | guard: quiet pass, short fail |
| 5 | Print a mark on success and the log only on failure so passing output does not fill context | Blog, 2025-12 | [HumanLayer, context-efficient backpressure](https://www.humanlayer.dev/blog/context-efficient-backpressure) | guard: quiet pass, short fail |
| 6 | Self-repair gains are modest and bounded by feedback quality | Paper (ICLR 2024) | [Is Self-Repair a Silver Bullet?](https://proceedings.iclr.cc/paper_files/paper/2024/hash/9ddc141bdbf9d1db510cefff56c586ad-Abstract-Conference.html) | guard: `file:line rule → fix` |
| 7 | Long repetitive action sequences correlate with failure; scaffold fixes for repetition did not raise resolve rates | Preprint | [SWE-smith, arXiv 2504.21798](https://arxiv.org/abs/2504.21798) | guard: bounded; SKILL step 4 |
| 8 | Frontier models modified tests or scoring code, or read stored answers, while showing they knew it was unwanted | Lab report, 2025-06-05 | [METR, recent reward hacking](https://metr.org/blog/2025-06-05-recent-reward-hacking) | guard: locked; SKILL rule 5 |
| 9 | CLAUDE.md is advisory and hooks are deterministic; delete an instruction the agent already follows or turn it into a hook; after two failed corrections, reset rather than retry | Vendor docs | [Claude Code best practices](https://code.claude.com/docs/en/best-practices) | guard: prose rules; bounded |
| 10 | Hook exit 2 returns stderr to the agent; Claude Code overrides a Stop hook after repeated blocks; scripts check `stop_hook_active` | Vendor docs | [Claude Code hooks guide](https://code.claude.com/docs/en/hooks-guide) | guard: bounded |
| 11 | Linter messages can carry fix instructions; run fast computational checks per change and slow or LLM-judge checks later; when an issue recurs, improve the guide or sensor | Article, 2026-04-02 | [Böckeler, Harness engineering](https://www.martinfowler.com/articles/harness-engineering.html) | guard: tight; keep the set small |
| 12 | Leave linter work to linters, not LLM judgement; keep the rule file short | Blog, 2025-11-25 | [HumanLayer, writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md) | guard: deterministic and fast |

## Unverified or excluded

- Flaky-test cost figures attributed to Google and Microsoft circulate through
  secondary blogs only; excluded.
- HumanLayer's "150–200 instructions" budget is the author's estimate.
- The Claude 3.7 Sonnet system card's test-special-casing note was read through
  secondary reports only; finding 8 carries the claim instead.
