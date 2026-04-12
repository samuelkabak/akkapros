# Metrics Coverage Matrix

## Purpose

This note documents the post-CR-056 confidence model for metrics verification.
The goal is not exhaustive snapshotting. The goal is that every public metrics
family has at least one exact-value verification path, and that research-
critical interval metrics are defended by more than one layer.

## Reference Strategy

The suite now uses four complementary reference sources.

1. Independent interval arithmetic on a hand-built row sequence in [tests/test_metrics_stats.py](../../tests/test_metrics_stats.py).
2. A manually audited single-line phone/ophone reference documented in [varco-verification.md](varco-verification.md).
3. A fixed representative small corpus generated from [tests/test_metrics_stats.py](../../tests/test_metrics_stats.py), with exact expected structural, prominence, speech, pause, and accentuation values pinned outside the production implementation.
4. Real checked-in corpus and pipeline fixtures:
   - the lexlinks construct corpus for broad corpus-level regression
   - the fullprosmaker regular fixture
   - the fullprosmaker mono fixture

## Coverage Matrix

| Public family | Exact-value coverage | Main layers | Reference source |
| --- | --- | --- | --- |
| Structural metrics | Yes | Unit/regression, integration, self-test | Fixed small sample, lexlinks corpus, fullprosmaker fixtures |
| Prominence metrics | Yes | Unit/regression, integration, self-test | Fixed small sample, lexlinks corpus, fullprosmaker fixtures |
| Speech and timing metrics | Yes | Unit/regression, integration, self-test | Fixed small sample, fullprosmaker fixtures |
| Pause metrics | Yes | Unit/regression, integration, self-test | Fixed small sample, fullprosmaker fixtures, lexlinks corpus |
| Drift metrics | Yes | Unit/regression, integration | Manual single-line phone/ophone fixture, lexlinks corpus, fullprosmaker fixture |
| Acoustic interval metrics | Yes | Unit/regression, integration, self-test | Hand-built rows, manual single-line verification, lexlinks corpus, fullprosmaker fixtures |

## Test Classification After CR-056

### Exact-value tests

- [tests/test_metrics_stats.py](../../tests/test_metrics_stats.py)
  - fixed small-corpus structural, prominence, speech, pause, and accentuation regressions
  - manual interval-row verification
  - manual single-line phone/ophone interval verification
  - lexlinks corpus regression covering structural, prominence, speech, pause, drift, accentuation, and acoustic families
- [tests/test_integration.py](../../tests/test_integration.py)
  - broadened fullprosmaker regular metrics JSON assertions
  - broadened fullprosmaker mono metrics JSON assertions
  - representative rendered metrics-table line assertions for both modes
- [tests/test_selftests_lib.py](../../tests/test_selftests_lib.py)
  - expanded metrics built-in self-tests for exact fixed-sample values

### Consistency-only tests retained intentionally

- Internal arithmetic/coherence checks that prove invariants such as syllable and mora totals, pause-ratio derivations, and accentuation-rate formulas.
- These are still useful, but after CR-056 they no longer stand alone for any major public family.

### Presence-only checks retained intentionally

- Selected output-layout and path-safety checks remain presence-oriented because they defend formatting and privacy constraints rather than numeric correctness.
- These checks supplement, rather than replace, the exact-value regressions above.

## Highest-Risk Manual References

The highest-risk metrics families are the public interval metrics and the
corpus-level surfaced summaries. Their main manual or independently derived
references are:

- [varco-verification.md](varco-verification.md) for the active interval metrics on a single phone/ophone line.
- [word-count-verification.md](word-count-verification.md) for corpus-level word and prominence counts on the lexlinks construct fixture.
- [tests/test_metrics_stats.py](../../tests/test_metrics_stats.py) fixed-value constants for the representative small sample and lexlinks corpus matrix.

## Residual Limits

This coverage model deliberately avoids whole-file opaque golden snapshots for
metrics text and JSON. Exact selected fields are preferred because they are
more auditable when the contract changes. If a future CR changes the approved
metrics contract, update the fixed-value references and this matrix together.
