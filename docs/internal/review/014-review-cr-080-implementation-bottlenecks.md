---
review_id: review-014
status: Draft
created: 2026-04-21
updated: 2026-04-21
reviewer: Automated repo review (assistant)
scope: >-
  docs/internal/cr/080-*, src/akkapros/cli/fullprosmaker.py, scripts/run_fullprosmaker.py,
  src/akkapros/lib/phonetize.py, src/akkapros/lib/metrics.py, tests/**
---

# Code and Project Review — CR-080 Implementation Bottlenecks

## 1. Executive Summary

CR implementation runtime has grown from ~20–30 minutes to multi-hour runs. The primary causes are test & verification practice choices (many end-to-end/full-pipeline runs embedded in tests and CR acceptance checks), combined with a monolithic full-pipeline CLI used repeatedly by tests. The repo structure itself is reasonable; the largest payoff is to change test/CI and verification practices, add explicit test markers, and add lightweight "fast" verification modes and profiling.

Top 3 actions:
- Mark heavy end-to-end tests as `integration`/`slow` and exclude them from default developer runs/fast CI.
- Add a "fast/demo" mode or small-sample fixtures for `fullprosmaker` and update tests to use them where possible.
- Add stage-level timing/profiling and a simple `--profile` run to collect hotspots (then optimize or cache as needed).

## 2. Architecture Assessment

### 2.1 Strengths
- Clear, stage-based pipeline implemented in `fullprosmaker` and separate modules ([src/akkapros/cli/fullprosmaker.py](src/akkapros/cli/fullprosmaker.py)).
- Explicit integration fixtures under `tests/integration_refs/` and well-defined acceptance criteria in CRs (good reproducibility intent).
- Unit-level tests for small, fast components (many functions in `tests/test_phonetize_lib.py`).

### 2.2 Areas for Improvement
- Acceptance and QA practice: many CRs and tests require full end-to-end runs; these are repeated across many pytest cases (see `tests/test_selftests_cli.py` and `tests/test_integration.py`).
- No default separation/markers for slow/integration tests: heavy tests are run by pytest by default unless the developer manually filters them.
- Monolithic pipeline runner is used directly by many tests; tests spawn `fullprosmaker` repeatedly instead of exercising smaller APIs or mocked stages.
- No automatic lightweight mode for `fullprosmaker` (e.g., max-lines / demo inputs) used by tests to speed verification.

## 3. Code Quality Assessment

- `fullprosmaker` ties together many heavy stages and is used by tests as an integration surface; this is fine but causes repeated full runs.
- The metrics and phonetize code are pure Python with loops and list operations (see [src/akkapros/lib/metrics.py](src/akkapros/lib/metrics.py#L984-L1005) and the `compute_*` helpers). These are maintainable but CPU-bound for large inputs; profiling will reveal true hotspots.
- Tests exercise many CLI self-test paths (see [tests/test_selftests_cli.py](tests/test_selftests_cli.py)), including the `--test-all` path which runs multiple stage selftests in sequence.

## 4. Documentation Assessment

- CRs explicitly require integration verification (e.g., CR-008, CR-015, CR-080). This is good for reproducibility but amplifies runtime cost when applied to every PR or developer verification.
- Recommend adding a small section to the CR template and `docs/internal/cr/000-cr-template.md` asking authors to designate a verification level: `quick | full` and to provide a representative *small* fixture for `quick` verification.

## 5. Research / Functional Assessment

- Functionally the implementation appears correct and tested; the observed slowness is not a correctness bug but a verification policy and test organization issue.
- No evidence in the repository of agents under `.github/agents/` (your note mentioned two agents there). I searched and found no `.github` folder in this workspace; if external agents run long jobs, they are outside this repo and should be inspected separately.

## 6. Process and Engineering Practices

- Many CRs require regenerating integration fixtures and then re-running the pipeline. This encourages repeated full runs.
- Several tests call `fullprosmaker` or `--test-all` programmatically; these are heavy and should be limited to dedicated CI jobs or nightly runs.
- No `pytest` markers for `integration`/`slow` were found; adding markers enables fast developer feedback and separated CI.

## 7. Recommendations (Priority Order)

High (fast wins):
- Add pytest markers: mark heavy tests in `tests/` as `@pytest.mark.integration` or `@pytest.mark.slow` (examples: `tests/test_integration.py`, `tests/test_selftests_cli.py` cases that run `--test-all`). Update `pytest.ini` so the default `pytest` run excludes `integration` by default.
- Update CR template: add `verification_level: quick|full` and request a small representative fixture for quick checks.
- Provide and use a small-sample demo input (e.g., `tests/integration_refs/demo_small.atf`) and update integration tests to use it for quick checks.

Medium:
- Add a `--fast` or `--max-lines N` option to `fullprosmaker` to limit processing in tests and local runs.
- Add simple per-stage timing logs in `fullprosmaker` and a `--profile` option to emit stage durations; include a small helper script to run a cProfile trace for one sample.
- Split CI: have a fast CI job (unit tests + lightweight integration) and a scheduled nightly job for full, heavy integration tests and artifact generation.

Longer-term:
- Profile the pipeline (cProfile/pyinstrument) to identify hot functions in `phonetize` and `metrics`. Consider targeted optimization (algorithmic or C-bindings) if hotspots persist.
- Consider caching intermediate stage outputs for repeated test runs of identical inputs.
- Refactor tests to prefer library calls with mocked heavy sub-stages where acceptable, reserving full pipeline runs for a small number of representative integration tests.

## 8. Summary Verdict

Root cause: verification strategy and test design (many full pipeline runs used by tests and CR acceptance) — not a single structural defect in the code. The recommended triage is to (1) distinguish slow/integration tests via markers, (2) add a "fast/demo" run mode or small fixtures, and (3) introduce light profiling and CI split. These changes will restore quick developer feedback while preserving full verification safety on demand.


---

## Files inspected (representative)

- [docs/internal/cr/080-add-mora-mode-aware-beat-alignment-and-relax-original-ophone-timing.md](docs/internal/cr/080-add-mora-mode-aware-beat-alignment-and-relax-original-ophone-timing.md)
- [src/akkapros/cli/fullprosmaker.py](src/akkapros/cli/fullprosmaker.py)
- [scripts/run_fullprosmaker.py](scripts/run_fullprosmaker.py)
- [src/akkapros/lib/metrics.py](src/akkapros/lib/metrics.py#L984-L1005)
- [tests/test_integration.py](tests/test_integration.py)
- [tests/test_selftests_cli.py](tests/test_selftests_cli.py)
- [tests/test_phonetize_lib.py](tests/test_phonetize_lib.py)


---

## Next steps I can take for you (pick one):
- I can add `pytest` markers and a `pytest.ini` change that excludes `integration` by default (quick PR).
- I can add a `--fast`/`--max-lines` flag to `fullprosmaker` and update a few tests to use the demo fixture (small PR + test updates).
- I can run a short-profile run on `fullprosmaker` with `cProfile` on your environment to locate hotspots (requires running the pipeline locally; I can provide the exact command and parse output).

Implementation is deferred in this review: this document gives the actionable next steps; I will not change production code until you request which of the recommended actions to implement.
