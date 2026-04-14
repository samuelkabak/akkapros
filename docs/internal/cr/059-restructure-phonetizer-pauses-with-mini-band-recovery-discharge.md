---
cr_id: CR-059
status: Blocked
priority: High
impact: Mutative
created: 2026-04-14
updated: 2026-04-14
implements: 'ADR-045, REQ-030, REQ-031'
---

# Change Request: Restructure Phonetizer Pauses with Mini-Band Recovery Discharge

# Summary

Restructure the active phonetizer pause contract from a two-length short/long
model to a three-length mini/short/long model, add an explicit recovery-pause
type, and make row-level drift discharge more frequent by allowing the
phonetizer to insert mini recovery pauses at eligible prosodic-unit boundaries.

This CR narrows the current pause typing and duration realization contracts in
[CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)
and the current downstream metrics contract in
[CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md). It is
grounded in current repository reality: the phonetizer already owns pause rows,
the current duration solver already tracks signed running drift, and metrics
already consumes phonetizer frontmatter drift summaries, but the live system
still has only short/long pause lengths, no recovery-pause row type, and no
mini-band discharge path.

---

# Motivation

Current pause handling is too coarse for the intended timing behavior.

Repository inspection on 2026-04-14 shows that the active code and docs still
assume only two pause lengths and no inserted recovery row:

- `src/akkapros/lib/phonetize.py` defines only `short` and `long` pause bands
  in `PHONETIZE_SCHEMA`.
- `src/akkapros/lib/phonetize.py` still exposes `short_pause_policy` and a
  two-branch `_pause_duration_and_drift()` path keyed only by `length == 'L'`
  versus not-long.
- `src/akkapros/lib/phonetize.py` currently creates pause rows only from
  punctuation suites or normalized final `<EOL>` insertion; `realize_phone_rows`
  fills durations but does not insert new pause rows during drift discharge.
- `src/akkapros/config/default.yaml` still defaults to `short_pause_policy:
  "strict"`, `drift_tolerance: 12`, `pauses.short: 600-680`, and
  `pauses.long: 1200-1780`.
- `src/akkapros/lib/helpmsg.py`, `src/akkapros/lib/config.py`,
  `src/akkapros/cli/phonetizer.py`, and `src/akkapros/cli/fullprosmaker.py`
  still expose `short_pause_policy` and the current drift policy surface.
- `docs/akkapros/phonetizer.md`,
  `docs/akkapros/phonetizer-algorithm.md`, and
  `docs/akkapros/phonetizer-phone-file-guide.md` still document only pause
  types `Q`, `S`, `E`, `C`, and `I`.
- `metrics.py` currently extracts only drift max/mean/stddev from phonetizer
  frontmatter and does not surface counts for incomplete pause unloading.

The requested change is broader than a config edit. It changes the pause row
contract, narrows the public config and CLI surface, changes what Pass 2 is
allowed to do, and adds new drift diagnostics that downstream metrics must
carry.

---

# Scope

## Included

- Add three active pause lengths for silence rows: `M` mini, `S` short, and
  `L` long.
- Add pause type `R` for phonetizer-inserted recovery pauses.
- Update the active pause-table contract so it includes the new recovery row and
  the revised `I` row semantics.
- Add `phonetize.process.timing_model.durations.pauses.mini.min` and
  `phonetize.process.timing_model.durations.pauses.mini.max`.
- Replace the current default short and long pause ranges with the new values
  requested here.
- Remove `short_pause_policy` from the active config/help/CLI contract.
- Set the default `drift_tolerance` to `35` ms.
- Narrow drift handling to extensible-only runtime behavior; strict failure is
  no longer an active supported mode.
- Allow Pass 2 to insert mini recovery-pause rows at eligible `boundary=F`
  locations when running drift reaches the mini-band trigger threshold and no
  punctuation-owned pause row already follows.
- Keep short and long pause rows responsible for ordinary punctuation-owned
  discharge behavior.
- Count how often short pauses and long pauses finish with residual drift still
  carried forward.
- Count how often syllable-duration correction has to touch vowel duration after
  drift is exhausted to the active tolerance band.
- Count how often vowel-duration correction reaches a legal limit but still
  cannot resolve the mismatch and must therefore return the remainder to drift.
- Propagate the new recovery/incomplete-unload diagnostics through phonetizer
  frontmatter, fullprosmaker data output, and metricalc drift-facing output.
- Require `metricalc` and `metrics` reporting to include a `Pause metrics`
  section/object listing, for each pause type `Q`, `S`, `E`, `C`, `I`, and
  `R`, the row-derived count and average duration.
- Update default config, confwriter surfaces, CLI help, package docs, demo
  configs, and tests to match the new contract.

## Not Included

- Implementing production code in this CR document.
- Redesigning pause-type precedence for `Q`, `S`, `E`, `C`, and `I` beyond the
  additions and clarifications stated here.
- Replacing the `_phone.txt` / `_ophone.txt` downstream ownership introduced by
  earlier records.
- Changing metricalc interval formulas governed by
  [CR-046](046-redesign-metricalc-around-phone-ophone-interval-metrics.md).
- Reopening prosody-stage merge logic or printer rendering beyond the pause and
  drift diagnostics that must travel downstream.

---

# Current Behavior

Current repository behavior still reflects the earlier two-band pause model.

Observed current behavior:

- `src/akkapros/lib/phonetize.py` defines pause duration bands only under
  `pauses.short` and `pauses.long`.
- `src/akkapros/lib/phonetize.py` uses `_new_pause_row(text, *, pause_type,
  is_long)` and records pause `length` only as `S` or `L`.
- `src/akkapros/lib/phonetize.py` classifies pause type with precedence
  `Q > E > S > C > I`; there is no active `R` type.
- `src/akkapros/lib/phonetize.py` currently treats Pass 2 as duration-only:
  `_partition_phone_units()` consumes already-built rows and `realize_phone_rows`
  fills `duration` in place without inserting new rows.
- `_preferred_pause_target()` and `_pause_duration_and_drift()` choose between
  `pauses.short` and `pauses.long`; there is no mini-band path.
- For long pauses, `_pause_duration_and_drift()` resets running drift to zero;
  for short pauses, residual drift may remain and carry forward.
- `src/akkapros/lib/phonetize.py` already applies vowel-range correction after
  initial syllable assignment, but the live contract does not count or report
  how often vowel correction is used or how often vowel correction saturates and
  the unresolved remainder returns to drift.
- `src/akkapros/config/default.yaml` still carries `short_pause_policy:
  "strict"`, `drift_policy: "extensible"`, and `drift_tolerance: 12`.
- `src/akkapros/lib/helpmsg.py`, `src/akkapros/lib/config.py`,
  `src/akkapros/cli/phonetizer.py`, and `src/akkapros/cli/fullprosmaker.py`
  still expose `short_pause_policy` as a first-class option.
- `docs/akkapros/phonetizer-phone-file-guide.md` currently documents the pause
  type inventory as `Q`, `E`, `S`, `C`, and `I` only.
- `tests/test_phonetize_lib.py` currently covers short-pause residual carry and
  long-pause reset, but not inserted recovery pauses or mini-band discharge.
- `metrics.py` currently extracts only drift `max`, `mean`, and `stddev` from
  phonetizer frontmatter and prints only those values in the drift section.

---

# Proposed Change

Adopt the following contract.

## 1. Supersession and precedence

- This CR narrows the pause-row contract in
  [CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)
  by adding recovery type `R`, adding mini length `M`, and allowing Pass 2 to
  insert recovery pause rows at runtime.
- This CR narrows the drift-facing reporting contract in
  [CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md) by adding
  drift-adjacent recovery and incomplete-unload counters to phonetizer and
  metrics outputs and by requiring a new per-type `Pause metrics` reporting
  surface in table and JSON output.
- Older records remain historical context. When this CR and the earlier records
  disagree on pause lengths, pause row insertion, or drift diagnostics, this CR
  is the active contract.

## 2. Active pause row contract

Pause rows remain `category = 'S'`, but the active silence inventory changes as
follows.

| Category | Type | Meaning | Expected length |
| --- | --- | --- | --- |
| `S` | `Q` | question pause | `L` |
| `S` | `S` | statement pause | `L` |
| `S` | `E` | exclamation pause | `L` |
| `S` | `C` | continuation pause | `S` |
| `S` | `R` | Recovery pause | `M` |
| `S` | `I` | internal no-intonation pause | `S` by default, may be `L` if created by long-only unsupported class |

Additional rules:

- `M`, `S`, and `L` are active pause-length values only for silence rows.
  Non-silence segment rows keep their existing length semantics.
- Recovery pause rows are phonetizer-inserted rows and do not come from source
  punctuation. Their `text` field shall therefore be empty.
- This CR does not require a new non-long pause realization glyph. Recovery
  rows may continue to use the existing non-long pause label/realization family
  so long as `type = 'R'` and `length = 'M'` carry the new semantics.
- `R` behaves like `I` for intonation purposes: it does not impose a clause-
  final contour on the preceding syllable.

## 3. Pause-band config and public surface

The active pause-band configuration becomes:

```yaml
        pauses:
          # Default mini-pause band. Empirically grounded short-pause region from
          # comparative studies, based on the max duration not perceived as a pause.
          # Below the minimum the pause is perceived as part of the segment.
          # The brain can maintain rhythmic synchronization during brief gaps, but
          # entrainment begins to drop significantly when anisochrony reaches the mini
          # pause range.
          # The algorithm uses the mini pause for rhythmic alignment to multiple
          # N * cvc_reference by unloading the accumulated drift more often.
          mini:
            # Minimum short-pause duration.
            min: 100
            # Maximum unperceived-pause duration.
            max: 200
          # Default short-pause band. Empirically grounded short-pause region from
          # comparative studies. Rhythmic alignment remains possible when at least one
          # integer multiple N * cvc_reference falls inside this band without redefining
          # the empirical range.
          short:
            # Minimum short-pause duration.
            min: 280
            # Maximum short-pause duration.
            max: 350
          # Default long-pause band. Clause-boundary range from comparative pause data.
          # If rhythmic alignment is used, enumerate all integer multiples N *
          # cvc_reference inside this band. Choose the candidate nearest the band
          # center; if two are equally near, choose the smaller one.
          long:
            # Minimum long-pause duration.
            min: 730
            # Maximum long-pause duration.
            max: 930
```

Public-surface changes:

- `phonetize.process.timing_model.short_pause_policy` is removed completely from
  the active config/help/CLI contract.
- The active default for `phonetize.process.timing_model.drift_tolerance` is
  `35` ms.
- The phonetizer runtime shall behave as extensible-only. Public docs and help
  shall no longer present strict drift failure as an active supported mode.
- A compatibility bridge may accept legacy `drift_policy: strict` inputs only
  to coerce them to extensible behavior with a warning, but that compatibility
  path is transitional and must not remain the documented active contract.

## 4. Recovery-pause insertion algorithm

Pass 2 is no longer duration-only immutable. It may insert recovery pause rows
while realizing durations.

Eligibility rules:

- Recovery insertion is evaluated only after a row whose `boundary = 'F'`.
- Recovery insertion is evaluated only when the following emitted row is a new
  segment row rather than an existing silence row.
- Recovery insertion is not allowed inside a merged unit and is not allowed
  before punctuation-owned pause rows.
- The recovery trigger threshold is the lower edge of the mini band:
  `abs(running_drift_ms) >= pauses.mini.min`.

Behavior:

- When the eligibility rules hold, the phonetizer shall insert one pause row
  with `category = 'S'`, `type = 'R'`, `length = 'M'`, and empty `text`.
- The inserted recovery row shall choose a legal duration inside the configured
  mini band that drives signed drift as close to zero as possible.
- If a legal mini-band duration can unload drift fully, the recovery row shall
  do so.
- If full discharge is impossible inside the mini band, the recovery row shall
  maximize discharge toward zero and carry the remaining drift forward under the
  same extensible semantics used elsewhere.
- Existing punctuation-owned short and long pauses continue to realize after the
  current row sequence exactly as before; no recovery row is inserted in front
  of them.

## 5. Short and long pause discharge accounting

Short and long pauses remain allowed to leave residual drift when their legal
bands block complete discharge.

The active syllable-duration correction algorithm is:

Control reminder for reporting context:

- The phonetizer already has an established syllable-duration solver that uses
  drift handling and legal vowel-range correction to approach the target timing
  implied by `cvc_reference`.
- This CR does not redefine that working solver step-by-step.
- The reporting goal here is only to surface two high-level events already
  meaningful in that solver:
  - the solver had to touch vowel duration because drift tolerance alone was
    insufficient
  - vowel adjustment reached a legal boundary and the unresolved remainder had
    to remain or return in drift
- Any implementation must preserve the current working timing algorithm and add
  reporting around those outcomes rather than narrowing the solver through an
  incomplete restatement in specification text.

The phonetizer shall count and report at minimum:

- `recovery_pause_count`: number of inserted recovery pause rows
- `short_pause_partial_unload_count`: number of short pauses that did not bring
  running drift fully to zero
- `long_pause_partial_unload_count`: number of long pauses that did not bring
  running drift fully to zero
- `vowel_correction_count`: number of syllables where the solver had to adjust
  vowel duration after drift absorption up to tolerance was insufficient
- `vowel_correction_return_to_drift_count`: number of syllables where vowel
  correction hit a legal boundary and the unresolved remainder had to return to
  running drift

These counters shall be emitted alongside the existing drift summary and shall
travel in the same phonetizer-owned data path that already carries drift max,
mean, stddev, extension count, and max extension.

## 6. Downstream propagation and metrics reporting

- Phonetizer frontmatter data shall include all five new counters for both the
  original and accentuated streams.
- `fullprosmaker` shall propagate those counters anywhere it already propagates
  phonetizer drift summaries.
- `metricalc` shall surface the new counters next to the drift summary in JSON
  and human-readable output.
- Where metrics reads phonetizer frontmatter drift summaries, the extraction
  contract shall be extended to include the new counters.

Pause-metrics reporting contract:

- `metricalc` and `metrics` shall emit a per-stream `Pause metrics` reporting
  surface in both human-readable table output and JSON output.
- The active pause inventory reported there is `Q`, `S`, `E`, `C`, `I`, and
  `R`.
- For each reported stream separately, every one of those six pause types shall
  be present even when the count is zero.
- For each pause type, metrics shall report:
  - `count`: number of realized silence rows whose `type` equals that code
  - `average_duration_ms`: arithmetic mean realized duration of rows with that
    pause type, or `0` when `count == 0`
- These values are row-derived from the realized `_phone.txt` / `_ophone.txt`
  stream being reported and shall not be reconstructed from punctuation.
- Human-readable table output shall use the exact section label
  `Pause metrics:`.
- JSON output shall expose a per-stream `pause_metrics` object keyed by pause
  type letter.

Minimum human-readable shape:

```text
Pause metrics:
  Q: count ..., average duration ... ms
  S: count ..., average duration ... ms
  E: count ..., average duration ... ms
  C: count ..., average duration ... ms
  I: count ..., average duration ... ms
  R: count ..., average duration ... ms
```

Minimum JSON shape per stream:

```json
{
  "pause_metrics": {
    "Q": {"count": 0, "average_duration_ms": 0},
    "S": {"count": 0, "average_duration_ms": 0},
    "E": {"count": 0, "average_duration_ms": 0},
    "C": {"count": 0, "average_duration_ms": 0},
    "I": {"count": 0, "average_duration_ms": 0},
    "R": {"count": 0, "average_duration_ms": 0}
  }
}
```

## 7. Documentation, help, demo, and test alignment

The following surfaces shall be updated to the new contract:

- default grouped config and generated config docs
- `confwriter` list/get/set/default/help surfaces
- standalone phonetizer CLI help and fullprosmaker phonetize-stage help
- phonetizer algorithm docs and phone-row reading guide
- configuration docs and any package docs that describe pause bands or drift
  policy
- metrics docs that describe table and JSON output shape
- demo YAML configs under `demo/akkapros/`
- demo result snapshots and examples that embed the old config values or pause
  inventory
- phonetizer library tests, phonetizer CLI/config tests, fullprosmaker tests,
  and any metrics tests that assert the old drift-report shape

The public docs shall explain the algorithm, not only the keys:

- why mini pauses exist
- why recovery pauses are inserted only at `boundary = 'F'`
- why punctuation-owned pauses keep priority over inserted recovery pauses
- how residual drift can remain after short and long pauses
- how the new incomplete-unload counters should be interpreted
- the big-picture control relationship between drift handling and vowel
  correction, without redefining the working solver as a rigid new algorithm
- how the `Pause metrics` section is computed from realized pause-row types and
  durations

---

# Technical Design

Architecture notes:

Components:

- `src/akkapros/lib/phonetize.py`
- `src/akkapros/lib/config.py`
- `src/akkapros/lib/helpmsg.py`
- `src/akkapros/config/default.yaml`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/lib/metrics.py`
- `docs/akkapros/metrics-computation.md`
- `docs/akkapros/phonetizer.md`
- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/phonetizer-phone-file-guide.md`
- `docs/akkapros/configuration.md`
- demo configs under `demo/akkapros/`

Design requirements:

- Generalize pause-band selection from a short/long branch to a mini/short/long
  branch.
- Preserve punctuation-suite classification precedence for `Q`, `E`, `S`, `C`,
  and `I`.
- Add `R` as a phonetizer-inserted silence subtype without making downstream
  stages re-infer recovery pauses from plain text.
- Allow Pass 2 to mutate the row stream only at eligible `boundary = 'F'`
  locations in order to insert recovery pause rows.
- Keep recovery pause insertion deterministic from the row stream plus effective
  config.
- Preserve the existing signed drift model and extend reporting rather than
  replacing it.
- Preserve the current working syllable-timing solver and extend reporting
  around its existing correction decisions rather than redefining the solver in
  specification text.
- Keep metricalc row-derived. No downstream stage may recreate recovery-pause
  logic from source punctuation once phone rows exist.

Recommended implementation direction:

- replace `_new_pause_row(..., is_long)` with a helper that accepts explicit
  pause length `M` / `S` / `L`
- generalize `_preferred_pause_target()` and `_pause_duration_and_drift()` to
  consume the three-band pause contract
- insert recovery rows inside `realize_phone_rows()` only when the boundary and
  next-row eligibility rules hold
- emit the new counters in the phonetizer report object and frontmatter
- count vowel-correction use and vowel-correction saturation/return-to-drift at
  the point in the existing solver where those outcomes are already decided
- extend metrics drift extraction and table formatting to display the new
  counters next to drift summary lines
- remove `short_pause_policy` from schema, config mapping, help registry, and
  dedicated CLI flags
- stop documenting `strict` as an active drift behavior and align runtime
  compatibility handling accordingly

---

# Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/lib/config.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/config/default.yaml`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/cli/fullprosmaker.py`
`src/akkapros/lib/metrics.py`
`tests/test_phonetize_lib.py`
`tests/test_config_support.py`
`tests/test_selftests_cli.py`
`tests/test_selftests_lib.py`
`tests/test_integration.py`
`docs/akkapros/phonetizer.md`
`docs/akkapros/phonetizer-algorithm.md`
`docs/akkapros/phonetizer-phone-file-guide.md`
`docs/akkapros/configuration.md`
`docs/akkapros/metrics-computation.md`
`demo/akkapros/lexlinks/construct-demo.yaml`
`demo/akkapros/prosmaker/corpus-demo.yaml`

---

# Acceptance Criteria

- [ ] Given the active pause-type table is documented, when silence rows are
      described, then it includes `| \`S\` | \`R\` | Recovery pause | \`M\` |`
      and the `I` row reads `S by default, may be L if created by long-only
      unsupported class`.
- [ ] Given the grouped config schema is inspected, when pause bands are listed,
      then `pauses.mini.min = 100`, `pauses.mini.max = 200`,
      `pauses.short.min = 280`, `pauses.short.max = 350`, `pauses.long.min =
      730`, and `pauses.long.max = 930` are the active defaults.
- [ ] Given the grouped config, confwriter surfaces, CLI flags, and help text
      are inspected, when pause-policy options are listed, then
      `short_pause_policy` is absent from the active contract.
- [ ] Given the default phonetizer timing config is inspected, when drift
  tolerance is read, then the active default is `35` ms.
- [ ] Given the active phonetizer runtime contract is inspected, when drift
      policy behavior is described, then strict failure is not presented as an
      active supported mode.
- [ ] Given Pass 2 reaches a row with `boundary = 'F'`, when the next emitted
      row is a new segment row and no silence row already follows, then a
      recovery pause may be inserted only if `abs(running_drift_ms) >=
      pauses.mini.min`.
- [ ] Given Pass 2 reaches a row with `boundary = 'F'`, when a punctuation-
      owned silence row already follows, then no recovery row is inserted in
      front of that existing pause.
- [ ] Given a recovery pause row is inserted, when its row fields are inspected,
      then it uses `category = 'S'`, `type = 'R'`, `length = 'M'`, and empty
      `text`.
- [ ] Given a legal mini-band duration can fully discharge recovery drift, when
      a recovery row is realized, then it brings running drift to zero.
- [ ] Given a legal mini-band duration cannot fully discharge recovery drift,
      when a recovery row is realized, then it maximizes discharge toward zero
      and carries the remainder forward without strict failure.
- [ ] Given a short pause ends with residual drift still carried forward, when
      phonetizer diagnostics are emitted, then `short_pause_partial_unload_count`
      increments.
- [ ] Given a long pause ends with residual drift still carried forward, when
      phonetizer diagnostics are emitted, then `long_pause_partial_unload_count`
      increments.
- [ ] Given recovery pauses are inserted, when phonetizer diagnostics are
      emitted, then `recovery_pause_count` equals the number of inserted `R`
      rows.
- [ ] Given syllable realization reaches the point where drift absorption up to
  `drift_tolerance` is insufficient, when the solver adjusts vowel duration,
  then `vowel_correction_count` increments.
- [ ] Given syllable realization reaches a legal vowel-range boundary and still
  cannot resolve the mismatch, when the unresolved remainder is returned to
  running drift, then `vowel_correction_return_to_drift_count` increments.
- [ ] Given phonetizer frontmatter data is inspected, when drift diagnostics are
  read, then the new counters appear alongside drift max/mean/stddev and the
  existing extension diagnostics.
- [ ] Given fullprosmaker output data is inspected, when phonetizer drift data
      is propagated, then the new counters are preserved for both streams.
- [ ] Given metricalc human-readable output is inspected, when a reported stream
  block is printed, then it contains a `Pause metrics:` section listing `Q`,
  `S`, `E`, `C`, `I`, and `R` with count and average duration in
  milliseconds.
- [ ] Given metricalc JSON output is inspected, when a reported stream block is
  read, then it contains a `pause_metrics` object keyed by `Q`, `S`, `E`,
  `C`, `I`, and `R`, each with `count` and `average_duration_ms`.
- [ ] Given a reported stream contains no rows for one or more pause types,
  when `Pause metrics` is emitted, then the missing types still appear with
  `count = 0` and `average_duration_ms = 0`.
- [ ] Given a reported stream contains realized pause rows of multiple types,
  when `Pause metrics` is computed, then each type's `count` and
  `average_duration_ms` are derived only from rows whose `type` matches that
  code.
- [ ] Given metricalc drift diagnostics are inspected, when drift summary is
  printed, then the new recovery, partial-unload, vowel-correction, and
  return-to-drift counters still appear next to drift max/mean/stddev in
  addition to the standalone `Pause metrics:` section.
- [ ] Given demo configs and package docs are inspected, when phonetizer pause
      and drift settings are explained, then they describe the mini/short/long
      pause bands, recovery pause insertion algorithm, removal of
      `short_pause_policy`, and the non-strict extensible-only behavior.
- [ ] Given unit and integration tests are inspected, when phonetizer pause
      behavior is covered, then tests exist for recovery-pause insertion,
      punctuation-owned pause precedence over recovery insertion, mini-band
      discharge, residual short/long pause counting, and the updated config/help
      surface.

---

# Risks / Edge Cases

Possible issues:

- Recovery insertion changes the earlier Pass 2 assumption that the row stream
  is immutable after Pass 1.
- Recovery insertion must not create cascades of adjacent mini pauses across the
  same boundary.
- If legacy configs still set `short_pause_policy` or `drift_policy: strict`,
  the transition behavior must be documented clearly to avoid silent surprise.
- Lowering `drift_tolerance` from the requested earlier draft value changes how
  often vowel correction is invoked and will therefore affect emitted
  diagnostics and exact timings.
- Lower pause bands will change emitted durations, demo snapshots, and any tests
  that assert exact row timings.
- `I` rows can still be short or long depending on unsupported punctuation
  suites, so downstream docs must not collapse `I` to only one duration class.
- Metrics and docs must distinguish recovery insertion counts from partial-
  unload counts; they are not the same signal.

---

# Testing Strategy

Unit tests:

- recovery pause is inserted only after eligible `boundary = 'F'` rows
- recovery pause is not inserted when a punctuation-owned pause row already
  follows
- recovery row fields are `S/R/M` with empty `text`
- mini-band discharge chooses a legal duration and drives drift toward zero
- short and long partial-unload counters increment only in the intended cases
- legacy `short_pause_policy` surface is absent from config and CLI mappings
- drift-tolerance default is `35`
- `vowel_correction_count` increments only when vowel duration must be adjusted
  after drift absorption reaches tolerance
- `vowel_correction_return_to_drift_count` increments only when vowel
  correction saturates at a legal bound and the remainder returns to drift
- per-stream `pause_metrics` includes `Q`, `S`, `E`, `C`, `I`, and `R` with
  row-derived count and average duration values

Integration tests:

- phonetizer and fullprosmaker propagate recovery/incomplete-unload counters in
  frontmatter and result data
- phonetizer and fullprosmaker propagate vowel-correction and return-to-drift
  counters in frontmatter and result data
- metricalc displays the new drift-adjacent counters and the per-stream
  `Pause metrics:` section/object in both table and JSON output
- docs/help/config emission aligns with the updated pause inventory and config
  surface

Manual verification:

- inspect representative `_phone.txt`, `_ophone.txt`, metrics JSON, and metrics
  table outputs to confirm recovery pauses appear only at eligible `F`
  boundaries and that drift counters match the realized row stream

---

# Rollback Plan

Revert the implementation that introduces mini-band recovery pauses, restore
the earlier short/long pause model, and reinstate the prior config/help surface
if needed.

Because this CR changes pause lengths, emitted rows, and drift-report shape,
rollback must be treated as a full contract reversal rather than a partial
toggle.

---

# Related Issues

- [CR-047](047-close-phonetizer-pause-and-reconstruction-gaps.md)
- [CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)
- [CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md)
- [ADR-045](../adr/045-three-pass-phonetizer-intonation-and-row-derived-mbrola.md)
- [REQ-030](../req/030-phone-ophone-only-metrics-and-interval-rhythm-computation.md)
- [REQ-031](../req/031-phone-artifact-handoff-and-downstream-consumption.md)

---

# Tasks

## Implementation

- [ ] Add mini-band pause configuration and remove `short_pause_policy`
- [ ] Add recovery pause row support and Pass 2 insertion logic
- [ ] Change the active drift runtime to extensible-only behavior
- [ ] Emit recovery/incomplete-unload diagnostics in phonetizer outputs
- [ ] Emit vowel-correction and return-to-drift diagnostics in phonetizer
  outputs
- [ ] Propagate the new diagnostics through fullprosmaker and metricalc
- [ ] Add per-type `Pause metrics` aggregation and output in metrics table and
  JSON reporting

## Tests

- [ ] Add unit tests for recovery insertion eligibility and row shape
- [ ] Add unit tests for mini-band discharge and residual counter behavior
- [ ] Add unit tests for vowel-correction counting and return-to-drift counting
- [ ] Update config/help/CLI tests for removed `short_pause_policy` and updated
      defaults
- [ ] Update integration tests for frontmatter propagation and metrics output

## Documentation

- [ ] Update pause-type tables and phone-row guides for `R` and `M`
- [ ] Rewrite phonetizer docs and help to explain the recovery insertion
      algorithm and extensible-only drift behavior
- [ ] Update grouped config docs, confwriter docs, and demo configs to the new
      pause bands and defaults
- [ ] Update metrics docs to explain the per-stream `Pause metrics` section and
  JSON object

## Review

- [ ] Verify the new CR against live phonetizer, fullprosmaker, and metricalc
      code paths before implementation starts
- [ ] Confirm all stale short-pause-policy and strict-drift references are
      removed from public docs and help surfaces

---

# Implementation Blockers

## 2026-04-14 - CR sequencing blocked by earlier unfinished record

- Type: `governance conflict`
- Observed: [CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md)
  is still `Draft`, and repository guidance requires CRs to be implemented in
  identifier order.
- Why blocked: safe implementation and verification of CR-059 cannot begin
  while the directly earlier CR remains not `Done`.
- Needed to unblock: move CR-058 to `Done`, or explicitly re-sequence/split the
  affected scope so CR-059 no longer depends on an unfinished earlier record.
- Owner: `maintainer`
- Related refs: [docs/internal/README.md](../README.md),
  [CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md)

---

# Notes

- This CR is intentionally specification-only. Implementation is deferred.
- The requested mini-pause trigger phrase "when the drift value reaches the
  pauses.mini.short" is normalized here to `abs(running_drift_ms) >=
  pauses.mini.min` because the requested config shape does not define a
  separate trigger key.
- This CR keeps punctuation-owned pauses as the primary externally visible
  silence events and treats recovery pauses as phonetizer-internal inserted rows
  that nevertheless travel downstream once materialized.