# Security and data checks

- Enforce authorization server-side at object/tenant level; UI hiding is not a
  control. Verify default-deny behavior and cross-tenant probes.
- Parameterize queries and commands. Validate type, size, format, and allowlists
  at trust boundaries. Encode output for its destination.
- Protect secrets and personal data in source, config, logs, errors, analytics,
  caches, exports, and backups. Never print a full credential while auditing.
- For server-side fetches and redirects, constrain schemes, hosts, addresses,
  redirects, and response size.
- Verify transactions preserve invariants under retries, concurrency, and
  partial failure. Check idempotency for externally repeated operations.
- Read migrations in order. Check backward compatibility, locks, defaults,
  backfill safety, rollback/forward-fix, and application/schema deployment order.
- Detect locked framework/database versions before relying on version-sensitive
  behavior; cite official documentation in Sources.
