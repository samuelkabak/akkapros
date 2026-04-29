---
req_id: REQ-048
status: Implemented
priority: High
impact: Mutative
created: 2026-04-28
updated: 2026-04-29
related_adrs: 'ADR-034'
implemented_by: 'CR-093'
---

# Requirement: Configurable Mono-Mode Accentuation Lengthening

## Summary

Introduce a new configurable parameter `mono_mode_accentuation_lengthening` under `phonetize.process.timing_model.durations` that controls the additional duration (in ms) attributed to accentuated syllables in mono mora mode. Unlike bi mode — where accentuation adds one full mora (`0.5 * cvc_reference`) and forces prosodic units to multiples of two morae — mono mode uses a smaller, configurable elongation whose value is set by this parameter.

The parameter is scalable with `scale` like all other duration values. Its default is 50 ms, with validation range `[0, round(0.5 * cvc_reference)]` using a dynamic maximum computed from the configured `cvc_reference`.

The additional duration is distributed using the same `accentuation_distribution_policy` as bi mode.

---

## Motivation

The `0.5 * cvc_reference` elongation is a bimoraic concept: it adds one mora's worth of duration to accentuated syllables to balance mora parity. In mono mode, the prosody layer does not use bimoraic parity gating (`CR-027`), so adding the full bimoraic elongation in the phonetizer produces timing that is inconsistent with the mono prosody model.

However, completely skipping accentuation elongation is too rigid. A smaller, configurable elongation (default 50 ms) is appropriate for mono mode, giving researchers control over the mono-mode accentuation timing.

The `~` marker's role in mono mode is primarily intonational (pitch contour), with a configurable durational component. The synchronization basis change (half-beat for mono) was already implemented by `CR-080` and is not affected by this requirement.

---

## Acceptance Criteria

- [ ] Given mono-mode input (`metadata.options.mora_mode: mono` in frontmatter) with accentuated syllables, when `realize_phone_rows()` processes them, then `mono_mode_accentuation_lengthening` ms is applied (distributed via `accentuation_distribution_policy`) instead of `0.5 * cvc_reference`.
- [ ] Given mono-mode input with accentuated syllables, when `realize_row_intonation()` processes them, then the `stress` intonation token is still assigned to accentuated syllables.
- [ ] Given bi-mode input with accentuated syllables, when `realize_phone_rows()` processes them, then the `0.5 * cvc_reference` elongation is applied exactly as before.
- [ ] Given mono-mode input without accentuated syllables, when `realize_phone_rows()` processes them, then behavior is unchanged.
- [ ] Given any mode, when `realize_row_intonation()` processes rows, then intonation assignment is unchanged.
- [ ] The `mono_mode_accentuation_lengthening` parameter defaults to 50 ms and validates within `[0, round(0.5 * cvc_reference)]`.
- [ ] The `accentuation_distribution_policy` config description clarifies it applies in both modes.
- [ ] Existing bi-mode tests pass without modification.
- [ ] New tests pin mono-mode accentuation timing with the configurable elongation.

---

## User Story (optional)

> As a researcher using mono-mode prosody, I want the phonetizer to apply a configurable accentuation elongation to accentuated syllables in mono mode, so that I can control the timing behavior independently of the bimoraic model.

---

## Interface Notes

- Input: `_tilde.txt` with frontmatter containing `metadata.options.mora_mode: mono` or `metadata.options.mora_mode: bi`.
- New config parameter: `phonetize.process.timing_model.durations.mono_mode_accentuation_lengthening` (int, default 50, range [0, round(0.5 * cvc_reference)]).
- Affected components:
  - `src/akkapros/lib/_phonetize_config.py` — schema, validation, config description
  - `src/akkapros/lib/phonetize.py` — `realize_phone_rows()`, `_shape_reference()`
  - `src/akkapros/lib/helpmsg.py` — help text
  - `tests/test_phonetize_lib.py` — updated mono-mode tests
  - `tests/test_integration.py` — updated mono-mode integration tests
  - `tests/integration_refs/` — updated mono-mode reference files

---

## Open Questions

- [ ] None.

---

## Implementation Notes (optional)

- Owner: TBD
- Estimated effort: small
- The `_resolve_mora_mode()` function already exists in `_phonetize_config.py` and is imported in `phonetize.py`. No new frontmatter parsing is needed.
- The primary change is in `realize_phone_rows()` around lines 1474-1486 of `phonetize.py`: apply `mono_mode_accentuation_lengthening` instead of `0.5 * cvc_reference` in mono mode.
- `_shape_reference()` should also accept a `mono_lengthening` parameter for consistency.
- `realize_row_intonation()` needs no changes — it already assigns intonation based on the `accent` field independently of mode.
- Migration: none. Mono-mode inputs already carry `mora_mode` in frontmatter from `CR-027`. Bi-mode is the default and is unchanged.

---

## Related

- Related ADRs: [ADR-034](../adr/034-prosody-mora-modes-and-explicit-link-locking.md)
- Related REQs: [REQ-019](019-prosody-mora-mode-selection.md)
- Implementation CRs: [CR-093](../cr/093-skip-accent-elongation-in-mono-mode.md)
- Related CRs: [CR-027](../cr/027-add-prosody-mora-mode-selection.md), [CR-080](../cr/080-add-mora-mode-aware-beat-alignment-and-relax-original-ophone-timing.md)

---

## Non-Goals

- This requirement does not change the synchronization basis logic from `CR-080`.
- This requirement does not change how `realize_row_intonation()` works.
- This requirement does not change bi-mode behavior in any way.
- This requirement does not change the prosody layer's accentuation logic.
- This requirement does not remove the `accentuation_distribution_policy` config option.

---

## Security / Safety Considerations

- Mono-mode input generated by an older version of the prosody layer (before `CR-027`) may not have `mora_mode` in frontmatter. The `_resolve_mora_mode()` function falls back to `'bi'` in this case, so no behavioral change occurs for legacy inputs. This is safe and backward-compatible.
- If `mono_mode_accentuation_lengthening` is set to 0, mono mode behaves as in the previous CR-093 (no elongation).
