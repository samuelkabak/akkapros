---
adr_id: ADR-047
status: Accepted
created: 2026-04-18
updated: 2026-04-18
superseded_by: null
---

# 47. Controlled Test Parameterization and Default-Independent Regression Coverage

## Plain Summary

Behavioral tests in this repository must stop depending implicitly on mutable
built-in defaults. Unit tests, integration tests, and regression tests must set
the parameters they need explicitly so the exercised path is fully controlled
and does not change merely because package defaults were retuned.

TL;DR: test the intended contract, not whatever the current defaults happen to
be.

## Context and Problem Statement

The repository now has a package-wide YAML configuration model, many runtime
options with evolving default values, and end-to-end tests that cover CLI and
pipeline behavior. In practice, some regression-oriented tests have been using
live default configuration indirectly through helpers such as runtime default
builders or default CLI behavior.

That creates two problems:

- a test that is meant to pin a stable behavioral contract can start failing
  when an unrelated default is intentionally changed
- the actual execution path becomes ambiguous because the test is partly driven
  by mutable repository defaults rather than by test-local declared inputs

ADR-025 established reproducible integration coverage, but it still described
verification in terms of default CLI behavior. ADR-036 established shared YAML
config and precedence, which made default-driven ambiguity more visible because
many runtime behaviors can now be reached either from built-in defaults, config
files, or explicit overrides.

The project needs a sharper rule for test construction: regression and
behavioral verification must travel a fully controlled parameter path.

## Decision Drivers

- Deterministic regression coverage
- Fully controlled execution paths in tests
- Isolation between intentional default retunes and unrelated behavioral tests
- Research-grade reproducibility
- Clear separation between testing default contracts and testing other behavior

## Considered Options

- Option A — Keep relying on live defaults in tests and refresh failing golds whenever defaults change.
- Option B — Require explicit parameterization for behavioral tests and reserve default-dependent assertions for dedicated default-contract tests.
- Option C — Freeze package defaults permanently to protect existing tests.

## Decision Outcome

Choose Option B.

Effective immediately for internal governance:

- Unit tests, integration tests, and regression tests that verify behavior,
  outputs, metrics, reconstruction, or other semantic results must set the
  parameters relevant to that verification explicitly.
- Such tests must not rely on mutable built-in defaults for the behavior they
  are asserting.
- Tests should use explicit fixtures, test-local config files, direct function
  arguments, or explicit CLI overrides so the exercised path is fully defined by
  the test itself.
- Dedicated tests whose explicit purpose is to verify default resolution,
  default emission, or default-schema contents are allowed to assert defaults,
  but they must say so clearly in their test purpose and should be narrow in
  scope.

For integration and regression coverage, this means the preferred contract is a
committed pinned config or equivalent explicit parameter surface, not an
unqualified default CLI run.

This ADR narrows ADR-025 by replacing its older “default CLI behavior” wording
for reproducibility with a stronger controlled-input rule. ADR-025 remains the
historical record for maintaining integration coverage, but ADR-047 becomes the
active rule for how that coverage must be parameterized. This ADR also extends
ADR-036 by specifying how the shared config model must be used in tests to
avoid default-driven ambiguity.

## Pros and Cons of the Options

### Chosen Option

- Pros: regression tests remain stable when unrelated defaults are intentionally changed
- Pros: each test states the exact path and parameter surface it covers
- Pros: gold outputs and metric baselines are tied to declared inputs rather than repository drift
- Pros: failures become easier to interpret because the source of behavior is explicit
- Cons: tests may need more fixtures or pinned config files
- Cons: updating tests can require touching test-local configs as well as expected outputs

### Other Options

- Option A:
  - Pro: less up-front test setup
  - Con: brittle regression coverage tied to mutable defaults
  - Con: ambiguous execution paths and low-signal failures after approved retunes
- Option C:
  - Pro: protects existing tests without rewriting them
  - Con: blocks legitimate default evolution
  - Con: makes tests control product defaults instead of the reverse

## Implications and Consequences

- Behavioral tests should prefer explicit config fixtures over live calls to
  default builders when the purpose is not to test defaults themselves.
- Gold-standard integration tests should be driven by pinned config snapshots or
  equivalent explicit parameter declarations.
- A test that intends to cover a particular solver branch, metrics path, pause
  path, or formatting path must specify the parameters that force that path,
  rather than depending on whatever defaults happen to select it.
- When defaults are intentionally retuned, dedicated default-contract tests may
  need updates, but unrelated regression tests should not fail for that reason
  alone.
- CRs and REQs that call for unit or integration coverage should treat
  “controlled path” as the default expectation for test design.

## Links

- [025-integration-test-coverage.md](025-integration-test-coverage.md)
- [026-conservative-change-discipline-for-research-grade-computation.md](026-conservative-change-discipline-for-research-grade-computation.md)
- [036-package-wide-yaml-configuration-and-cli-override-precedence.md](036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- [../req/022-package-wide-yaml-config-and-confwriter.md](../req/022-package-wide-yaml-config-and-confwriter.md)

## Implementation Notes (optional)

- Update internal process guidance in `docs/internal/README.md` so the rule is
  visible outside this ADR.
- Prefer committed pinned test configs for regression fixtures when a workflow
  spans multiple stages or many config keys.
- If a test intentionally covers default behavior, name that purpose plainly and
  keep the assertion surface limited to defaults.

## Reviewed By

- Accepted on 2026-04-18 by the repository maintainer.
