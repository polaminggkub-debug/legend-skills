# Requirements traceability

**Small features and demos need only a checklist in the Issue:** one line per
criterion, each linked to its screenshot or check. Build a full requirements
traceability matrix (RTM) only for regulated or large multi-requirement work,
or when the owner asks. The RTM must stay short enough for the owner to review.

Use the project's existing records and terminology; an RTM is a view of their
relationships, not a universal schema, tool, or certification claim.

## Establish the obligation before matching the implementation

Identify the authoritative request, specification, or agreed need and its
revision; confirm it reflects the owner's current plan. Give each distinct
obligation a stable identity and derive its expected outcome from that source,
not from what the implementation exposes. Code can suggest a candidate
requirement; mark it inferred until an accepted source supports it.

Keep scope and outcome separate. A deferred obligation keeps what remains due
and who decided the deferral. An unknown policy stays visibly unresolved.
A list derived only from existing implementation mappings cannot show that no
required obligation was omitted.

## Connect meaning, delivery, and verification

| Link | Required meaning |
|---|---|
| Requirement -> criterion | Condition, observable outcome, and a plausible wrong outcome the check must reject ([Acceptance and evidence](acceptance-evidence.md)). |
| Criterion -> implementation | Actual surface, symbol, or artifact that realizes it, at an identified revision. |
| Criterion -> verification | The smallest method that observes the promise: inspection, demonstration, test, or owner review. |
| Verification -> result | What ran, on which revision, the result, and what it does not prove. |

A source path or symbol establishes a location, not behavior; check that its
behavior supports the criterion. Requiring a click or automated test for every
row invents obligations. An opened document does not establish comprehension
or required content. Apply Chris's
[release test policy](../SKILL.md#release-test-decisions) when executing checks.

## Separate trace validity from acceptance

A structural gate can check identities, resolvable links, and missing required
relationships. A matching count, marker, hash, or populated field proves only
that structural property, not requirement quality or behavior. A green trace
gate leaves behavioral, visual, and owner evidence pending. Owner acceptance
must cite the owner's actual decision, not an agent's inference from a build.

For a new or changed gate, apply [Guardrails and CI](guardrails-and-ci.md):
show it rejects a concrete missing obligation and accepts the valid case.
Change an obligation's meaning or scope only through the owner.

## Review changes and close the record

Trace both directions: requirements reach their evidence; changed artifacts
name the obligations they affect. When meaning changes, revise the requirement
and recheck downstream links. Do not relabel an old result as current. Close
with the recommendation, unmet obligations, failures, and checks still required.
