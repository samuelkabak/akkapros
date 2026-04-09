---
cr_id: CR-035
status: Done
priority: High
impact: Mutative
created: 2026-04-04
updated: 2026-04-09
implements: 'ADR-039, REQ-024'
---

# Change Request: Add phonetize stage config and phone artifact contract

# Summary

Introduce a new pipeline step between prosody/prosmaker and metrics/metricalc:

- CLI: `phonetizer`
- library: `phonetize`

This stage owns the timing-parameter configuration that had previously been
expected to live under metrics. The grouped config gains a new top-level
`phonetize` section with a normative `process` subtree and a normative
`timing_model` subtree, and the stage produces a new intermediate artifact:

- `<prefix>_phone.txt`

This CR defines the approved phonetize config shape directly. The model uses:

- `phonetize.process.geminate_policy`
- `phonetize.process.accentuation_distribution_policy`
- `phonetize.process.short_pause_policy`
- `phonetize.process.drift_policy`
- `phonetize.process.drift_tolerance`
- `phonetize.timing_model.durations.cvc_reference`
- `segmental_ceiling`, class-local `special_realization`, and
  `perception_limits`

This CR also makes the downstream repercussions explicit: config-path docs,
`confwriter` key inventory, `--set` and `--set-default` examples, stage CLI
help surfaces, default config emission, and stage documentation must all align
to the revised `phonetize` key inventory exactly.

---

# Motivation

The timing-model replacement story needs a dedicated intermediate stage rather
than a metrics-owned timing-config surface. A separate phonetize stage creates
a clearer separation of responsibility: prosody produces `_tilde`, phonetize
produces `_phone`, and metrics consumes the phonetic timing representation
rather than defining the timing parameters itself.

The phonetize stage needs a config surface that matches the current timing
model. That model needs:

- explicit process controls for geminate handling, accentuation distribution,
  short-pause discharge, drift recovery, and drift tolerance
- an explicit segment-level ceiling independent of pause bands and CVC totals
- one central heavy-syllable control value `cvc_reference` rather than a
  separate min/max CVC band key
- class-specific consonant anchors with local geminate perception floors
- class-local special realizations for hiatus and vowel-transition timing
- vowel-class perceptual boundaries under `perception_limits`
- one stable approved schema rather than provisional draft variants

Because the package-wide config and `confwriter` surfaces are schema-driven,
any change to this skeleton propagates into YAML path validation, help text,
examples, and generated config comments. The CR therefore needs to specify
those repercussions directly rather than treating the YAML block as an isolated
edit.

---

# Scope

## Included

- Add a new pipeline stage between prosody/prosmaker and metrics/metricalc:
  - CLI `phonetizer`
  - library `phonetize`
- Add a new top-level grouped-config section named `phonetize` with
  normative `process` and `timing_model` subtrees.
- Define the `phonetize.process` and `phonetize.timing_model` default
  structure, comments, ordering, and default values listed in this CR.
- Remove `metrics.wpm` from the grouped config surface.
- Remove `metrics.pause_ratio` from the grouped config surface.
- Keep `metrics.long_punct_weight` absent, consistent with
  [CR-033](033-remove-long-pause-weight-from-conf-and-cli-options.md).
- Specify the new phonetizer output artifact `<prefix>_phone.txt`.
- Specify that each `_phone` file contains one line per phoneme or silence with
  duration in milliseconds plus stage metadata related to syllabification,
  punctuation, boundaries, and related structure.
- Specify that metricalc is currently planned to consume both `_tilde` and
  `_phone` during this transition step.
- Hard-code `wpm` and `pause_ratio` internally inside metrics until the
  phonetize-to-metrics contract is fully operational.
- Centralize phonetize timing defaults and parameter definitions in one shared
  library location.
- Require config-schema, `confwriter`, CLI-help, and docs updates for the new
  key inventory and for removal of the superseded draft keys.
- Require explicit coverage for config-path repercussions, including nested
  `confwriter --set`, `--get`, `--list`, `--unset`, and `--set-default`
  behavior for the revised phonetize paths.
- Require explicit coverage for stage CLI repercussions, including:
  - direct `phonetizer` process-option flags using hyphenated names, for example
    `--geminate-policy`
  - `fullprosmaker` pass-through process-option flags prefixed with
    `--phonetize-`, for example `--phonetize-geminate-policy`
  - `--t` / `--option path=value` support for `phonetize.timing_model` values
    in `phonetizer` and in `fullprosmaker`
- Require explicit coverage for user-facing and developer-facing documentation
  updates across stage docs, configuration docs, and examples.

## Not Included

- Finalizing the long-term metricalc input contract so that `_phone` alone is
  sufficient.
- Finalizing the full downstream printer input contract.
- Finalizing the later phonetizer phase split or dual-phone-output design that
  is handled by later phonetizer records.
- Reintroducing unpublished legacy phonetize draft keys for backward
  compatibility.
- Redesigning unrelated non-timing metrics options.

---

# Current Behavior

The current grouped config planning still reflects an earlier draft timing
model. It exposes flat metrics timing options:

- `metrics.wpm`
- `metrics.pause_ratio`

There is no finalized phonetize-stage schema for the revised timing model, and
there is no finalized `<prefix>_phone.txt` intermediate artifact contract for
the transition from prosody into metrics.

Any provisional phonetize keys outside the schema defined in this CR are out
of contract and must not appear in schema emission, `confwriter` key
inventory, help text, examples, or docs.

---

# Proposed Change

Adopt the following grouped-config shape exactly.

```yaml
phonetize:
  process:
    # geminate realization policy
    # - cumulative: keep coda duration + onset duration instead of correcting to the configured geminate target
    # - corrective: correct the sequence to the configured geminate target
    geminate_policy: corrective
    # this policy indicates how the accentuation mora (0.5 * cvc_reference) is distributed, format N_M
    # N = percentage on the accentuated segment; M = percentage on the adjacent segment
    # Distribution stops when legality ranges would be challenged; if full assignment is impossible, Phase 2 must fail fatally.
    # Allowed values: 100_0, 85_15, 70_30
    accentuation_distribution_policy: 85_15
    # short pause discharge policy
    # - strict: the pause must realize a preferred legal short-band target derived from the nearest integer multiple of cvc_reference,
    #   and it must discharge drift reserve through that target as far as the band allows;
    #   config validation should warn if no integer multiple N * cvc_reference
    #   remains inside the empirically grounded short-pause band, and should fail only if the nearest-multiple gap
    #   exceeds the vowel perception-gap threshold used by shared semantic verification
    # - best_effort: the pause may choose any legal short-band realization that maximizes drift discharge,
    #   and any remainder carries into the following phrase
    short_pause_policy: strict
    # drift recovery policy
    # - strict: use running drift first, then legal vowel adjustment, and fail if the mismatch still cannot be resolved
    # - extensible: use running drift first, then legal vowel adjustment, then extend drift beyond drift_tolerance if needed
    drift_policy: strict
    # maximum local timing mismatch tolerated before the algorithm must fail
    drift_tolerance: 12
  timing_model:
    speech:
      # Speech-rate estimate used by timing and pause logic.
      wpm: 193
      # Share of total time reserved for pauses.
      pause_ratio: 35
    durations:
      # Upper ordinary duration for one vowel or consonant.
      # Model-facing ceiling from comparative duration limits; does not apply to pauses or CVC totals.
      segmental_ceiling: 310
      # Central heavy-syllable timing reference used by accentuation and pause alignment.
      # Set inside the empirically grounded CVC interval 286-306 ms.
      # This keeps the control value conservative and compatible with pause-band alignment
      # whenever at least one integer multiple N * cvc_reference falls inside a configured pause band.
      cvc_reference: 305
      consonants:
        # Stop-like closure class. Includes lexical ʾ.
        closure:
          # Default onset closure duration.
          # Direct comparative stop-closure anchor.
          onset: 108
          # Default post-vocalic closure duration.
          # Direct comparative coda/post-vocalic stop anchor.
          coda: 103
          # Default geminate closure target.
          # Summary point for the attested stop-geminate band.
          geminate: 195
          special_realization:
            # Hiatus or zero-onset marker between adjacent vowels.
            # Unstressed light glottal-stop realization; stressed cases defer to full geminated closure timing.
            hiatus: 18
          perception_limits:
            # Earliest closure duration treated as geminate-like.
            # Perceptual threshold from the stop singleton/geminate contrast, not the lowest measured token.
            geminate_min: 180
        # Fricative class. Heavier than closures by manner, but less directly grounded than the stop row.
        fricative:
          # Default onset fricative duration.
          # Derived from closure onset plus fricative manner delta.
          onset: 137
          # Default post-vocalic fricative duration.
          # Current heavy post-vocalic anchor used by the simplified row.
          coda: 142
          # Default geminate fricative target.
          # Exploratory value based on the current onset + post-vocalic row.
          geminate: 279
          perception_limits:
            # Earliest fricative duration treated as held or geminate-like.
            # Class-specific perceptual floor from weak fricative gemination evidence.
            geminate_min: 152
        # Sonorant, nasal, and glide class.
        sonorant:
          # Default onset sonorant duration.
          # Set from the clearer singleton liquid onset anchor.
          onset: 89
          # Default post-vocalic sonorant duration.
          # Structural minimum retained on the coda side of the row.
          coda: 70
          # Default geminate sonorant target.
          # Set from the direct glide geminate region.
          geminate: 163
          special_realization:
            # Diphthong-internal or glide-like VV transition marker.
            # Unstressed light glide realization; stressed cases defer to full geminated glide timing.
            vowel_transition: 11
          perception_limits:
            # Earliest sonorant duration treated as geminate-like.
            # Lower perceptual boundary from moraic nasal/liquid comparison.
            geminate_min: 152
      vowels:
        # Default short-vowel duration.
        # Production anchor from the retained short-vowel baseline.
        short: 85
        # Default long-vowel duration.
        # Production anchor from the retained long-vowel baseline.
        long: 160
        # Default very-long vowel duration.
        # Contextual extension anchor, not ordinary lexical default.
        very_long: 220
        perception_limits:
          # Minimum duration still treated as a realized short-vowel nucleus.
          short_min: 40
          # Earliest duration treated as long.
          # Midpoint-style boundary derived from short and long anchors.
          long_min: 123
          # Earliest duration treated as very long.
          # Midpoint-style boundary derived from long and very-long anchors.
          very_long_min: 190
          # Upper ordinary bound for contextual vowel extension.
          max: 240
      pauses:
        short:
          # Default short-pause band.
          # Empirically grounded short-pause region from comparative studies.
          # Rhythmic alignment remains possible when at least one integer multiple
          # N * cvc_reference falls inside this band without redefining the empirical range.
          min: 600
          max: 680
        long:
          # Default long-pause band.
          # Clause-boundary range from comparative pause data.
          # If rhythmic alignment is used, enumerate all integer multiples N * cvc_reference inside this band.
          # Choose the candidate nearest the band center; if two are equally near, choose the smaller one.
          min: 1200
          max: 1780
```

Required config behavior:

- `metrics.wpm` is removed.
- `metrics.pause_ratio` is removed.
- The timing parameters above move into `phonetize.process` and
  `phonetize.timing_model` under the top-level `phonetize` section.
- `phonetize.process.drift_tolerance` and all values under
  `phonetize.timing_model.durations` are represented as integer milliseconds.
- `phonetize.timing_model.speech.pause_ratio` is represented as a percentage,
  not as milliseconds.
- The phonetize parameters are part of the canonical default config structure.
- The exact nested key names, comments, ordering, and defaults above must
  propagate unchanged to:
  - canonical config schema emission
  - `src/akkapros/config/default.yaml`
  - `confwriter --list`, `--get`, `--set`, `--unset`, and `--set-default`
    behavior
  - generated YAML comments/help text
  - config documentation
  - CLI help text that explains config integration or override examples
  - pipeline and stage docs that show phonetize timing parameters
- The comments in the normative YAML block are part of the contract and must be
  treated as canonical help text inputs rather than as disposable examples.
- The phonetize section distinguishes strict hiatus timing from stronger
  vowel-transition timing via separate class-local anchors at
  `timing_model.durations.consonants.closure.special_realization.hiatus` and
  `timing_model.durations.consonants.sonorant.special_realization.vowel_transition`.
- `timing_model.durations.consonants.closure.special_realization.hiatus`
  remains below `timing_model.durations.consonants.closure.onset`.
- `timing_model.durations.consonants.sonorant.special_realization.vowel_transition`
  remains below `timing_model.durations.consonants.sonorant.onset`.
- `phonetize.process.geminate_policy` controls whether Phase 2 forces a same-
  consonant coda/onset pair to the configured class geminate target or instead
  keeps the cumulative coda-plus-onset duration. The contract values are
  `corrective` and `cumulative`.
- `phonetize.process.accentuation_distribution_policy` controls the intended
  split of the added accentuation mora between the accentuated segment and its
  adjacent partner. The contract values are `100_0`, `85_15`, and `70_30`.
  These represent percentages of the added mora, not absolute milliseconds.
- `phonetize.process.short_pause_policy` controls whether a short pause must
  realize a preferred legal short-band target or may use any legal short-band
  realization that best discharges drift. The contract values are `strict` and
  `best_effort`.
- Short-pause multiple compatibility with
  `timing_model.durations.pauses.short.{min,max}` is warning-bearing when no
  integer multiple of `timing_model.durations.cvc_reference` falls inside the
  configured short-pause band.
- Short-pause multiple compatibility becomes a blocking verification failure
  when the nearest integer multiple of
  `timing_model.durations.cvc_reference` remains farther from the configured
  short-pause band than
  `timing_model.durations.vowels.perception_limits.long_min - timing_model.durations.vowels.perception_limits.short_min`.
- Long-pause multiple compatibility with
  `timing_model.durations.pauses.long.{min,max}` remains a blocking
  verification condition.
- At each realized pause, the phonetizer must assign a duration that includes
  at least one integer multiple of `timing_model.durations.cvc_reference`.
- Before a pause, accumulated running drift becomes reserve for pause
  discharge.
- In long pauses, that drift reserve must be unloaded completely.
- In short pauses, if the configured pause band prevents complete unloading,
  the phonetizer carries the remaining drift into the following phrase.
- `phonetize.process.drift_policy` controls whether drift recovery must fail
  once legal vowel adjustment is exhausted or may extend beyond configured
  drift tolerance. The contract values are `strict` and `extensible`.
- `phonetize.process.drift_tolerance` is the maximum local timing mismatch
  tolerated before the algorithm must fail under the configured drift policy.
- Those `special_realization` anchors are unstressed baseline values only.
  When a hiatus row is accentuated in Phase 2, duration selection must use
  `timing_model.durations.consonants.closure.geminate`. When a
  vowel-transition row is accentuated in Phase 2, duration selection must use
  `timing_model.durations.consonants.sonorant.geminate`. The emitted row
  identity remains the same in both cases.
- Lexical `ʾ` remains classified under
  `timing_model.durations.consonants.closure` rather than either
  special-realization key.
- The phonetize section defines one top-level
  `timing_model.durations.segmental_ceiling` key and one central
  `timing_model.durations.cvc_reference` key.
- The phonetize section uses class-local `perception_limits` blocks under
  consonant subclasses and under `timing_model.durations.vowels`.
- The phonetize section uses `timing_model.durations.pauses.{short,long}.{min,max}`
  exactly as shown above.
- No keys outside the schema defined in this CR are part of the contract.
- `metrics.long_punct_weight` is not reintroduced.

Required phonetizer stage behavior:

- A new stage runs between prosody and metrics.
- It produces `<prefix>_phone.txt`.
- The file contains one line per phoneme or silence.
- Each line carries a duration in milliseconds plus related metadata for
  syllabification, punctuation, boundaries, and similar structural context.
- The resulting phoneme-row list must support later neighborhood traversal
  across word boundaries; silence rows are the only mandatory stopping points
  for that local traversal logic.

Required metrics behavior for this transition step:

- Metricalc is currently planned to consume both `_tilde` and `_phone`.
- `wpm` and `pause_ratio` are temporarily hard-coded internally inside metrics
  at `193` and `35` until the phonetize-driven contract is fully
  operational.
- Metrics does not consume the `phonetize` config section directly in this
  transitional step.

Required CLI and documentation repercussions:

- Schema-driven config operations must accept the full nested phonetize paths,
  including examples such as:
  - `phonetize.process.geminate_policy`
  - `phonetize.process.accentuation_distribution_policy`
  - `phonetize.process.short_pause_policy`
  - `phonetize.process.drift_policy`
  - `phonetize.process.drift_tolerance`
  - `phonetize.timing_model.speech.wpm`
  - `phonetize.timing_model.durations.segmental_ceiling`
  - `phonetize.timing_model.durations.cvc_reference`
  - `phonetize.timing_model.durations.consonants.closure.geminate`
  - `phonetize.timing_model.durations.consonants.closure.special_realization.hiatus`
  - `phonetize.timing_model.durations.consonants.sonorant.special_realization.vowel_transition`
  - `phonetize.timing_model.durations.consonants.closure.perception_limits.geminate_min`
  - `phonetize.timing_model.durations.vowels.perception_limits.long_min`
  - `phonetize.timing_model.durations.pauses.long.max`
- `phonetizer` must expose `phonetize.process` options as dedicated CLI flags
  using the option name with underscores replaced by hyphens. Representative
  examples:
  - `--geminate-policy corrective`
  - `--accentuation-distribution-policy 85_15`
  - `--short-pause-policy strict`
  - `--drift-policy strict`
  - `--drift-tolerance 12`
- `fullprosmaker` must expose phonetizer-process pass-through flags prefixed
  with `--phonetize-`. Representative examples:
  - `--phonetize-geminate-policy corrective`
  - `--phonetize-accentuation-distribution-policy 85_15`
  - `--phonetize-short-pause-policy strict`
  - `--phonetize-drift-policy strict`
  - `--phonetize-drift-tolerance 12`
- `phonetize.timing_model` options are not exploded into dedicated flags.
  Instead, `phonetizer` and `fullprosmaker` must expose them through
  `--t path=value` and `--option path=value`, where `path` is the full YAML
  path. Representative examples:
  - `--option phonetize.timing_model.speech.wpm=193`
  - `--option phonetize.timing_model.durations.cvc_reference=305`
  - `--option phonetize.timing_model.durations.pauses.short.max=680`
- Any config-path examples, override examples, or help snippets in pipeline
  CLIs and related docs must use only the approved phonetize schema.
- Any user-facing explanation of phonetize timing parameters must explain that
  `perception_limits` are classification boundaries, not runtime pause values
  or alternate emitted duration rows.
- Any user-facing explanation of `phonetize.process` must explain that the
  five process keys are policy controls or tolerances for Phase 2 behavior, not
  free-form timing values.
- Documentation for `phonetizer`, `metricalc`, `fullprosmaker`, package config,
  and `confwriter` must be updated in the same change series so the schema does
  not drift across surfaces.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/lib/metrics.py`
- `src/akkapros/cli/metricalc.py`
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/lib/config.py`
- `src/akkapros/lib/helpmsg.py`
- `src/akkapros/cli/confwriter.py`
- `src/akkapros/config/default.yaml`

Design requirements:

- One canonical library-side phonetize timing definition must hold:
  - process controls
  - default values
  - key inventory
  - type expectations
  - canonical help/comment text
  - ordering metadata needed for config emission and `confwriter` listing
- That canonical definition must match this CR's revised timing model with:
  - `process.geminate_policy`
  - `process.accentuation_distribution_policy`
  - `process.short_pause_policy`
  - `process.drift_policy`
  - `process.drift_tolerance`
  - `timing_model.speech.wpm` and `timing_model.speech.pause_ratio`
  - `timing_model.durations.segmental_ceiling`
  - `timing_model.durations.cvc_reference`
  - consonant subclasses `closure`, `fricative`, and `sonorant`
  - class-local `special_realization` anchors for hiatus and
    vowel-transition timing
  - subclass-local `perception_limits`
  - vowel-local `perception_limits`
  - explicit `timing_model.durations.pauses` min/max bands
- Integer millisecond representation is part of the contract for
  `phonetize.process.drift_tolerance` and all values under
  `phonetize.timing_model.durations`.
- Config emission must derive the `phonetize` section from that shared
  definition rather than duplicating the structure in multiple files.
- `confwriter` key validation, discovery, default emission, and help text must
  reuse the same canonical definition.
- `confwriter` must reject phonetize keys that are outside the approved schema
  before any write occurs.
- `phonetizer` must map direct CLI process flags to the canonical
  `phonetize.process.*` keys without inventing a second naming scheme.
- `fullprosmaker` must forward those same process controls with the required
  `--phonetize-` prefix rather than duplicating a second timing model.
- `phonetizer` and `fullprosmaker` must accept `phonetize.timing_model`
  overrides through `--t` / `--option path=value` using the full schema path.
- The phonetize stage must sit between prosody and metrics in the documented
  pipeline.
- The phonetizer output contract must define `<prefix>_phone.txt` as a
  line-oriented phoneme/silence artifact with millisecond durations and related
  metadata.
- Metrics temporarily retains hard-coded `wpm=193` and `pause_ratio=35`
  internally while the phonetize-driven contract is being introduced.
- The fixed long-pause-weight behavior removed by CR-033 remains outside the
  phonetize config surface.
- Subsequent config-aware work must preserve this exact schema skeleton unless
  a later approved internal record changes it explicitly.

Suggested transitional pipeline order:

- atfparse
- syllabify
- prosody
- phonetize
- metrics
- print

---

# Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`src/akkapros/cli/fullprosmaker.py`
`src/akkapros/lib/config.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/cli/confwriter.py`
`src/akkapros/config/default.yaml`
`docs/GETTING_STARTED.md`
`docs/akkapros/configuration.md`
`docs/akkapros/fullprosmaker.md`
`docs/akkapros/metricalc.md`
`docs/akkapros/phonetizer.md`
`README.md`
`tests/`

---

# Acceptance Criteria

- [x] Grouped config no longer defines top-level `metrics.wpm`.
- [x] Grouped config no longer defines top-level `metrics.pause_ratio`.
- [x] Grouped config defines the top-level `phonetize` section with the exact
      parameter set, comments, ordering, and defaults specified in this CR.
- [x] Grouped config emits `phonetize.process.geminate_policy=corrective`.
- [x] Grouped config emits
  `phonetize.process.accentuation_distribution_policy=85_15`.
- [x] Grouped config emits `phonetize.process.short_pause_policy=strict`.
- [x] Grouped config emits `phonetize.process.drift_policy=strict`.
- [x] Grouped config emits `phonetize.process.drift_tolerance=12`.
- [x] Grouped config emits `timing_model.durations.segmental_ceiling=310`.
- [x] Grouped config emits `timing_model.durations.cvc_reference=305`.
- [x] Grouped config emits
  `timing_model.durations.consonants.closure.special_realization.hiatus=18`
  and
  `timing_model.durations.consonants.sonorant.special_realization.vowel_transition=11`
  and keeps lexical `ʾ` classified under closures rather than either
  special-realization key.
- [x] The contract makes explicit that accentuated hiatus uses
  `timing_model.durations.consonants.closure.geminate` and accentuated
  vowel-transition uses
  `timing_model.durations.consonants.sonorant.geminate`, without changing
  the row identity established earlier in the pipeline.
- [x] Grouped config emits consonant subclasses `closure`, `fricative`, and
      `sonorant` with the exact onset, coda, geminate, and nested
      `perception_limits` values specified in this CR.
- [x] Grouped config emits
  `timing_model.durations.vowels.short=85`,
  `timing_model.durations.vowels.long=160`,
  `timing_model.durations.vowels.very_long=220`, and
  `timing_model.durations.vowels.perception_limits.{short_min,long_min,very_long_min,max}`
  with the exact values specified in this CR.
- [x] Grouped config emits `timing_model.durations.pauses.{short,long}.{min,max}`
  with the exact values specified in this CR.
- [x] Grouped config does not emit phonetize keys outside the approved schema
  defined in this CR.
- [x] Grouped config does not reintroduce `metrics.long_punct_weight`.
- [x] `confwriter` supports the revised nested phonetize YAML paths for
      `--list`, `--get`, `--set`, `--unset`, and `--set-default`.
- [x] `confwriter` rejects phonetize keys outside the approved schema without
  modifying the config file.
- [x] `confwriter` help/comments/examples stop referencing superseded draft
      phonetize keys.
- [x] `phonetizer` accepts process-option flags using hyphenated names such as
  `--geminate-policy` and `--drift-policy`.
- [x] `fullprosmaker` accepts the phonetizer-process pass-through flags using
  the required `--phonetize-` prefix such as `--phonetize-geminate-policy`.
- [x] `phonetizer` accepts `phonetize.timing_model` overrides through
  `--t path=value` and `--option path=value`.
- [x] `fullprosmaker` accepts the same `phonetize.timing_model` override model
  through `--t path=value` and `--option path=value`.
- [x] CLI help text, generated YAML comments, config docs, and stage docs that
      expose the phonetize section use the exact key names, comments, and
      defaults defined in this CR unless superseded explicitly.
- [x] The documented pipeline includes a `phonetizer` / `phonetize` stage
      between prosody and metrics.
- [x] The phonetizer stage writes `<prefix>_phone.txt`.
- [x] The `_phone` artifact contract is documented as one line per phoneme or
      silence with millisecond duration plus related metadata.
- [x] The `_phone` artifact contract states that row-neighborhood traversal may
  cross word boundaries and stops only at silence rows.
- [x] Metricalc is documented as currently planned to consume both `_tilde` and
      `_phone`.
- [x] Metrics temporarily hard-codes `wpm=193` and `pause_ratio=35`
      internally in this transition step.
- [x] Phonetize timing defaults and parameter definitions are grouped in one
      shared library location rather than duplicated across config, CLI, and
      runtime.
- [x] User-facing and developer-facing docs are updated for the new stage,
      revised config section, artifact contract, and temporary metrics
      behavior.
- [x] Built-in `run_tests()` coverage is updated in affected modules, and
  pytest coverage remains split between detailed unit checks and
  representative integration flows.
- [x] The documentation set is split and updated explicitly as
  `docs/akkapros/phonetizer.md` for stage/CLI/artifact contracts and
  `docs/akkapros/phonetizer-algorithm.md` for algorithm and timing-model
  behavior, with matching updates to confwriter/configuration docs and
  impacted program docs such as fullprosmaker.

---

# Risks / Edge Cases

Possible issues:

- stage-order changes may ripple into fullprosmaker orchestration and docs
- the `_phone` artifact contract may be underdocumented if metadata fields are
  described too loosely
- temporary hard-coded metrics values may be forgotten unless documented
  prominently
- config docs and examples may accidentally retain superseded draft keys
- `confwriter` key inventory may drift if the schema and help text are not
  generated from one canonical phonetize definition
- CLI docs may drift if the direct `phonetizer` flags and `fullprosmaker`
  pass-through flags are documented inconsistently
- `--option path=value` examples may drift if they omit the full phonetize path
- user-facing docs may confuse `perception_limits` with emitted durations or
  with pause-band values unless terminology is kept precise
- comments copied by hand into docs may diverge from canonical schema wording

---

# Testing Strategy

Built-in self-tests (`run_tests()`):

- add or extend detailed `run_tests()` coverage in affected modules for the
  phonetize schema, CLI flag resolution, `_phone` artifact contract, and
  temporary metrics behavior

Unit tests:

- default config emission contains the `phonetize` section with the exact
  nested structure, values, and comment/help metadata specified here
- flat `metrics.wpm` and `metrics.pause_ratio` are absent from emitted schema
- `long_punct_weight` remains absent from the config surface described by this
  CR
- emitted schema includes `segmental_ceiling`, `cvc_reference`, consonant
  subclass `special_realization`, consonant subclass `perception_limits`, and
  vowel `perception_limits`
- emitted schema includes `phonetize.process.geminate_policy`,
  `phonetize.process.accentuation_distribution_policy`,
  `phonetize.process.short_pause_policy`,
  `phonetize.process.drift_policy`, and
  `phonetize.process.drift_tolerance` with the exact inventories defined in
  this CR
- emitted schema/docs distinguish unstressed `special_realization` anchors from
  accentuated geminate timing for hiatus and vowel-transition rows
- emitted schema omits any phonetize keys outside the approved schema
- `confwriter` accepts representative nested phonetize keys for `--set`,
  `--get`, `--unset`, and `--set-default`
- `confwriter` accepts representative `phonetize.process` keys and rejects
  invalid policy values outside the contract inventories
- `confwriter` rejects phonetize keys removed from the approved schema
- `phonetizer` CLI resolution maps `--geminate-policy` and sibling process
  flags to the expected config keys
- `fullprosmaker` CLI resolution maps `--phonetize-geminate-policy` and
  sibling pass-through flags to the expected phonetizer process keys
- `phonetizer` and `fullprosmaker` accept representative
  `--option phonetize.timing_model...=...` overrides without schema drift
- metrics runtime behavior uses the temporary hard-coded `wpm` and
  `pause_ratio` values in this transition step

Integration tests:

- pipeline documentation/examples reflect the new phonetize stage position
- representative pipeline behavior includes generation of `<prefix>_phone.txt`
- config-driven flows can list and set representative revised phonetize paths
  without schema drift
- config-driven flows can override representative `phonetize.process` values
  through `phonetizer` direct flags and through `fullprosmaker` prefixed flags
- config-driven flows can override representative `phonetize.timing_model`
  values through `--t` / `--option path=value`
- metricalc transitional behavior is documented/tested against combined `_tilde`
  plus `_phone` planning assumptions where feasible for the stage contract
- `_phone` contract review confirms that row-neighborhood traversal is defined
  across word boundaries and stops only at silence rows

Manual review:

- inspect default config and config docs for the revised `phonetize` section
- inspect `confwriter --list phonetize` output and representative
  `--set-default` examples for the new key inventory
- inspect `phonetizer --help` and `fullprosmaker --help` for the required
  process-flag naming conventions and `--option` examples
- inspect user-facing and developer-facing docs for removal of superseded draft
  key names
- inspect pipeline diagrams or stage descriptions for the new phonetize step

---

# Rollback Plan

Restore the pre-phonetize pipeline ordering, restore the old flat metrics timing
config keys if needed, and remove the `_phone` artifact contract in one
coordinated change. Partial rollback is discouraged because it would leave the
pipeline, config schema, and docs inconsistent.

---

# Related Issues

- [ADR-039](../adr/039-replacement-of-timing-model.md)
- [REQ-024](../req/024-replacement-of-timing-model.md)
- [ADR-036](../adr/036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- [CR-034](034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md)
- [CR-033](033-remove-long-pause-weight-from-conf-and-cli-options.md)
- [ADR-010](../adr/010-metrics-from-text-and-dual-percent-v.md)

---

# Tasks

## Implementation

- [x] Add canonical shared library phonetize defaults and metadata for the
      revised schema in this CR
- [x] Add the new phonetizer/phonetize stage contract
- [x] Remove flat `metrics.wpm` and `metrics.pause_ratio` config keys
- [x] Emit the revised `phonetize` section in the canonical config
- [x] Add the `<prefix>_phone.txt` artifact contract
- [x] Keep metrics on temporary hard-coded `wpm` and `pause_ratio` until the
      new stage contract is fully operational
- [x] Update schema-driven `confwriter` behavior and examples for the revised
      nested phonetize keys
- [x] Update `phonetizer` process flags to the required hyphenated naming
      convention
- [x] Update `fullprosmaker` phonetizer pass-through flags to the required
      `--phonetize-` naming convention
- [x] Add `--t` / `--option path=value` handling for `phonetize.timing_model`
      overrides in `phonetizer` and `fullprosmaker`

## Tests

- [x] Add or extend detailed built-in `run_tests()` coverage in affected
  modules
- [x] Add pytest unit coverage for the revised phonetize config schema,
  temporary hard-coded metrics timing behavior, and representative
  `confwriter` phonetize YAML paths
- [x] Add pytest unit coverage for `phonetizer` process flags,
  `fullprosmaker` pass-through flags, and `--option` timing-model
  overrides
- [x] Add pytest integration coverage for the new stage position and `_phone`
  artifact

## Documentation

- [x] Create or update `docs/akkapros/phonetizer.md` as the detailed stage,
  CLI, and artifact-contract reference
- [x] Create or update `docs/akkapros/phonetizer-algorithm.md` as the detailed
  algorithm and timing-model reference distinct from the CLI/stage page
- [x] Create or update `docs/akkapros/confwriter.md` and
  `docs/akkapros/configuration.md` for the revised phonetize schema and
  config-edit surface
- [x] Update generated/default config comments so the exact phonetize skeleton
  is documented in the config file itself
- [x] Update impacted downstream program docs, including
  `docs/akkapros/fullprosmaker.md`, for stage ordering, pass-through flags,
  and `_phone` artifact expectations
- [x] Remove stale examples for superseded phonetize draft keys from all
  affected docs and CLI-help surfaces

## Review

- [x] Verify acceptance criteria

---

# Notes for CR-035

This CR introduces the new phonetize stage and revises the phonetize timing
schema to the current process-plus-reference model, but it does not finalize
the long-term metricalc input contract. The transition is explicitly temporary
where metrics still relies on hard-coded `wpm` and `pause_ratio`.

This CR also fixes the intended meaning of the special onset-marker anchors:
their `special_realization` values are baseline unstressed timings, while
accentuated hiatus and accentuated vowel-transition rows escalate to the
corresponding consonant-class geminate targets during Phase 2 without changing
their structural row identity.

This CR further adds five Phase 2 process controls under `phonetize.process`:

- one policy controlling whether same-consonant geminate pairs are normalized
  to the configured geminate target or left cumulative
- one constrained policy controlling the intended split of the added
  accentuation mora
- one short-pause discharge policy
- one drift recovery policy
- one explicit drift-tolerance value

Implementation is intentionally deferred. Later code changes must treat this CR
as the authoritative `phonetize` config skeleton until a newer approved
internal record supersedes it.