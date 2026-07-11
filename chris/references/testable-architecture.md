# Testable architecture

Map code before tests: pure logic, I/O boundary, utility, orchestrator. Give
each a one-line `Given -> produces -> rule` spec. Extract mixed concerns until
business rules can run without network, filesystem, clock, UI, or global state.

Test order: unit specs first; integration tests for real adapters and data
contracts; one targeted E2E or contract sample for a critical user journey.
Skip thin wiring when its units and boundary are already covered.
