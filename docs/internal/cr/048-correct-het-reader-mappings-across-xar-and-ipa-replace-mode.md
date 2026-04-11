---
cr_id: CR-048
status: Draft
priority: Medium
impact: Mutative
created: 2026-04-11
updated: 2026-04-11
implements: 'ADR-019, ADR-021, ADR-022, REQ-005'
---

# Change Request: Correct ḥ Reader Mappings Across XAR and IPA Replace Mode

# Summary

Correct the repository's reader-facing treatment of `ḥ` in two printer
surfaces:

- XAR: change `ḥ` from `ḫ` to `'`, aligning it with the existing XAR treatment
  of `ʿ` and `ʾ`
- IPA `replace` mode: change `ḥ` from `χ` to `ʔ`, aligning it with the existing
  `replace`-mode treatment of `ʿ` and `ʾ`

This CR therefore corrects the same underlying mistake in both practical
orthography and IPA-replacement policy. In XAR, `ḥ`, `ʿ`, and `ʾ` converge to
apostrophe. In IPA `replace` mode, `ḥ`, `ʿ`, and `ʾ` converge to `ʔ`, while `ḫ`
alone remains `χ`.

The CR also requires tests, inline comments, help text, and user-facing
documentation to be updated together, and it explicitly preserves the current
rule that automatic vowel coloring does not infer any `ḥ`-conditioned vowel
shift. If a reader wants `a` to surface as `e` near `ḥ`, that vowel quality
must already be present in the input text.

---

# Motivation

The repository currently exposes the same underlying classification error in two
places.

- XAR documents and implements `ḥ -> ḫ`, while `ʿ` and `ʾ` already map to `'`.
- IPA `replace` mode documents and implements `ḥ -> χ`, collapsing `ḥ` with
  `ḫ`, while `ʿ` and `ʾ` already converge to `ʔ`.

The requested policy is that `ḥ` should not share the `ḫ` outcome in either of
those reader-facing replacement systems. Instead:

- XAR should treat `ḥ` the same as `ʿ` and `ʾ`
- IPA `replace` mode should also treat `ḥ` the same as `ʿ` and `ʾ`

This is a contract-sensitive output change because both XAR and IPA are public
printer surfaces with explicit examples in code, tests, docs, and CLI help. The
change therefore needs one coordinated record that updates the rendering
contract, the assertions that encode it, and the explanatory notes around what
the printer does not do automatically.

It is also important to avoid silently implying a second change that is not
requested. The current printer only applies automatic colored-vowel logic to
vowels adjacent to `q`, `ṣ`, and `ṭ`. This CR does not expand that inference to
`ḥ`. Any `ḥ`-conditioned vowel quality, including an `a` to `e` shift in the
source transliteration, remains input-owned rather than printer-inferred.

---

# Scope

## Included

- Change XAR consonant rendering so `ḥ` maps to `'` instead of `ḫ`.
- Preserve the existing XAR mapping of `ʿ` and `ʾ` to `'`.
- Change IPA `replace` mode so `ḥ` maps to `ʔ` instead of `χ`.
- Preserve IPA `replace` mode behavior where `ʿ` and `ʾ` map to `ʔ`.
- Preserve IPA behavior where `ḫ` remains `χ`.
- Make both convergences explicit in code comments, docstrings, CLI help, and
  user-facing documentation.
- Update the printer self-tests and any affected integration or example-based
  tests that currently encode `ḥ -> ḫ` in XAR output or `ḥ -> χ` in IPA
  `replace` output.
- Update user-facing XAR documentation to explain that `ḥ`, `ʿ`, and `ʾ`
  all surface as apostrophe in XAR.
- Update user-facing IPA documentation to explain that `replace` mode maps
  `ḥ`, `ʿ`, and `ʾ` to `ʔ`, while `ḫ` remains `χ`.
- Document explicitly that automatic vowel coloring remains limited to the
  current emphatic-coloring set and does not infer vowel quality changes next
  to `ḥ`.
- Document explicitly that if a user wants a `ḥ`-conditioned vowel quality
  such as `a -> e`, that vowel must already be present in the input text.

## Not Included

- Changing MBROLA mappings for `ḥ`, `ʿ`, or `ʾ`.
- Changing IPA `preserve` mode, which continues to distinguish `ḥ -> ħ`,
  `ḫ -> χ`, `ʿ -> ʕ`, and `ʾ -> ʔ`.
- Adding new automatic vowel-coloring or vowel-normalization logic for `ḥ`.
- Reopening the broader XAR vowel system beyond the clarification above.
- Reopening the broader IPA vowel-coloring system beyond the clarification
  above.

---

# Current Behavior

Repository state on 2026-04-11 shows the following active behavior.

- `src/akkapros/lib/print.py` currently defines XAR consonant mappings with
  `ḥ -> ḫ`, `ḫ -> ḫ`, `ʿ -> '`, and `ʾ -> '`.
- `src/akkapros/lib/print.py` currently defines IPA `replace` mappings with
  `ḥ -> χ`, `ḫ -> χ`, `ʿ -> ʔ`, and `ʾ -> ʔ`.
- The printer self-tests in `src/akkapros/lib/print.py` currently assert XAR
  examples such as `ḥa -> ḫa`, `ʿa -> 'a`, and `ʾa -> 'a`.
- The printer self-tests in `src/akkapros/lib/print.py` currently assert IPA
  `replace` examples such as `ḫa -> χa` and `ḥa -> χa`.
- `docs/akkapros/xar-script.md` currently documents `ḥ -> ḫ`, `ḫ -> ḫ`,
  `ʿ -> '`, and `ʾ -> '` as the public XAR consonant table.
- `docs/akkapros/prosody-realization-algorithm.md` currently documents IPA
  `replace` mode as `ḥ -> χ`, `ḫ -> χ`, `ʿ -> ʔ`, `ʾ -> ʔ`.
- `docs/akkapros/printer.md` currently documents the `--ipa-proto-semitic
  {preserve,replace}` option without the corrected per-letter mapping table, so
  the mode description remains too loose to prevent the wrong merger from being
  reintroduced.
- Automatic colored-vowel logic in `src/akkapros/lib/print.py` currently uses
  `EMPHATIC_CONSONANTS = {'q', 'ṣ', 'ṭ'}` and therefore does not treat `ḥ` as
  a trigger for printer-side vowel recoloring.
- As a result, current XAR output does not automatically convert `a` to `e`
  near `ḥ`. Any such vowel quality must already be present in the source text.

This means the present public contract incorrectly collapses `ḥ` with `ḫ` in
two replacement surfaces, while already not providing any `ḥ`-specific
automatic vowel-coloring behavior.

---

# Proposed Change

Adopt the following printer contract.

## 1. XAR consonant mapping change

- In XAR output, `ḥ` shall map to `'` instead of `ḫ`.
- `ʿ` shall continue to map to `'`.
- `ʾ` shall continue to map to `'`.
- `ḫ` shall continue to map to `ḫ`.

Representative examples:

- `ḥa -> 'a`
- `ʿa -> 'a`
- `ʾa -> 'a`
- `baḥk -> ba'k`
- `baʿk -> ba'k`
- `baʾk -> ba'k`

The rationale is a reader-facing convergence in XAR: the three guttural-onset
letters `ḥ`, `ʿ`, and `ʾ` share the same visible apostrophe rendering in the
practical orthography, especially in initial position.

## 2. IPA `replace` mapping change

- In IPA `replace` mode, `ḥ` shall map to `ʔ` instead of `χ`.
- In IPA `replace` mode, `ʿ` shall continue to map to `ʔ`.
- In IPA `replace` mode, `ʾ` shall continue to map to `ʔ`.
- In IPA `replace` mode, `ḫ` shall continue to map to `χ`.
- In IPA `preserve` mode, the existing distinctions remain unchanged:
  `ḥ -> ħ`, `ḫ -> χ`, `ʿ -> ʕ`, `ʾ -> ʔ`.

Representative examples:

- `ḥa` in IPA `replace` mode renders as `ʔa`
- `ʿa` in IPA `replace` mode renders as `ʔa`
- `ʾa` in IPA `replace` mode renders as `ʔa`
- `ḫa` in IPA `replace` mode renders as `χa`

The rationale is that the repository must not treat `ḥ` as equivalent to `ḫ`
in the replacement policy. The replacement target for `ḥ` belongs with the
glottalized practical series already used for `ʿ` and `ʾ`, not with `ḫ`.

## 3. No new automatic vowel-coloring behavior for `ḥ`

- This CR does not add `ḥ` to the automatic emphatic-coloring trigger set.
- XAR grave-accent vowel coloring remains governed by the existing printer-side
  adjacency policy unless a later higher-numbered record changes it.
- The printer must not infer a `ḥ`-conditioned `a -> e` shift or any other
  vowel-quality rewrite merely because `ḥ` is present.
- If a user wants a specific vowel quality near `ḥ`, that vowel must already be
  encoded in the input text before printer conversion.

Representative examples:

- `ḥa` maps to `'a`, not automatically to `'e`.
- If the desired XAR output is `'e`, the source text must already contain a
  corresponding `e`-quality vowel before XAR rendering.

## 4. Required comment and documentation updates

- Inline comments or docstrings in `src/akkapros/lib/print.py` must describe
  the apostrophe convergence for `ḥ`, `ʿ`, and `ʾ` in XAR.
- Inline comments or docstrings in `src/akkapros/lib/print.py` must describe
  the `replace`-mode convergence for `ḥ`, `ʿ`, and `ʾ` to `ʔ`, while preserving
  `ḫ -> χ`.
- Inline comments or docstrings must also state that automatic vowel coloring
  does not treat `ḥ` as a recoloring trigger.
- User-facing docs must state both parts of the contract:
  - consonant convergence: `ḥ`, `ʿ`, `ʾ` render as `'`
  - IPA `replace` convergence: `ḥ`, `ʿ`, `ʾ` render as `ʔ`, while `ḫ` remains `χ`
  - non-goal: `ḥ`-conditioned vowel quality is not inferred by printer and
    must be present in the input text

## 5. Supersession note

- This CR narrows and updates the currently implemented/public XAR contract in
  [REQ-005](../req/005-multi-format-printer-output.md),
  [ADR-019](../adr/019-ipa-output-variant-policy.md),
  [ADR-021](../adr/021-multi-target-printer-architecture-contract.md), and the
  public printer docs where readers currently see or may infer the wrong
  equivalence.
- Older records remain historical context, but the active contract after this
  CR is:
  - XAR uses apostrophe for `ḥ`, `ʿ`, and `ʾ`, while keeping `ḫ` as `ḫ`
  - IPA `replace` mode uses `ʔ` for `ḥ`, `ʿ`, and `ʾ`, while keeping `ḫ` as `χ`

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/print.py`
- `docs/akkapros/printer.md`
- `docs/akkapros/prosody-realization-algorithm.md`
- `docs/akkapros/fullprosmaker.md`
- `docs/akkapros/xar-script.md`
- `src/akkapros/lib/helpmsg.py`
- printer self-tests in `src/akkapros/lib/print.py`
- any affected printer integration coverage in `tests/`

Implementation direction:

- Update the XAR consonant map entry for `ḥ` so it renders as `'`.
- Update the IPA `replace` consonant map entry for `ḥ` so it renders as `ʔ`.
- Update all XAR examples and assertions that currently encode `ḥ -> ḫ`.
- Update all IPA `replace` examples and assertions that currently encode
  `ḥ -> χ`.
- Add or revise code comments near the XAR consonant map and/or vowel-coloring
  helpers so the behavior is explicit to maintainers.
- Add or revise code comments near the IPA mode tables so the `replace` policy
  cannot be read as `ḥ == ḫ`.
- Add or revise user-facing docs so readers are told that apostrophe in XAR can
  reflect `ḥ`, `ʿ`, or `ʾ`, and that `replace`-mode `ʔ` can reflect the same
  three letters while `ḫ` remains distinct as `χ`.
- Keep `EMPHATIC_CONSONANTS` unchanged in this CR unless a separate governing
  record explicitly broadens the automatic vowel-coloring trigger set.

Compatibility note:

- This is a mutative public-output change for XAR and IPA `replace` mode and
  must be treated as such in release notes and output examples.

---

# Files Likely Affected

`src/akkapros/lib/print.py`
`docs/akkapros/printer.md`
`docs/akkapros/xar-script.md`
`docs/akkapros/prosody-realization-algorithm.md`
`docs/akkapros/fullprosmaker.md`
`src/akkapros/lib/helpmsg.py`
`tests/test_integration.py`
`docs/internal/cr/index.md`

---

# Acceptance Criteria

- [ ] XAR output maps `ḥ` to `'` instead of `ḫ`.
- [ ] XAR output continues to map `ʿ` to `'`.
- [ ] XAR output continues to map `ʾ` to `'`.
- [ ] XAR output continues to map `ḫ` to `ḫ`.
- [ ] IPA `replace` output maps `ḥ` to `ʔ` instead of `χ`.
- [ ] IPA `replace` output continues to map `ʿ` to `ʔ`.
- [ ] IPA `replace` output continues to map `ʾ` to `ʔ`.
- [ ] IPA `replace` output continues to map `ḫ` to `χ`.
- [ ] IPA `preserve` mode remains unchanged.
- [ ] Representative printer tests are updated so examples such as `ḥa` and a
  non-initial `ḥ` case assert apostrophe output.
- [ ] Representative IPA `replace` tests are updated so examples such as `ḥa`
  assert `ʔa` while `ḫa` still asserts `χa`.
- [ ] No test is added or changed to imply automatic `ḥ`-conditioned vowel
      recoloring.
- [ ] Comments or docstrings in the printer code explain that XAR apostrophe may
      represent `ḥ`, `ʿ`, or `ʾ`.
- [ ] Comments or docstrings in the printer code explain that IPA `replace`
  `ʔ` may represent `ḥ`, `ʿ`, or `ʾ`, while `ḫ` remains `χ`.
- [ ] Comments or docstrings in the printer code explain that `ḥ` does not join
      the automatic vowel-coloring trigger set in this CR.
- [ ] `docs/akkapros/xar-script.md` is updated so the public consonant table no
      longer states `ḥ -> ḫ`.
- [ ] `docs/akkapros/prosody-realization-algorithm.md` is updated so the IPA
  mode table no longer states `ḥ -> χ` in `replace` mode.
- [ ] `docs/akkapros/printer.md` is updated to describe the apostrophe behavior
  and the corrected IPA `replace` behavior, along with the non-automatic
  treatment of `ḥ`-conditioned vowel quality.
- [ ] Any CLI help or option-summary text that describes `replace` mode is
  updated to avoid implying `ḥ == ḫ`.
- [ ] User-facing documentation states that if a reader wants `a -> e` or other
      `ḥ`-related vowel quality in XAR, that quality must already be present in
      the input text.
- [ ] Release-facing documentation notes that this is a visible XAR and IPA
  `replace` output change.

---

# Risks / Edge Cases

Possible issues:

- readers may now be unable to distinguish `ḥ`, `ʿ`, and `ʾ` from XAR alone in
  positions where they all surface as apostrophe
- readers may now be unable to distinguish `ḥ`, `ʿ`, and `ʾ` from IPA
  `replace` output alone in positions where they all surface as `ʔ`
- documentation may accidentally imply that apostrophe output also means shared
  vowel behavior, which this CR does not approve
- documentation may update XAR but miss the parallel IPA `replace` correction,
  leaving the underlying mistake half-fixed
- examples may drift if code, self-tests, and the public XAR guide are not
  updated together

---

# Testing Strategy

Unit tests:

- update printer self-tests in `src/akkapros/lib/print.py` for `ḥ` XAR cases
- update printer self-tests in `src/akkapros/lib/print.py` for IPA `replace`
  `ḥ` cases
- add or revise representative `ḥ` XAR examples in any dedicated printer test
  coverage if present

Integration tests:

- update any affected end-to-end snapshots or assertions that include XAR output
- update any affected end-to-end snapshots or assertions that include IPA
  `replace` output

Manual review:

- compare the XAR consonant table in public docs against the printer map and
  against the self-test examples
- compare the IPA `replace` mode table and examples in public docs against the
  printer map and against the self-test examples
- verify docs explicitly separate consonant mapping from vowel-coloring policy

---

# Rollback Plan

If the new reader-facing convergence proves unworkable, revert the XAR and IPA
`replace` `ḥ` mappings together with the aligned tests/docs so the previous
public contracts are restored consistently rather than leaving one surface
corrected and the other stale.

---

# Related Issues

- [REQ-005](../req/005-multi-format-printer-output.md)
- [ADR-019](../adr/019-ipa-output-variant-policy.md)
- [ADR-011](../adr/011-multi-format-printer-outputs.md)
- [ADR-021](../adr/021-multi-target-printer-architecture-contract.md)
- [ADR-022](../adr/022-output-format-public-contract-boundaries.md)
- [CR-047](047-close-phonetizer-pause-and-reconstruction-gaps.md)

---

# Tasks

## Implementation

- [ ] Change the XAR `ḥ` mapping in the printer library
- [ ] Change the IPA `replace` `ḥ` mapping in the printer library
- [ ] Add or revise code comments/docstrings for apostrophe convergence and the
  corrected IPA `replace` convergence and the non-automatic `ḥ`
  vowel-coloring policy

## Tests

- [ ] Update XAR self-tests for `ḥ` examples
- [ ] Update IPA `replace` self-tests for `ḥ` examples
- [ ] Update any affected printer integration assertions

## Documentation

- [ ] Update the XAR guide
- [ ] Update the printer guide
- [ ] Update the prosody-realization algorithm guide and any other IPA mode
  tables or summaries
- [ ] Update CLI help text or option-summary text where needed
- [ ] Note the visible XAR and IPA `replace` output change in release-facing
  docs

## Review

- [ ] Verify acceptance criteria
- [ ] Confirm docs and test examples match the final XAR map and IPA `replace`
  map

---

# Implementation Blockers

None currently.

---

# Notes

- This CR intentionally changes reader-facing `ḥ` replacement behavior in two
  places only: XAR and IPA `replace` mode.
- It does not change IPA `preserve` mode or MBROLA behavior.
- This CR intentionally does not define a new phonological inference rule for
  `ḥ`-conditioned vowel quality.