---
adr_id: ADR-051
status: Accepted
created: 2026-04-19
updated: 2026-04-19
superseded_by: null
---

# 51. Test Self-Sufficiency and Test-Owned Fixtures

## Plain Summary

Tests in this repository must be self-sufficient. Any input file, fixture, or
configuration required by a test must be hardcoded in the test itself or stored
under `tests/`.

TL;DR: tests must not depend on mutable files from `demo/`, `outputs/`, `tmp/`,
or any other uncontrolled folder.

## Context and Problem Statement

Recent failures exposed that some tests were reading files from `demo/`, which
is not a controlled test surface and may be edited by users or regenerated for
reasons unrelated to the test contract. That creates brittle failures, hidden
dependencies, and false attribution when unrelated work changes non-test
artifacts.

ADR-047 already established that tests must not rely on mutable runtime defaults
for the behavior they assert. The remaining gap is fixture ownership: even when
parameters are explicit, a test is still not reproducible if it reads inputs or
config from folders whose contents are not reserved to tests.

The project needs a stronger rule: tests must own their inputs.

## Decision Drivers

- Reproducible test execution
- Clear test ownership of fixtures and configs
- Isolation from user-editable demo and output artifacts
- Lower risk of false regressions after unrelated changes
- Research-grade verification discipline

## Considered Options

- Option A — Allow tests to read repository files from anywhere as long as the current contents make the test pass.
- Option B — Require tests to use only hardcoded inputs or fixtures/configs stored under `tests/`.
- Option C — Continue allowing `demo/` inputs but treat them as quasi-test fixtures by convention.

## Decision Outcome

Choose Option B.

Effective immediately for internal governance:

- Unit tests, integration tests, regression tests, and self-tests must be
  self-sufficient.
- Any file or configuration needed to execute or verify a test must be either:
  - hardcoded directly in the test, or
  - stored under `tests/` as a test-owned fixture or config.
- Tests must not depend on inputs from `demo/`, `outputs/`, `tmp/`, user work
  folders, or any other uncontrolled location whose contents may change outside
  the test contract.
- If a repository file outside `tests/` is part of the product contract and
  truly must be exercised, the test should copy, derive, or pin the relevant
  content into a test-owned fixture under `tests/` rather than treating the
  live external file as the source of truth.

This ADR narrows ADR-047. ADR-047 remains the active rule for explicit
parameterization and default-independent execution paths. ADR-051 extends that
discipline to fixture and config ownership by requiring test-owned inputs.

## Pros and Cons of the Options

### Chosen Option

- Pros: tests become reproducible even when demos, outputs, or scratch files change
- Pros: failures point to real contract drift rather than mutable external artifacts
- Pros: fixture ownership becomes explicit and reviewable
- Pros: tests stay stable under user edits to non-test folders
- Cons: some existing tests need migration away from convenience inputs
- Cons: test fixtures may duplicate small slices of non-test data intentionally

### Other Options

- Option A:
  - Pro: lower short-term effort when writing tests
  - Con: hidden dependencies and brittle failures
  - Con: user edits to unrelated folders can break pytest
- Option C:
  - Pro: keeps some convenient repository samples available
  - Con: still relies on convention instead of ownership
  - Con: does not solve the core mutability problem

## Implications and Consequences

- Tests that currently read files from `demo/`, `outputs/`, `tmp/`, or other
  uncontrolled locations should be migrated to test-owned fixtures.
- New CRs that require tests should name the test-owned inputs and configs they
  expect.
- Test helpers may derive temporary artifacts at runtime, but the durable source
  inputs for those helpers must still come from hardcoded strings or `tests/`
  fixtures.
- Demo artifacts remain useful for showcasing workflows, but they are not part
  of the test contract unless copied or pinned into `tests/`.

## Links

- [047-controlled-test-parameterization-and-default-independent-regression-coverage.md](047-controlled-test-parameterization-and-default-independent-regression-coverage.md)
- [../README.md](../README.md)
- [../cr/000-cr-template.md](../cr/000-cr-template.md)

## Implementation Notes (optional)

- Keep this rule visible in `docs/internal/README.md` and the CR template so it
  is applied during authoring, not only after failures.
- Prefer small test-owned fixtures over broad copied demo trees.
- When replacing a demo-backed test, preserve the asserted behavior while moving
  the source input under `tests/` or into a hardcoded test string.

## Reviewed By

- Accepted on 2026-04-19 by the repository maintainer.