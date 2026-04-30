---
review_id: REVIEW-016
status: Done
created: 2026-04-29
reviewed_crs: CR-081, CR-082, CR-083, CR-084, CR-085, CR-086, CR-087, CR-088, CR-089, CR-090, CR-091, CR-092
reviewer: '@change'
---

# Polish Review: CR-081 through CR-092

## Summary

A systematic polish review of CR-081 through CR-092, checking consistency
between code, documentation, config files, and tests. All 12 CRs are marked
`Done`. Most are fully implemented and verified. Two issues found: one
governance inconsistency (CR-091) and one minor config drift observation.

---

## Files Inspected

| File | Role |
|------|------|
| `src/akkapros/config/default.yaml` | Package default config |
| `src/akkapros/lib/phonetize.py` | Primary phonetizer implementation |
| `src/akkapros/lib/_phonetize_config.py` | Schema, validation, config rendering |
| `src/akkapros/lib/prosody.py` | Prosody facade |
| `src/akkapros/lib/_prosody_text.py` | Prosody text helpers + types |
| `src/akkapros/lib/prosody_model.py` | Prosody model classes |
| `src/akkapros/lib/prosody_engine.py` | Prosody engine |
| `src/akkapros/lib/syllabify.py` | Syllabify facade |
| `src/akkapros/lib/_syllabify_escape.py` | Syllabify escape helpers |
| `src/akkapros/lib/phoneprep.py` | Phoneprep facade |
| `src/akkapros/lib/_phoneprep_phonology.py` | Phoneprep phonology rules |
| `src/akkapros/lib/_phoneprep_io.py` | Phoneprep I/O |
| `src/akkapros/lib/print.py` | Print facade |
| `src/akkapros/lib/_print_ipa.py` | IPA rendering |
| `src/akkapros/lib/_print_pho.py` | .pho rendering |
| `src/akkapros/lib/config.py` | Config facade |
| `src/akkapros/lib/_config_io.py` | Config I/O |
| `src/akkapros/lib/tests/` | Library self-tests |
| `tests/dependency_map.yaml` | Test dependency routing |
| `docs/internal/code-index/module-tags.yaml` | Code index tags |
| `pytest.ini` | Pytest configuration |
| `demo/akkapros/prosmaker/corpus-demo.yaml` | Demo config |
| `demo/akkapros/lexlinks/construct-demo.yaml` | Demo config |
| `tests/integration_refs/regression_defaults.yaml` | Integration test reference |
| `docs/internal/cr/081-*.md` through `092-*.md` | CR documents |

---

## Findings

### CR-081: Remove Phonetize Speech Config

**Status:** ✅ Clean

- `speech` subtree absent from `default.yaml` ✅
- `speech` absent from schema (`PHONETIZE_SCHEMA`) ✅
- `speech` absent from demo YAML files ✅
- `speech` absent from `regression_defaults.yaml` ✅
- All 9 AC checkboxes checked ✅

### CR-082: Add Corrective Geminate Coda Share Ratio

**Status:** ✅ Clean

- `geminate_coda_ratio: 0.6` present in `closure`, `fricative`, `sonorant` ✅
- All 6 AC checkboxes checked ✅

### CR-083: Rename Mini Pause to Resync Pause

**Status:** ✅ Clean

- `enable_resync_pause: false` present ✅
- `pauses.resync` replaces `pauses.mini` ✅
- `pauses.mini` absent from default config ✅
- All 7 AC checkboxes checked ✅

### CR-084: Add Pre-Pausal Final Duration Anchors

**Status:** ✅ Clean

- `coda_final` present in all 3 consonant classes ✅
- `short_final: 110` and `long_final: 160` present ✅
- All 7 AC checkboxes checked ✅

### CR-085: Add Global Duration Scale

**Status:** ✅ Clean

- `durations.scale: 1.0` present as first key in `durations` block ✅
- All 8 AC checkboxes checked ✅

### CR-086: Optimize Test Execution

**Status:** ✅ Clean

- `pytest.ini` exists with marker taxonomy ✅
- `tests/dependency_map.yaml` exists ✅
- `docs/internal/code-index/module-tags.yaml` exists ✅
- `fullprosmaker --fast` and `--max-lines` available ✅
- All 8 AC checkboxes checked ✅

### CR-087: Phase 1 Module Splitting

**Status:** ✅ Clean

- `_phonetize_config.py` exists ✅
- `_prosody_text.py` exists (types consolidated here per CR-091 note) ✅
- `prosody_model.py` and `prosody_engine.py` exist ✅
- `_syllabify_escape.py` exists ✅
- `lib/tests/phonetize_tests.py`, `prosody_tests.py`, `syllabify_tests.py` exist ✅
- `_prosody_types.py` was consolidated into `_prosody_text.py` (documented deviation) ✅
- All 10 AC checkboxes checked ✅

### CR-088: Extend Emphatic Vowel Coloring

**Status:** ✅ Clean

- `limit_emphatic_coloring: false` present (after CR-089 rename) ✅
- All 17 AC checkboxes checked ✅

### CR-089: Rename to limit_emphatic_coloring

**Status:** ✅ Clean

- `extended_emphatic_coloring` removed from schema ✅
- `limit_emphatic_coloring` present with default `false` ✅
- All 7 AC checkboxes checked ✅

### CR-090: Add Experimental Feature Guard

**Status:** ✅ Clean

- `allow_experimental: false` present ✅
- All 7 AC checkboxes checked ✅

### CR-091: Phase 2 Module Splitting (metrics)

**Status:** ⚠️ Governance inconsistency

**Observation:** CR-091 is marked `status: Done` but:
- All implementation tasks remain unchecked `[ ]`
- The CR body states "None of the splits proposed in this CR have been implemented"
- `_metrics_stats.py` does NOT exist
- `_metrics_output.py` does NOT exist
- `metrics.py` remains monolithic (~1780 lines)

**Impact:** CR-092 supersedes CR-091 (partial) and correctly implements the
`phoneprep`, `print`, and `config` splits that CR-091 proposed. However,
CR-092's scope explicitly excludes `metrics.py` ("metrics.py was split by
CR-091 and is NOT in scope for this CR"). Since CR-091 was never implemented,
the metrics split is in limbo — neither CR-091 nor CR-092 delivered it.

**Recommendation:** Either:
1. Mark CR-091 as `Superseded` (not `Done`) and create a new CR for the
   metrics split, OR
2. Update CR-091 to accurately reflect that only the `prosody_types`
   consolidation was done, and mark the metrics split as deferred.

### CR-092: Phase 2 Module Splitting (remaining)

**Status:** ✅ Clean

- `_phoneprep_phonology.py` exists ✅
- `_phoneprep_io.py` exists ✅
- `_print_ipa.py` exists ✅
- `_print_pho.py` exists ✅
- `_config_io.py` exists ✅
- `lib/tests/phoneprep_tests.py` exists ✅
- `lib/tests/print_tests.py` exists ✅
- All 12 AC checkboxes checked ✅

---

## Overall Assessment

**Status:** Clean — one governance inconsistency found.

11 of 12 reviewed CRs are fully implemented with all acceptance criteria
satisfied. The sole issue is CR-091's status being `Done` when its metrics
split was never implemented.

### Recommended Actions

1. **Required:** Fix CR-091 governance inconsistency — either mark as
   `Superseded` or update status to reflect actual completion state.
2. **Optional:** Create a follow-up CR for the `metrics.py` split if still
   desired.

---

## Verification Commands

```bash
python -m pytest --tb=short -q    # 367 passed
python scripts/update-indexes.py  # indexes regenerated
```
