---
req_id: REQ-050
status: Implemented
priority: Medium
impact: Additive
created: 2026-05-09
updated: 2026-05-09
related_adrs: ''
implemented_by: 'CR-101'
---

# Requirement: Ultraheavy Marker Phone and MBROLA Output

## Summary

The phonetizer must support an experimental configurable option to expand
circumflex vowels (`â`, `ê`, `î`, `û`) from a single long-vowel segment into
three segments (vowel + transition + vowel) in dedicated output files
(`<prefix>_yphone.txt` and `<prefix>_ymbrola.pho`), produced alongside the
standard `<prefix>_phone.txt` and `<prefix>_mbrola.pho`.

This feature is experimental and must be gated behind
`phonetize.process.allow_experimental = true`.

## Motivation

- The printer's `--circ-hiatus` option splits circumflex vowels into hiatus
  in IPA output only, without affecting the phone-row timing model, MBROLA
  export, or metrics computation
- Researchers need a phonetizer-level expansion that produces independent
  phone and MBROLA artifacts with proper timing (vowel + transition + vowel)
  and intonation propagation
- The feature is experimental and must be gated behind
  `phonetize.process.allow_experimental = true`

## Requirements

### REQ-050-01: Config key

The phonetizer must support a config key
`phonetize.process.realization.ultraheavy_hiatus_enable` (bool, default false).

### REQ-050-02: Experimental guard

Setting `ultraheavy_hiatus_enable = true` without `allow_experimental = true`
must raise a verification error.

### REQ-050-03: Output files

When `ultraheavy_hiatus_enable = true`, the phonetizer must produce:

- `<prefix>_yphone.txt` (expanded phone rows)
- `<prefix>_yophone.txt` (expanded original phone rows)
- `<prefix>_ymbrola.pho` (expanded MBROLA output)
- `<prefix>_yombrola.pho` (expanded original MBROLA output)

alongside the standard `<prefix>_phone.txt`, `<prefix>_ophone.txt`,
`<prefix>_mbrola.pho`, and `<prefix>_ombrola.pho`.

### REQ-050-04: Expansion logic

Each circumflex vowel row (labels `AWI`, `EWI`, `IWI`, `UWI`) must be expanded
into three rows:

1. First vowel segment (same label, category V, length S, same boundary,
   same accent, same realization, duration U1 = floor(0.5 * (Z - T)))
2. Transition segment (label ENA, category C, type T, length S, boundary I,
   accent F, realization from mapping table, duration T = vowel_transition)
3. Second vowel segment (same label, category V, length S, same boundary,
   accent F, same realization, duration U2 = ceiling(0.5 * (Z - T)))

### REQ-050-05: Transition realization mapping

| Original realization | Transition realization |
|---|---|
| `AA`, `AO` | `AL` |
| `UU`, `UO` | `WA` |
| `EE`, `II`, `EO`, `IO` | `YI` |

### REQ-050-06: Timing formula

Z = original duration in ms
T = vowel_transition (from config, default 25 ms)
U1 = floor(0.5 * (Z - T))
U2 = ceiling(0.5 * (Z - T))

If Z - T <= 0, the expansion must not be applied (original row kept as-is).

### REQ-050-07: Intonation preservation

The original intonation contour must be preserved across the three segments:

- Row 1: linear rise from F1 to mid_freq over U1 ms
- Row 2: constant mid_freq over T ms
- Row 3: linear rise from mid_freq to F2 over U2 ms

Where mid_freq = F1 + (F2 - F1) * (U1 / Z), with floor/ceiling to avoid
decimal frequencies.

### REQ-050-08: Front matter propagation

The `_yphone.txt` and `_ymbrola.pho` files must include
`ultraheavy_hiatus_enable: true` in their front matter.

### REQ-050-09: Standard output unchanged

The standard `<prefix>_phone.txt` and `<prefix>_mbrola.pho` must be unchanged
when `ultraheavy_hiatus_enable = true`.

### REQ-050-10: No y-files when disabled

When `ultraheavy_hiatus_enable = false` (default), no `_y*` files must be
produced.

### REQ-050-11: Edge cases

- Zero or negative split (Z <= T): expansion not applied
- Accentuated circumflex vowels: accent preserved on first segment
- Emphatic coloring: emphatic realizations preserved in both vowel segments
- Boundary codes: last segment inherits original boundary; internal boundaries are I
- Text field: only first segment carries original text
- Drift field: original drift assigned to first segment; transition and second
  segment get neutral drift
- Pause rows: unaffected
- Resync pause rows: unaffected

## Acceptance Criteria

- [x] Config key exists and defaults to false
- [x] Experimental guard works
- [x] Output files produced when enabled
- [x] Expansion logic correct
- [x] Transition mapping correct
- [x] Timing formula correct
- [x] Intonation preserved
- [x] Front matter propagated
- [x] Standard output unchanged
- [x] No y-files when disabled
- [x] Edge cases handled
- [x] Unit tests pass
- [x] Integration tests pass

## Implementation

Implemented by CR-101.
