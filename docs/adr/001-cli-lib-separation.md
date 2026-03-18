---
Status: Accepted
Date: 2026-03-10
---

# 1. CLI/Lib Separation

## Plain Summary

We keep reusable code in `lib/` and keep command-line tools in `cli/`.
This makes the core logic easy to import, test, and reuse.

## Context and Problem Statement

The project needs reusable logic for scripts, tests, and potential library use. Early script-heavy layouts made code harder to reuse and test.

## Decision Drivers

- Reusability of core logic
- Testability and maintainability
- Clear separation of runtime logic and argument parsing

## Considered Options

- Keep behavior mainly in CLI files
- Separate command adapters (`cli/`) from implementation modules (`lib/`)

## Decision Outcome

Chosen option: Separate `cli/` from `lib/`, because it keeps business logic importable and lets CLIs remain thin wrappers.

## Pros and Cons of the Options

### Separate `cli/` and `lib/`

- Good, because logic is reusable across CLIs and tests
- Good, because interface changes are isolated to CLI layer
- Bad, because there is a small amount of wrapper boilerplate

### Keep behavior in CLI files

- Good, because fewer files initially
- Bad, because hard to reuse and unit-test internals
- Bad, because argument handling and logic become tightly coupled

## Implications and Consequences

- Keep implementation, tests, and docs aligned with this decision when related changes are introduced.
- Treat changes that alter this decision's user-facing behavior as release-note-worthy updates.

## Links

- Related: `src/akkapros/cli/`
- Related: `src/akkapros/lib/`
- Related ADR: [014-cli-built-in-self-tests.md](014-cli-built-in-self-tests.md)

## Reviewed By

- Akkapros maintainers
