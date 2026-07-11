# Audit lenses

Choose only lenses that can reveal a distinct failure class.

## Behavior

Trace business invariants, edge conditions, state transitions, duplicate logic,
and assumptions across entry points. Compare implementation with user-visible
contracts and callers.

## Data and integration

Follow input -> validation -> storage/service -> response. Check schema drift,
nullability, transactions, idempotency, retries, ordering, concurrency, partial
failure, pagination, serialization, and migration compatibility.

## Security and access

Trace identity and authorization at every trusted boundary. Check tenant/object
scope, input/output validation, secret exposure, injection, unsafe redirects or
fetches, rate/abuse limits, and sensitive logs. Use `security-data.md`.

## Error and recovery

Inspect every fallible async/I/O path: timeout, cancellation, retry, duplicate
submission, rollback, stale state, user feedback, observability, and recovery.

## UI and flow

Walk critical tasks through loading, empty, success, error, destructive,
permission-denied, refresh, back navigation, narrow viewport, and accessibility
states. Confirm terminology and completion feedback.

## Tests and observability

Map critical behaviors to tests and production signals. Look for untested
boundaries, assertions that cannot catch the bug, missing correlation/context,
and alerts with no owner or recovery action. Route test implementation to Chris.

## Performance

Inspect algorithmic growth, repeated I/O, N+1 calls, unbounded lists, cache
correctness, payload size, blocking async work, and resource cleanup. Require a
realistic workload or measurement before a HIGH performance finding.
