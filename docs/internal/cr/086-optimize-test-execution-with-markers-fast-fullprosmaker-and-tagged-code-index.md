---
cr_id: CR-086
status: Done
priority: High
impact: Mutative
created: 2026-04-21
updated: 2026-04-22
implements: ''
---

# Change Request: Optimize Test Execution with Markers, Fast fullprosmaker Modes, and Tagged Code Index

# Summary

Introduce a runtime-optimized verification workflow so most development checks
finish quickly while preserving a full safety gate before CR completion.

This CR includes four coordinated changes:

- (A) Add pytest markers and update `pytest.ini` so default runs focus on fast,
  impacted checks.
- (B) Add `--fast` and `--max-lines` to `fullprosmaker` and update tests to
  use bounded inputs where full corpus coverage is not required.
- (C) Add test dependency tagging/mapping so targeted test runs can be selected
  from impact tags (for example `config_impact`, `critical_path`).
- (D) Add tagged code indexing/chunk metadata so code inspection can load
  relevant sections first; provide progressive-disclosure guidance for
  inspection and review (start with small code slices, expand only as needed).

Before this CR is tagged Done, one final full validation run (`pytest` without
fast filters, plus stage self-tests) must pass.

---

# Profiling Baseline (2026-04-21)

Observed profile run command:

`python -m cProfile -o tmp/cr086_fullprosmaker.prof -m akkapros.cli.fullprosmaker outputs/erra_proc.txt -p cr086profile --outdir tmp/cr086_profile_run --metrics-json --print-acute`

Observed runtime:

- 4,700,529 function calls (4,394,649 primitive calls) in 2.833s.

Top cumulative hotspots from `tmp/cr086_fullprosmaker_profile_utf8.txt`:

- `src/akkapros/cli/fullprosmaker.py:215(run_pipeline)`
- `src/akkapros/lib/print.py:981(process_file)`
- `src/akkapros/lib/phonetize.py:1012(realize_phone_streams)`
- `src/akkapros/lib/metrics.py:1477(process_file)`
- `src/akkapros/lib/print.py:938(_render_phone_rows)`
- `src/akkapros/lib/phonetize.py:2024(realize_phone_rows)`

Interpretation: the expensive surfaces are mostly downstream rendering,
phonetizer realization, and metrics processing. Reducing unnecessary full-file
pipeline test executions should produce the largest near-term win.

---

# Motivation

CR implementation and verification throughput has degraded because default test
habits repeatedly execute heavy integration paths. The project needs a strict,
predictable split between:

- fast/default developer verification,
- targeted impact-based verification,
- final full verification gate.

This CR formalizes that split in code, tests, and governance.

---

# Scope

## Included

- Define and register explicit pytest markers for runtime class and impact
  domain.
- Change default `pytest.ini` behavior to exclude heavy classes from default
  runs while keeping opt-in commands straightforward.
- Add `fullprosmaker --fast` and `--max-lines` with deterministic behavior and
  clear precedence rules.
- Update tests to use marker-based and bounded-input execution where valid.
- Add an explicit test dependency map (or equivalent impact-tag contract) that
  links code domains to test selectors.
- Add a code indexing/tagging artifact to support bounded inspection by module
  domain and independent sections.
- Define mandatory final full-run gate before CR status can move to Done.

## Not Included

- Algorithmic optimization of phonetizer/metrics internals in this CR.
- Removing existing integration tests.
- Replacing full validation gates with only selective runs.

---

# Proposed Change

## A) Pytest markers and `pytest.ini`

Add and adopt marker families:

- Runtime class markers: `unit`, `integration`, `slow`.
- Impact-domain markers: `config_impact`, `critical_path`, `docs_only`,
  `metrics_impact`, `phonetize_impact`, `prosody_impact`.

Default `pytest` behavior should exclude `integration` and `slow` unless
explicitly requested.

Example selectors:

- fast default: `pytest`
- targeted config impact: `pytest -m "config_impact and not slow"`
- full integration: `pytest -m "integration or slow"`
- release/final gate: `pytest` with override that includes all markers

## B) `fullprosmaker --fast` and `--max-lines`

Add bounded execution controls:

- `--max-lines N`: process at most N non-frontmatter input lines from proc
  input before downstream stages.
- `--fast`: convenience profile that enables bounded behavior (for example,
  preset line cap and minimal output surfaces) while preserving deterministic
  artifact contract.

Contract requirements:

- line slicing must preserve frontmatter consistency and line order.
- output frontmatter must record whether fast mode or line caps were applied.
- `--max-lines` and `--fast` behavior must be test-covered.

## C) Test dependency map or tagging

Adopt at least one authoritative impact routing artifact:

- option 1: `tests/dependency_map.yaml` mapping code paths/domains to markers
  or test modules.
- option 2: strict marker-only routing with maintained tag taxonomy document.

The contract must permit answering: "Given touched domain X, which tests are
mandatory in fast mode and which are optional until final gate?"

## D) Tagged code indexing for bounded inspection

Introduce a machine-readable code index with per-file tags and optional section
boundaries (for example top-level function/class ranges or logical blocks).

Suggested artifact:

- `docs/internal/code-index/module-tags.yaml`

Minimum fields per entry:

- module path
- domain tags (for example `phonetize`, `metrics`, `config`, `cli`)
- coupling level (`independent`, `shared-core`, `pipeline-critical`)
- primary test markers/dependency tags

Usage rule:

- bounded, tag-filtered inspection is first-pass default;
- full repository inspection is explicit fallback when tag resolution is
  insufficient.

---

# Files Likely Affected

pytest.ini
src/akkapros/cli/fullprosmaker.py
src/akkapros/lib/frontmatter.py
tests/test_integration.py
tests/test_selftests_cli.py
tests/test_config_support.py
tests/test_metrics_stats.py
tests/test_phonetize_lib.py
tests/dependency_map.yaml
docs/internal/code-index/module-tags.yaml
docs/internal/cr/000-cr-template.md
docs/internal/README.md

---

# Acceptance Criteria

- [x] `pytest.ini` registers marker taxonomy and default run excludes heavy
      classes (`integration`, `slow`) unless explicitly requested.
- [x] Existing heavy tests are marked consistently; marker misuse does not
      silently skip critical path tests.
- [x] `fullprosmaker` exposes `--fast` and `--max-lines` with documented,
      deterministic behavior.
- [x] Tests cover `--fast` and `--max-lines` behavior, including frontmatter
      reporting for bounded runs.
- [x] A maintained test dependency map or equivalent marker-routing document is
      present and referenced by verification instructions.
- [x] A maintained tagged code index artifact exists and supports bounded code
      inspection by domain tags.
- [x] CR verification instructions define three tiers: fast default,
      impact-targeted, and final full gate.
- [x] Before status changes to Done, one final full run passes:
  `pytest` (all tests) and stage self-tests (`--test-all` where relevant).
  Verified: 352 tests passed (2026-04-22).

---

# Risks / Edge Cases

- Over-filtered default marker expressions could hide regressions.
- `--max-lines` slicing could invalidate assumptions if line-level context is
  required by downstream logic.
- Code-index tags may drift unless ownership/update responsibility is explicit.
- Mapping-based test selection can become stale if not verified in CI.

---

# Testing Strategy

Unit tests:

- marker registration and selection sanity checks.
- `fullprosmaker --max-lines` deterministic truncation behavior.
- `fullprosmaker --fast` option resolution and frontmatter metadata.

Integration tests:

- targeted marker runs for impacted domains.
- at least one representative fullprosmaker bounded run compared against
  expected artifact shape.

Governance checks:

- dependency map/tag index validation (format and referenced paths).
- explicit final gate execution before CR completion.

---

# Rollback Plan

- Revert marker-based default filtering in `pytest.ini`.
- Remove `--fast`/`--max-lines` CLI additions and related metadata.
- Remove dependency map and code-index artifacts.
- Restore previous verification procedure.

---

# Related Issues

- [CR-080](080-add-mora-mode-aware-beat-alignment-and-relax-original-ophone-timing.md)
- [Review-014](../review/014-review-cr-080-implementation-bottlenecks.md)

---

# Tasks

## Implementation

- [x] Add marker taxonomy and update default pytest behavior.
- [x] Add `fullprosmaker --fast` and `--max-lines`.
- [x] Add dependency routing artifact (map or enforced marker taxonomy).
- [x] Add tagged code-index artifact for bounded inspection.

## Tests

- [x] Add/adjust tests for marker policies and bounded fullprosmaker runs.
- [x] Verify targeted selectors for config-impact and critical-path slices.

## Documentation

- [x] Document optimized test run modes and final full-run policy.
- [x] Document code-index tag semantics and update process.

## Review

- [x] Run fast default verification.
- [x] Run impact-targeted verification for changed domains.
- [x] Run final full gate (`pytest` all + stage `--test-all`) before setting
  status to Done.

---

# Implementation Blockers
