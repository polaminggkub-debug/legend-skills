# Requirements traceability

Read when building or revising a requirements traceability matrix (RTM),
auditing requirement coverage, or assessing change impact across linked artifacts.
Use the project's existing records and terminology. An RTM is a view of their
relationships; choose the depth and format for the task rather than imposing a
universal schema, tool, or certification claim.

## Establish the obligation before matching the implementation

Identify the authoritative request, specification, policy, or agreed stakeholder
need and its revision. Give each distinct obligation a stable identity. Derive
the expected outcome from that source, independently of what the implementation
currently exposes. Existing code can reveal a candidate requirement; record its
inferred origin and unresolved authority until supported by an accepted source.

Keep scope and outcome separate. For a partial or deferred obligation, retain
what remains due and the authoritative scope decision. An unknown policy stays
unresolved, with its affected criteria identified. Use accepted decisions and
discoverable facts before escalating a material choice; continue independent
work while it is unresolved.

Completion here means every in-scope obligation has an identifiable source and
meaning, or an explicit authority/policy gap. A list derived only from existing
implementation mappings cannot establish that no required obligation was omitted.

## Connect meaning, delivery, and verification

Keep these distinctions in the record; separate files are optional:

| Link | Required meaning |
|---|---|
| Requirement -> criterion | Condition, observable outcome, and a plausible wrong outcome the check must reject. Derive criteria using [Acceptance and evidence](acceptance-evidence.md). |
| Criterion -> design | How the intended outcome is delivered and where it belongs. Mark inferred placement separately from source-mandated placement. |
| Design -> implementation | Actual surface, symbol, state transition, data binding, or artifact that realizes the design, at an identified revision. Include relevant boundaries and missing or unsupported links. |
| Criterion -> verification method | The observation needed and the smallest sufficient method: analysis, inspection, demonstration, test, or stakeholder review as appropriate. |
| Verification -> receipt | Criterion/scope, requirement revision, inspected code or artifact revision, environment, command or action, observed result, evidence location, and limitations. |

Use stable references where the project supports them; expose many-to-many
relationships or split compound criteria when one row hides independent outcomes.
A source path or symbol establishes a location. Review whether its actual
behavior supports the linked criterion before treating the mapping as meaningful.

Choose delivery and verification from the promise. A visible explanation may
need inspection or stakeholder review; an operation needs its observable result.
Requiring a click or automated test for every row invents obligations. Conversely,
an acknowledgement or opened document does not establish comprehension or the
document's required content. Apply the project's authorization and Chris's
[release test policy](../SKILL.md#release-test-decisions) when executing checks.

## Separate trace validity from acceptance

A structural gate can check unique identities, resolvable links, declared revision
consistency, and missing required relationships within its supported analysis.
Derive the required set from the normative source, then compare it with the
mapping. A matching count, marker, hash, or populated field proves only the
stated structural property; it does not prove requirement quality or behavior.

Report structural findings separately from the criterion's observed outcome and
stakeholder acceptance where required. Distinguish an observed failure from a
check not run, missing provenance, or an unsupported analysis; use the evidence
statuses and acceptance rules in [Acceptance and evidence](acceptance-evidence.md).
A green trace gate leaves required behavioral, visual, or owner evidence pending
until applicable receipts exist. Acceptance by an owner must cite that owner's
actual decision or observation, not an agent's inference from a passing build.

For a new or changed gate, apply [Guardrails and CI](guardrails-and-ci.md):
demonstrate rejection of a concrete missing or invalid obligation and acceptance
of the valid case through the real command path. Report expected rejection cases
separately from observed failures. Keep the unmet obligation visible while
repairing its delivery, mapping, or evidence; change its meaning or scope only
through the authoritative requirement process.

## Review changes and close the record

Trace in both directions: requirements should reach the artifacts and evidence
they need; changed artifacts should identify the obligations they affect.
Keep requirement meaning, delivery choices, and results independently reviewable.
Revise the requirement identity/version according to project policy when meaning
changes, and inspect the downstream links and receipts for stale assumptions.

Preserve historical receipts with their original provenance. Reuse unaffected
evidence only when its applicability is established; rerun or review affected
checks within the authorized scope. Do not relabel an old result as a current
observation. Close with the acceptance recommendation, exact unmet obligations,
observed failures and proposed corrections, and the checks still required.
