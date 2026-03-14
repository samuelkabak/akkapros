# 1. CLI/Lib Separation

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

## Links

- Related: `src/akkapros/cli/`
- Related: `src/akkapros/lib/`
- Related ADR: [014-cli-built-in-self-tests.md](014-cli-built-in-self-tests.md)
