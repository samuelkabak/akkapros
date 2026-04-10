---
cr_id: CR-047
status: Done
priority: High
impact: Mutative
created: 2026-04-10
updated: 2026-04-10
implements: 'ADR-040, ADR-044, REQ-005, REQ-025, REQ-030, REQ-031'
---

# Change Request: Close Phone-Handoff Pause and Downstream Consumption Gaps

# Summary

Close the specification and implementation gaps discovered during verification
of the CR-033 through CR-046 transition story.

The active phonetizer-to-metricalc pipeline is largely aligned with the newer
records, but the repository still leaves four important gaps: a missing final
line break is not normalized into a final long pause before phone output is
written, mixed punctuation-suite precedence is not pinned clearly in tests and
docs, the phone-row handoff is not yet the single active source for downstream
pause semantics and printer input, and stale removed metrics surfaces still
survive in helper code and help registries.

This CR narrows and completes the active contract without rewriting the older
accepted records as though these details had already been settled.

---

# Motivation

The repository now treats phonetizer-owned `_ophone.txt` and `_phone.txt`
artifacts as the active handoff into metrics, but it still leaves printer on an
older `_tilde` input contract. That split is no longer coherent if pause
classification and line-break semantics are supposed to be determined once and
then reused consistently downstream.

During verification of the implemented CR-033 through CR-046 chain, the live
code, tests, and docs showed that the main architecture is in place, but some
important edge semantics are still under-specified or only emergent from the
current code:

- explicit newlines are encoded as long pauses, but a missing final line break
  is not normalized before phone output is written
- an armored punctuation suite containing at least one long-pause cue is
  currently classified as one long pause row, but that precedence is not pinned
  as an explicit active contract
- printer still remains documented and implemented as a `_tilde` consumer even
  though pause information should now come from `_phone` / `_ophone`
- removed metrics surfaces such as explicit-link overrides still survive in
  stale helper/help code even though the active CR-046 contract removed them

Those gaps matter because pause semantics influence timing and later intonation,
and the repository now needs one active downstream source of truth for short
and long pauses rather than separate re-inference paths from `_tilde`.

---

# Scope

## Included

- Make phonetizer-owned phone rows the explicit active owner of pause
  classification for the `_ophone.txt` + `_phone.txt` -> metrics and printer
  pipelines.
- Normalize missing final line breaks before phone output is written: if the
  consumed input has no final break, the emitted downstream text/row contract
  must contain one.
- Treat that normalized final line break as a long pause through the same row
  pathway used for ordinary explicit line breaks.
- Define mixed punctuation-suite precedence explicitly: one long-pause cue in a
  punctuation suite is sufficient to classify the whole suite as long.
- Pin the punctuation-suite rule in tests and user-facing docs.
- Make `_phone.txt` / `_ophone.txt` the active downstream inputs for printer as
  well as for metrics.
- Require metrics and printer to derive short-pause and long-pause behavior
  from the phone-row stream only and not to recompute pause classes from
  `_tilde` or plain text.
- Preserve YAML front matter on both `_phone.txt` and `_ophone.txt` as part of
  the active downstream artifact contract.
- Add a dedicated user-facing Markdown reading guide under `docs/akkapros/`
  that explains how to read `_phone.txt` and `_ophone.txt` files, including the
  fixed-width compact row fields and how those files encode boundaries, pauses,
  accent, realization, duration, and source text.
- Remove or explicitly quarantine stale removed metrics surfaces that still
  imply `_tilde`-frontmatter-driven explicit-link overrides or legacy pause
  ownership.
- Update user-facing docs, internal docs, and tests to match the corrected
  contract.

## Not Included

- Redesigning the phonetizer timing model beyond the pause semantics clarified
  here.
- Replacing the `_ophone.txt` + `_phone.txt` handoff introduced by CR-046.
- Reopening MBROLA ownership, which remains governed by CR-045.
- Rewriting older accepted records as though this refinement had always been
  present.

---

# Current Behavior

Repository verification on 2026-04-10 found the following live state.

- `src/akkapros/lib/phonetize.py` emits a `ZEN` / `ZP` long-pause row for an
  explicit newline and stores `<EOL>` in the `text` field, but a source text
  lacking a final break is not normalized into the same long-pause path before
  phone output is written.
- `src/akkapros/lib/phonetize.py` currently classifies an armored punctuation
  suite such as `⟦ ?!!! ⟧` as one long-pause row, because the suite is handled
  as one chunk and long cues win, but that behavior is not pinned explicitly in
  tests or in the public phonetizer docs.
- `src/akkapros/lib/metrics.py` still contains legacy direct-text pause
  inference helpers, including final-EOF long-pause counting, even though the
  active metricalc pipeline now consumes phone rows.
- `docs/akkapros/printer.md` and related older internal records still describe
  printer as a `_tilde` consumer.
- `src/akkapros/lib/helpmsg.py` still contains `metrics.explicit_link_count`
  help text, and `src/akkapros/lib/frontmatter.py` still contains explicit-link
  override helpers tied to the removed `_tilde` frontmatter dependency.

Targeted verification used:

- `pytest tests/test_phonetize_lib.py tests/test_integration.py tests/test_cli_logging.py`
- `pytest tests/test_punctuation_whitelist.py tests/test_metrics_stats.py tests/test_config_support.py`
- direct phonetizer row probes under temporary `tmp/` inspection

Those checks passed for the current covered behavior, which means this CR is a
contract-completion and coverage-hardening follow-up, not a report of a broken
mainline pipeline.

---

# Proposed Change

Adopt the following contract.

## 1. Final-break normalization and pause ownership

- Before downstream phone artifacts are finalized, a missing terminal line break
  in the consumed upstream text must be normalized by insertion of one final
  break.
- That normalized final break is then encoded through the ordinary long-pause
  row path used for explicit line breaks.
- For the active downstream pipeline, pause detection is owned by the phonetizer
  row stream, not by downstream direct-text inference.
- Metricalc must derive active pause metrics from phone rows only.
- Printer must derive visible short-pause and long-pause behavior from phone
  rows only.

## 2. Mixed punctuation-suite precedence

- When the phonetizer receives one punctuation suite as one consumed chunk,
  classification precedence is:
  - long if any long-pause cue is present
  - otherwise short if any short-pause cue is present
  - otherwise fail if undeclared punctuation remains
- This rule applies to armored punctuation spans and to any other upstream
  punctuation-token chunk that reaches phonetizer as a single suite.
- Representative mixed suites such as `?!!!`, `?!`, and short-plus-long mixed
  chunks must be covered in tests and examples.

## 3. Downstream input contract

- `_phone.txt` and `_ophone.txt` are the active downstream inputs for both
  metrics and printer.
- `_phone.txt` and `_ophone.txt` retain YAML front matter.
- `_tilde.txt` remains an upstream prosody pivot only and is no longer the
  active input contract for metricalc or printer.
- Metrics and printer must not recompute pause class from `_tilde`, plain text,
  or punctuation characters when phone rows are available.
- If printer needs distinctions that are currently present only in `_tilde`, the
  phone-row contract must be refined so those distinctions travel in
  `_phone.txt` / `_ophone.txt` instead of leaving printer on `_tilde`.

## 4. Removal of stale removed surfaces

- No active user-facing help, config registry, or runtime API may continue to
  describe `metrics.explicit_link_count` or
  `metadata.data.prosody.explicit_word_link_count` as an active metrics input.
- If legacy helper functions remain for internal non-pipeline tests, they must
  be documented as legacy/internal-only and must not define the active pipeline
  contract.
- Public docs for metricalc, printer, phonetizer, fullprosmaker,
  configuration, and related help surfaces must consistently describe
  phonetizer-owned pause encoding and phone-row downstream input.
- Public docs must include one explicit Markdown reading-guide document under
  `docs/akkapros/` for `_phone.txt` / `_ophone.txt`, because the compact
  fixed-width row format is optimized for space and is not self-explanatory
  without a guide.

## 5. Supersession note

- This CR explicitly supersedes older accepted records where they still state
  that printer consumes `_tilde.txt` as its active downstream input, especially
  [REQ-005](../req/005-multi-format-printer-output.md),
  [ADR-011](../adr/011-multi-format-printer-outputs.md), and
  [CR-037](037-preserve-punctuation-armor-in-tilde-pivot.md).
- Those older records remain historical context. The active downstream contract
  after this CR is that metrics and printer consume `_phone.txt` /
  `_ophone.txt`, while `_tilde.txt` remains an upstream pivot.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/lib/metrics.py`
- `src/akkapros/lib/print.py`
- `src/akkapros/lib/helpmsg.py`
- `src/akkapros/lib/frontmatter.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/cli/printer.py`
- `docs/akkapros/phonetizer.md`
- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/phonetizer-phone-file-guide.md`
- `docs/akkapros/metricalc.md`
- `docs/akkapros/metrics-computation.md`
- `docs/akkapros/fullprosmaker.md`
- `docs/akkapros/printer.md`
- `tests/test_phonetize_lib.py`
- `tests/test_punctuation_whitelist.py`
- `tests/test_metrics_stats.py`
- printer coverage and representative integration coverage in
- `tests/test_integration.py`

Implementation direction:

- Normalize missing final line breaks before phone output is serialized so the
  downstream row stream always closes lexical text with a line-break-driven long
  pause.
- Make punctuation-suite precedence explicit in the phonetizer classifier and
  pin it with direct tests.
- Move printer onto `_phone.txt` / `_ophone.txt` input and require any printer-
  relevant distinctions now found only in `_tilde` to be carried forward in the
  phone-row contract instead.
- Remove stale help/frontmatter references to removed explicit-link override
  surfaces, or demote those helpers to explicitly legacy internal use.
- Keep active metricalc and printer documentation centered on phone-row inputs,
  while clearly separating any remaining legacy direct-text helpers from the
  active pipeline contract.

Compatibility note:

- This CR is allowed to narrow or replace the currently accepted behavior from
  CR-037, CR-039, CR-040, CR-041, and CR-046 where those records leave final-
  break normalization, punctuation-suite precedence, or printer input ownership
  incomplete.

---

# Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/lib/metrics.py`
`src/akkapros/lib/print.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/lib/frontmatter.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/cli/fullprosmaker.py`
`src/akkapros/cli/printer.py`
`docs/akkapros/phonetizer.md`
`docs/akkapros/phonetizer-algorithm.md`
`docs/akkapros/metricalc.md`
`docs/akkapros/metrics-computation.md`
`docs/akkapros/fullprosmaker.md`
`docs/akkapros/printer.md`
`tests/test_phonetize_lib.py`
`tests/test_punctuation_whitelist.py`
`tests/test_metrics_stats.py`
`tests/test_integration.py`

---

# Acceptance Criteria

- [x] If upstream input lacks a final break, downstream phone artifacts are
  normalized so the output has one final break.
- [x] That normalized final break is encoded through the same long-pause row
  pathway used for ordinary explicit line breaks.
- [x] Mixed punctuation suites are classified with explicit long-over-short
      precedence, and this rule is covered by direct tests.
- [x] Metricalc consumes `_phone.txt` / `_ophone.txt` only as its active input
  contract and derives pause semantics from phone rows only.
- [x] Printer consumes `_phone.txt` / `_ophone.txt` only as its active input
  contract and derives pause semantics from phone rows only.
- [x] `_phone.txt` and `_ophone.txt` both retain YAML front matter as active
  downstream artifacts.
- [x] A user-facing Markdown reading guide in `docs/akkapros/` documents how to
  read `_phone.txt` and `_ophone.txt` rows, including each compact field,
  pause rows, boundary codes, accent codes, realization codes, duration
  formatting, and the `text` tail after the colon.
- [x] `_tilde.txt` is no longer documented as the active downstream input for
  metricalc or printer.
- [x] No active help text or config/help registry still advertises
      `metrics.explicit_link_count`.
- [x] No active metrics contract still depends on
      `metadata.data.prosody.explicit_word_link_count`.
- [x] If legacy direct-text metrics helpers remain, docs and tests label them
      internal-only and separate them from the active phone-row pipeline.
- [x] If legacy `_tilde`-driven printer helpers remain during migration, docs
  and tests label them internal-only and separate them from the active
  pipeline contract.
- [x] Public docs are updated so phonetizer pause ownership, final-break
  normalization, punctuation-suite precedence, and phone-row downstream
  consumption are described consistently.
- [x] Integration tests cover at least one no-trailing-newline case and one
  mixed punctuation-suite case in the phonetizer -> metrics handoff and the
  phonetizer -> printer handoff.

---

# Risks / Edge Cases

Possible issues:

- moving printer off `_tilde` may require explicit migration of separator,
  punctuation-armor, and presentation-relevant distinctions into phone rows
- legacy helper behavior may still be needed for isolated tests even after the
  active pipeline contract is cleaned up
- final-break normalization must avoid duplicating an already explicit final
  newline or explicit final punctuation pause
- if the reading guide is omitted or too terse, the compact phone-row files may
  remain effectively opaque to maintainers and reviewers despite being correct

---

# Testing Strategy

Unit tests:

- phonetizer row-building test for missing trailing newline normalized into one
  final long-pause row
- phonetizer row-building test for explicit trailing newline
- phonetizer test for mixed punctuation suites where one long cue makes the
  whole suite long
- printer and metrics tests proving downstream pause handling comes only from
  phone-row inputs
- help/frontmatter tests that removed explicit-link override surfaces are no
  longer active

Integration tests:

- full phonetizer -> metricalc case without trailing newline
- full phonetizer -> metricalc case with a mixed punctuation suite
- full phonetizer -> printer case without trailing newline
- full phonetizer -> printer case with a mixed punctuation suite

Manual review:

- inspect phonetizer, metricalc, and printer docs for consistent pause
  ownership and phone-input wording
- inspect serialized phone rows to confirm final-break normalization and mixed-
  punctuation-suite classification
- inspect the phone/ophone reading guide against real sample rows to confirm it
  is usable without consulting source code

---

# Rollback Plan

If the contract refinement proves too broad, revert the implementation changes
and keep the new CR as the documented follow-up target. Do not partially retain
user-facing claims about final-break normalization or phone-input printer
ownership unless the corresponding row behavior and tests also remain.

---

# Related Issues

- [CR-033](033-remove-long-pause-weight-from-conf-and-cli-options.md)
- [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- [CR-037](037-preserve-punctuation-armor-in-tilde-pivot.md)
- [CR-039](039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
- [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
- [CR-041](041-add-phonetizer-phase-2-follow-up-docs-and-test-coverage.md)
- [CR-045](045-move-mbrola-pho-output-to-phonetizer.md)
- [CR-046](046-redesign-metricalc-around-phone-ophone-interval-metrics.md)
- [ADR-011](../adr/011-multi-format-printer-outputs.md)
- [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- [ADR-044](../adr/044-phone-interval-metrics-from-phonetizer-streams.md)
- [REQ-005](../req/005-multi-format-printer-output.md)
- [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md)
- [REQ-030](../req/030-phone-ophone-only-metrics-and-interval-rhythm-computation.md)
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)

---

# Tasks

## Implementation

- [x] Normalize missing final line breaks before downstream phone output is
  materialized
- [x] Make punctuation-suite precedence explicit in runtime code
- [x] Move printer onto `_phone.txt` / `_ophone.txt` input
- [x] Remove stale explicit-link override help/helper surfaces or mark them
      legacy internal-only

## Tests

- [x] Add direct phonetizer tests for EOF and mixed punctuation suites
- [x] Add integration coverage for phonetizer -> metrics with EOF and mixed
      punctuation suites
- [x] Add integration coverage for phonetizer -> printer with EOF and mixed
  punctuation suites

## Documentation

- [x] Update phonetizer docs with final-break normalization and mixed-suite
  pause rules
- [x] Update metrics, printer, and full-pipeline docs to describe phonetizer-
  owned pause encoding and phone-row downstream input only
- [x] Add a user-facing Markdown phone/ophone reading guide under
  `docs/akkapros/` and link it from phonetizer, metricalc, printer, and
  full-pipeline docs
- [x] Remove stale references to explicit-link override metrics inputs

## Review

- [x] Verify acceptance criteria

---

# Notes

Verification evidence gathered for this CR included source inspection of the
phonetizer, metrics, printer, help, frontmatter, and full-pipeline modules;
targeted pytest coverage for phonetizer, printer, format validation,
integration, and metrics; and direct row-level review confirming that:

- `baba nana` is normalized into one final `<EOL>` long-pause row before phone
  artifacts are serialized
- `baba nana\n` still emits one ordinary explicit `<EOL>` long-pause row
- mixed suites such as `?!!!` are serialized as one long-pause row because
  long cues win within one consumed punctuation chunk
- printer and metricalc both derive pause behavior from `_ophone.txt` and
  `_phone.txt` rather than recomputing it from `_tilde`

Final targeted verification pass:

- `pytest tests/test_phonetize_lib.py tests/test_print_merger.py tests/test_format_validation.py tests/test_integration_append_frontmatter.py tests/test_integration.py tests/test_metrics_stats.py`
- Result: `86 passed`

REQ-025 remains `Draft` because it is an umbrella requirement whose child
records continue to narrow the phonetizer contract. No status change is applied
here.