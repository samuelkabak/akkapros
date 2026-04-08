# Phonetizer Algorithm

This document describes the currently implemented CR-035 phonetize-stage contract.

## Current Scope

The live implementation is intentionally transitional.

It provides:
- one canonical `phonetize` config section
- one executable `phonetizer` CLI
- one materialized `<prefix>_phone.txt` artifact
- one shared library module, `src/akkapros/lib/phonetize.py`

It does not yet implement the later full Phase 1 and Phase 2 phonetizer contracts from the downstream phonetizer records.

## Row Model

The current `_phone.txt` body is newline-delimited JSON.

Each row is either:
- `phoneme`
- `silence`

Representative row fields:
- `symbol`
- `duration_ms`
- `line_index`
- `word_index`
- `syllable_index`
- `accentuated`
- `boundary_after`
- `segment_class`
- `source_marker`

## Duration Source

Durations are read from `phonetize.timing_model`.

Examples:
- vowels use `phonetize.timing_model.durations.vowels.*`
- consonants use class-specific onset or coda defaults under `phonetize.timing_model.durations.consonants.*`
- silence rows use `phonetize.timing_model.durations.pauses.short.min` or `.long.min`

## Boundary Behavior

The current stage:
- marks word boundaries on the preceding phoneme row
- increments syllable indices at `.` and `-`
- emits silence rows for configured short and long pause punctuation
- emits a long-pause silence row for line breaks
- preserves merged-word traversal without inserting ordinary word-space silence rows

## Transition Note

`metricalc` still computes from `_tilde.txt` rather than consuming `_phone.txt` directly.
During this transition it uses the phonetize defaults internally:
- `wpm = 193`
- `pause_ratio = 35`

That is an implementation bridge, not the final phonetize-to-metrics contract.
