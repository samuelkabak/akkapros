---
cr_id: CR-062
status: Done
priority: High
impact: Mutative
created: 2026-04-15
updated: 2026-04-15
implements: ''
---

# Change Request: Unify phone/ophone row separator and adopt signed numeric drift token

## Summary

Unify the field separator used in `<prefix>_phone.txt` and `<prefix>_ophone.txt` rows to the pipe character (`|`) and change the serialized per-row `drift` token to a fixed-width signed numeric token (examples: `-012`, `+000`, `+054`). This CR defines the new row grammar, the drift numeric-sign semantics, and the required producer/consumer updates across the pipeline.

## Motivation

- Consistent delimiter semantics simplifies parsing and reduces accidental field-splitting bugs (today rows use `-` and `:` in different places).
- A single visible delimiter (`|`) is easier to target with lightweight shell tools and programmatic split-with-maxsplit logic.
- Replacing `A/B/O`-style drift labels with an arithmetic sign makes the drift token immediately human- and machine-readable and consistent with numeric diagnostics elsewhere.

## Scope

### Included

- Phonetizer row emission format: change to pipe-separated fields.
- Row-level `drift` token format: sign + three-digit zero-padded milliseconds (always include `+` or `-`).
- Update pipeline consumers to accept the new format.
- Documentation, demo artifacts, and unit/integration tests that assert phone/ophone row shape.

### Not included

- Changing any other file formats (for example `.pho`) unless explicitly called out by implementers.
- External tools outside this repository that consume the phone-row files (those will need coordination separately).

## Current Behavior

Phone/ophone row files are fixed-width-ish, human-readable single-line records where the structural fields are separated by `-` and the structural payload is separated from the textual tail by `:`. Example current row:

```
SUD-C-F-S-O-N-F-SU-0137-O000-M0C:ṣ
```

The row-level `drift` token is 4 characters and uses letters: `O000` (on the beat), `Axyz` (stream ahead by `xyz` ms), `Bxyz` (stream behind by `xyz` ms). The structural separators are not uniform across emitters and consumers.

## Proposed Change

1. Row separator: emit all fields separated by `|` and use a single final `|` before the text tail. The canonical field order becomes (12 fields):

```
label|category|type|length|position|boundary|accent|realization|duration|drift|intonation|text
```

2. Drift token: replace letter-prefixed token with a signed numeric token having exactly four characters: a sign (`+` or `-`) followed by three zero-padded digits. Examples:

- `+000` — on the beat (zero)
- `-034` — 34 ms ahead of the beat (stream leads)
- `+125` — 125 ms behind the beat (stream lags)

Semantic mapping note: the numeric sign follows ordinary arithmetic: negative = stream ahead of beat (same semantic direction as prior `A`), positive = stream behind the beat (prior `B`). Implementers must preserve this sign convention so downstream summaries continue to mean the same thing.

3. Parser guidance: consumers MUST parse robustly using a bounded split to preserve the free-form text tail. Example Python parsing idiom:

```python
parts = line.rstrip('\n').split('|', 11)  # yields 12 elements: last is the text tail
```

4. Compatibility

This change is intentionally breaking. Producers MUST emit and consumers MUST accept the new pipe-separated format with signed numeric `drift` tokens. No legacy parser compatibility mode is required.

5. Emission policy: the `phonetizer` (row writer) MUST emit the pipe-separated form once this CR is implemented.

6. Tests & docs: update all examples, demo outputs in `demo/akkapros/…`, and unit/integration tests that assert phone-row shape and drift summary values.

## Technical Design

### Components to change (likely affected files)

- `src/akkapros/lib/phonetize.py` — row emitter and row-building logic
- `src/akkapros/cli/phonetizer.py` — CLI wrapper that writes outputs and self-tests
- `src/akkapros/cli/fullprosmaker.py` — pipeline runner that triggers phonetizer outputs
- `src/akkapros/cli/metricalc.py` — metrics CLI that consumes `*_phone.txt`
- `src/akkapros/cli/printer.py` and `src/akkapros/lib/print.py` — printer that consumes row files
- `src/akkapros/lib/metrics.py` (or `src/akkapros/cli/metricalc.py`) — row loader/parser used by metrics
- `tests/test_phonetize_lib.py`, `tests/test_metrics_stats.py`, and other tests referencing phone-row examples
- Documentation: `docs/akkapros/phonetizer-phone-file-guide.md`, `docs/akkapros/phonetizer.md`, `docs/akkapros/phonetizer-algorithm.md`, and any demo outputs under `demo/` and `outputs/` used as examples.

### Parser implementation notes

- Use a single splitting pass with `maxsplit=11` to preserve the tail.
- Validate numeric `duration` and signed `drift` syntactically (duration four digits, drift `[+-]\d{3}`).
- Implement a small helper `parse_phone_row(line)` that returns a canonical dict for the new pipe-separated shape.

### Emission notes

- When writing rows, join fields with `|` in the order specified and format `drift` using the new signed token generator.
- Ensure demo and example files in `demo/` are regenerated as part of the change PR.

## Files Likely Affected

`src/akkapros/lib/phonetize.py`  
`src/akkapros/cli/phonetizer.py`  
`src/akkapros/cli/fullprosmaker.py`  
`src/akkapros/cli/metricalc.py`  
`src/akkapros/cli/printer.py`  
`src/akkapros/lib/print.py`  
`src/akkapros/lib/metrics.py`  
`docs/akkapros/phonetizer-phone-file-guide.md`  
`docs/akkapros/phonetizer.md`  
`docs/akkapros/phonetizer-algorithm.md`  
`tests/test_phonetize_lib.py`  
`tests/test_metrics_stats.py`  

## Acceptance Criteria

- [x] Phonetizer emits `|`-separated rows using the specified 12-field order.
- [x] Phonetizer emits `drift` tokens in the signed `[+-]DDD` format (zero as `+000`).
- [x] A single parsing helper `parse_phone_row` exists for the new format.
- [x] `metricalc`, `printer`, and other consumers read the canonical row dict returned by the helper without breaking.
- [x] Unit and integration tests cover new format parsing and emission.
- [x] Documentation and demo artifacts updated to show the new canonical format.
- [x] Release notes mark this as a breaking interface change.

## Risks / Edge Cases

- Text tail can include `|` characters; therefore all parsers must use bounded split (`maxsplit`) to avoid over-splitting.
- External third-party consumers will need updates.
- Some ad-hoc shell scripts or analysis pipelines may break if they relied on `-` splitting; update instructions should include recommended `awk`/`cut` patterns using `|`.

## Testing Strategy

Unit tests:

- `parse_phone_row` with new rows (12 fields); ensure canonical dict output.
- Emission test: `phonetize` internal writer emits a pipe-delimited line for known input.

Integration tests:

- Regenerate `demo/` artifacts and ensure `metricalc` table and JSON output values are unchanged except for string shape.

Manual tests:

- Run `phonetizer` to write outputs, then run `metricalc` and `printer` against those outputs.

## Rollback Plan

- If downstream consumers break, revert the writer/parser changes and restore the previous row contract in one patch set.

## Tasks

### Implementation

- [x] Implement `parse_phone_row` helper and centralize parsing.
- [x] Update phonetizer row writer to emit `|` and signed drift token.
- [x] Update consumers to use `parse_phone_row`.
- [x] Regenerate demo outputs and documentation.

### Tests

- [x] Add unit tests for new-format parse acceptance.
- [x] Update existing phone-row fixtures to new format.

### Documentation

- [x] Update `phonetizer-phone-file-guide.md` with examples and migration notes.
- [x] Add a short migration note in `CHANGELOG.md` or release notes.

## Implementation Blockers

None identified at spec stage.

## Notes / Open Questions

- Conversion utility: none required; demo files should be regenerated from canonical `_tilde` sources.
- No backward-compatibility requirement for legacy row parsing.

Implementation completed on 2026-04-15 with full-suite verification passing.

---

Implementation is deferred to the code-change PR(s). This CR only defines the contract, acceptance criteria, and migration plan.
