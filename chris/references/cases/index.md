# Case index

Read these cases when the user requests examples or evidence from real projects,
or when comparing approaches whose tradeoffs a precedent can clarify. Choose
one relevant section; routine development does not require reading this library.

| Question | Read |
|---|---|
| Does configured lint actually fail the invoked command and CI? | [L1: VS Code and Ruff](lint-enforcement.md#l1--configuration-is-not-enforcement-vs-code--ruff) |
| How can generated files be checked against their source? | [L2: Kubernetes and Moby](lint-enforcement.md#l2--generated-output-is-a-source-of-truth-contract-kubernetes--moby) |
| When is custom semantic lint worth maintaining? | [L3: React and Next.js](lint-enforcement.md#l3--custom-semantic-lint-needs-a-real-domain-invariant-react--nextjs) |
| Does a test actually reproduce a fixed defect? | [A1: FastAPI](acceptance-and-review.md#a1--distinguish-regression-proof-from-additional-coverage-fastapi) |
| Why can source/manual success miss a broken delivered artifact? | [A2: Omarchy](acceptance-and-review.md#a2--test-the-shipped-artifact-through-its-real-consumer-omarchy) |
| How do we prove rejection happens before an expensive side effect? | [A3: Goose](acceptance-and-review.md#a3--put-the-guard-before-the-costly-side-effect-goose) |

Source observations were collected on **2026-09-13 (Asia/Bangkok)**. File links
pin commits; PR comments and runs describe the recorded event. Later PR status,
repository settings, and tool behavior can change. Branch-protection settings
were not established by these cases. Contributor reports are identified where
independent execution was not observed.

Use the local facts and adaptations to explain the recorded case without a new
search. For a current API/configuration question, a changed version, or a claim
these cases do not support, inspect the target repository and current primary
sources. Separate observed facts, adaptation, and remaining uncertainty. Explain
why the original constraint does or does not match the user's project. Cite the
linked primary sources when attributing behavior to a project.
