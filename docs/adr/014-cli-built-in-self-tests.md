#---
Status: Accepted
Date: 2026-03-14
---

# 14. CLI Built-In Self-Tests

## Context and Problem Statement

Each stage has critical edge cases. Users and maintainers need a quick way to validate behavior without external test harness setup.

## Decision Drivers

- Fast confidence checks per tool
- Better debugging in CLI-first workflows
- Consistent quality gates across modules

## Considered Options

- Keep tests only in external pytest suite
- Provide built-in `--test` (and variants) in CLI tools plus pytest

## Decision Outcome

Chosen option: Maintain built-in CLI self-tests and keep pytest coverage for broader regression testing.

## Pros and Cons of the Options

### Built-in tests + pytest

- Good, because quick local checks are easy
- Good, because automation still benefits from full suite
- Bad, because some tests are duplicated conceptually

### External tests only

- Good, because one test system
- Bad, because harder to run targeted checks from CLI tools

## Links

- Related: `tests/test_selftests_cli.py`
- Related: `tests/test_selftests_lib.py`
