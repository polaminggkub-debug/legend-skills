# Audit profiles

Start with generic behavior, data, security, recovery, flow, tests, and
performance lenses. Add the matching profile only when detected:

- **Vue/Supabase:** composables, RLS, RPC/functions, migrations, auth/session,
  realtime and optimistic state.
- **React/Node:** effects, server/client boundaries, authorization, API schema,
  queues and background work.
- **Python/FastAPI:** dependency injection, Pydantic boundaries, async blocking,
  auth, transaction/session lifetime, background tasks.

For framework/library behavior that may differ by version, first inspect locked
versions; then consult official documentation and list the source in the report.
