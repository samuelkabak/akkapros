---
cr_id: CR-066
status: 'Done'
priority: 'High'
impact: 'Mutative'
created: 2026-04-17
updated: 2026-04-17
implements: 'CR-050, CR-063'
---

# Change Request: Promote Mini Pauses to a Distinct Phone-Row Contract

# Summary

The phonetizer already inserts algorithmic mini pauses, but it currently serializes them with the same label, realization, and pause subtype used for ordinary short punctuation-owned pauses. That makes mini pauses indistinguishable from inner punctuation at the phone-row contract level unless a downstream reader inspects the free-text field. This CR introduces a dedicated mini-pause row contract so inserted prosodic-space rows are first-class entities in runtime tables, public documentation, tests, and generated demo artifacts.

---

# Motivation

Why is this change needed?

- Bug fix
- Contract clarification
- Documentation correction

The current runtime emits mini pauses as rows such as `SES|S|I|S|S|N|P|SP|0132|+000|M0C|:mini-pause:`. That row shape conflates three different things that should remain distinct: punctuation-owned short pauses, algorithmically inserted prosodic-space pauses, and their visible source token. Public docs currently mirror the same conflation, so the mismatch is not only descriptive; it is part of the active emitted contract.

---

# Scope

## Included

- Define a dedicated canonical mini-pause label `MEN`
- Define a dedicated canonical mini-pause type code `M`
- Define a dedicated canonical mini-pause realization code `MP`
- Define the canonical mini-pause text field as one literal ASCII space character
- Update phonetizer-owned inventories, examples, and validation rules so inserted mini pauses emit the dedicated contract
- Update public phonetizer documentation so ordinary pauses and mini pauses are documented separately
- Update tests and demo/reference artifacts that currently assert or snapshot the old mini-pause contract

## Not Included

- Retuning the mini-pause insertion algorithm or beat-folding math
- Changing punctuation precedence `Q > E > S > C > I` for punctuation-owned pauses
- Redesigning the twelve-field phone-row layout
- Reworking MBROLA pause export beyond whatever mapping is needed to carry the new `MP` realization code

---

# Current Behavior

The current system already creates mini-pause rows during Phase 2 when drift can be discharged by an in-band inserted pause. However, those rows are emitted through the ordinary short-pause path.

Observed repository evidence:

- [src/akkapros/lib/phonetize.py](src/akkapros/lib/phonetize.py) defines `MINI_PAUSE_TEXT = ':mini-pause:'`
- [src/akkapros/lib/phonetize.py](src/akkapros/lib/phonetize.py) currently maps only `SES -> SP` and `ZEN -> ZP` in the inspected input-to-realization tables
- [src/akkapros/lib/phonetize.py](src/akkapros/lib/phonetize.py) currently builds inserted mini pauses through `_new_pause_row(..., pause_type='I', length_code='S')`
- [docs/akkapros/phonetizer-phone-file-guide.md](docs/akkapros/phonetizer-phone-file-guide.md) documents only `SES` and `ZEN` labels and only `SP` and `ZP` pause realizations
- [demo/akkapros/lexlinks/results/erra_construct_phone.txt](demo/akkapros/lexlinks/results/erra_construct_phone.txt) contains emitted mini-pause rows such as `SES|S|I|S|S|N|P|SP|0132|+000|M0C|:mini-pause:`
- [tests/test_phonetize_lib.py](tests/test_phonetize_lib.py) currently asserts `SES` and `SP` for inserted pause rows

In practice, this means downstream readers cannot distinguish a punctuation-owned short pause from an inserted prosodic-space pause by inspecting the canonical row identity fields alone.

---

# Proposed Change

Define mini pauses as a distinct phone-row kind with their own stable identity:

- `label = MEN`
- `category = S`
- `type = M`
- `length = S`
- `position = S`
- `accent = P`
- `realization = MP`
- `text = ' '` (one literal ASCII space character)

Ordinary punctuation-owned pauses remain unchanged:

- inner punctuation continues to use `SES ... SP`
- phrasal or line-final punctuation continues to use `ZEN ... ZP`
- punctuation-owned pause types continue to use `Q`, `E`, `S`, `C`, or `I`

Under the new contract, the earlier observed row:

`SES|S|I|S|S|N|P|SP|0132|+000|M0C|:mini-pause:`

must instead serialize as:

`MEN|S|M|S|S|N|P|MP|0132|+000|M0C| `

The final field above is one actual space character. It is not a sentinel word,
placeholder token, or colon-delimited mnemonic.

This CR intentionally changes row identity, not timing behavior. A mini pause remains an algorithmically inserted short-band silence used to discharge drift where permitted by the live solver.

This CR also requires one dedicated public reference page,
`docs/akkapros/phonetizer-data-model.md`, that centralizes the live phonetizer
data model, canonical tables, row format, and the parsing and structural
constraints that downstream readers must preserve.

---

# Technical Design

Explain how it should be implemented.

Architecture notes:

Components:
- phonetizer runtime row inventory
- phone-row validators and parsers
- public phonetizer docs
- regression/demo artifacts and tests

Storage:
- no new persistent storage
- generated phone-row artifacts adopt the new canonical mini-pause row shape

API changes:
- emitted `_phone.txt` and `_ophone.txt` rows gain a third silence identity for inserted prosodic-space pauses
- downstream readers must accept `MEN`, `M`, `MP`, and a single-space `text` field as canonical mini-pause values

Implementation shape:

- Add a dedicated mini-pause source/inventory row instead of reusing the short-pause inventory
- Route inserted mini pauses through a dedicated constructor that does not alias ordinary short punctuation rows
- Teach realization metadata and export mapping about `MP`
- Update docs and examples so pause inventories distinguish ordinary short pause, long pause, and mini pause
- Add a dedicated public data-model reference page that centralizes the live
	row contract, canonical inventories, serialization format, and parsing
	constraints for `_phone.txt` and `_ophone.txt`
- Update tests and generated demo/reference outputs that currently lock in the old `SES|...|SP|...|:mini-pause:` form

Compatibility rule:

- Newly emitted artifacts must use the new mini-pause contract
- Reader-side acceptance of legacy `:mini-pause:` or `SES ... SP` mini-pause rows is an implementation choice, but emitted artifacts, public docs, and refreshed references must converge on the new canonical form with a one-space text field

---

# Files Likely Affected

docs/akkapros/phonetizer-phone-file-guide.md
docs/akkapros/phonetizer-algorithm.md
docs/akkapros/phonetizer.md
docs/akkapros/phonetizer-data-model.md
src/akkapros/lib/phonetize.py
tests/test_phonetize_lib.py
tests/test_format_validation.py
tests/test_integration.py
tests/test_print_merger.py
demo/akkapros/lexlinks/results/erra_construct_phone.txt

---

# Acceptance Criteria

- [x] Inserted mini pauses emit `MEN` as the label instead of `SES`
- [x] Inserted mini pauses emit `M` as the pause type instead of `I`
- [x] Inserted mini pauses emit `MP` as the realization code instead of `SP`
- [x] Inserted mini pauses emit one literal space character in `text` instead of `:mini-pause:`
- [x] Ordinary punctuation-owned pauses continue to use `SES` or `ZEN`, `SP` or `ZP`, and the existing punctuation pause-type set `Q/E/S/C/I`
- [x] Public phonetizer docs clearly distinguish ordinary short pauses, long pauses, and inserted mini pauses
- [x] Public phonetizer docs include `docs/akkapros/phonetizer-data-model.md`
	as the centralized reference for the live phonetizer data model, canonical
	tables, row format, and key parsing and structural constraints
- [x] Test coverage is updated so runtime tables, validators, and integration outputs assert the new canonical mini-pause contract
- [x] Refreshed demo or reference phone artifacts show mini pauses with the new canonical row identity
- [x] No acceptance test for this CR depends on changing mini-pause timing eligibility or duration math

---

# Risks / Edge Cases

Possible issues:

- Downstream validators may currently hard-code `SP` and `ZP` as the only silence realization codes
- Demo and integration snapshots may fail broadly because the mini-pause row identity changes in emitted artifacts
- Printer, metrics, or `.pho` export may accidentally treat `MP` as an unknown realization unless silence handling is centralized
- Reader-side backward compatibility for legacy demo artifacts may need an explicit decision during implementation

---

# Testing Strategy

Unit tests:

- inventory metadata exposes `MEN`, `M`, `MP`, and a one-space mini-pause text payload
- inserted mini-pause builders emit the dedicated mini-pause contract
- ordinary punctuation-owned short and long pauses preserve their current contract

Integration tests:

- phone-row pipelines emit `MEN|S|M|S|S|N|P|MP|...| ` where mini pauses are inserted
- downstream readers continue to process phone rows containing `MP`

Manual tests:

- inspect the refreshed lexlinks demo phone file and confirm mini pauses are no longer serialized as `SES ... SP ... :mini-pause:`
- inspect representative emitted rows and confirm the final `text` field for `MP` is exactly one space character
- compare one ordinary short punctuation pause and one inserted mini pause to confirm they remain visually and structurally distinct
- inspect `docs/akkapros/phonetizer-data-model.md` and confirm that the live
	row schema, canonical tables, output format, and parsing constraints are
	consolidated in one place

---

# Rollback Plan

Explain how to revert if needed.

Revert the dedicated mini-pause inventory entries and restore aliasing to the ordinary short-pause contract. Refresh docs, tests, and demo artifacts back to the previous serialization form.

---

# Related Issues

CR-050
CR-063

---

# Tasks

## Implementation

- [x] Introduce the dedicated mini-pause inventory entries and row constructor path
- [x] Update downstream silence handling to recognize `MP`
- [x] Refresh demo or reference artifacts that currently serialize mini pauses with the old contract

## Tests

- [x] Update unit tests for inventory tables and pause-row builders
- [x] Update integration coverage for emitted phone-row examples

## Documentation

- [x] Update public phonetizer docs to document the distinct mini-pause contract
- [x] Create `docs/akkapros/phonetizer-data-model.md` as the centralized
	public reference for the live phonetizer data model and row contract
- [x] Update examples that still show `:mini-pause:` or `SES ... SP` for inserted mini pauses

## Review

- [x] Verify emitted artifacts distinguish punctuation-owned pauses from inserted mini pauses without inspecting free text heuristically
- [x] Verify acceptance criteria


---

# Implementation Blockers

Leave the section empty if no blockers are known.

---

# Notes

Evidence gathered for this CR came from repository inspection rather than from source changes. In particular, the current runtime, public docs, tests, and demo artifact all converge on the old serialization of mini pauses as ordinary short pauses, which confirms that implementation must be coordinated across code, docs, and reference outputs rather than treated as a docs-only correction.