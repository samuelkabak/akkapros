---
cr_id: CR-025
status: Done
priority: High
impact: Mutative
created: 2026-03-29
updated: 2026-03-29
implements: 'REQ-005'
---

# Change Request: Fix Markdown Line Breaks in Bold Printer Output

# Summary

Fix the printer's `_accent_bold.md` output so source line boundaries survive in
Markdown renderers. The current bold Markdown output writes plain newline
characters between lines, but many Markdown readers collapse those newlines into
one visual paragraph.

The printer shall emit an explicit Markdown line break marker at each preserved
input line boundary in bold output. For this change, the approved mechanism is
the trailing backslash character `\` before each intended Markdown newline.

---

# Motivation

This is a rendering bug in the bold printer output. The file content preserves
physical line breaks, but common Markdown engines do not treat those physical
newlines as hard line breaks, so adjacent Akkadian lines appear merged into a
single rendered line.

The bold output is intended for human reading and publication. If lineation is
lost at render time, the Markdown artifact no longer preserves the prosodic or
editorial structure represented by the original line layout.

---

# Scope

## Included

- Preserve intended line boundaries in `_accent_bold.md` rendered output.
- Emit a Markdown hard line-break marker using a trailing backslash `\` at each
  preserved output line boundary.
- Keep the existing bold-marking behavior for accentuated syllables.
- Keep existing frontmatter behavior unchanged.
- Add regression tests for Markdown line-break serialization.
- Update printer documentation for bold Markdown output semantics.

## Not Included

- Changing acute, IPA, XAR, or MBROLA output formats.
- Replacing preserved line boundaries with paragraph breaks or blank-line
  policy changes.
- General redesign of printer formatting beyond this Markdown line-break fix.

---

# Current Behavior

The printer writes `_accent_bold.md` using ordinary newline characters between
lines. In Markdown readers, adjacent non-blank lines are typically rendered as
one visual paragraph unless the lines end with a Markdown hard break marker.

Example current output:

```md
ukappit-ma : ti**ām**tu pitiqša
tā**ḫā**za **ik**taṣar : ana‿ilī nip**rī**ša
aḫrâtaš eli‿apsî : u**lam**min ti**ām**tu
```

In common Markdown renderers, those three lines may appear as one continuous
rendered line or paragraph rather than three distinct displayed lines.

---

# Proposed Change

When writing `_accent_bold.md`, append a trailing backslash `\` to every
non-final line that must remain a rendered line break in Markdown.

Example target output:

```md
ukappit-ma : ti**ām**tu pitiqša\
tā**ḫā**za **ik**taṣar : ana‿ilī nip**rī**ša\
aḫrâtaš eli‿apsî : u**lam**min ti**ām**tu
```

Behavior rules:

- preserve one rendered line per logical input line
- do not add a trailing backslash where no following rendered line exists
- preserve blank-line semantics if blank lines are already meaningful in the
  input/output contract
- keep bold accentuation markup unchanged apart from the added line-break
  marker

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/cli/printer.py`
- `src/akkapros/lib/print.py`

Serialization rule:
- for bold Markdown output only, serialize each intended line break as a
  Markdown hard break by placing `\` immediately before the newline character
- the final content line should not receive a forced trailing backslash unless
  a subsequent rendered line is intended

Compatibility notes:
- keep YAML frontmatter behavior unchanged for `.md` output
- do not alter how bold spans are inserted around accentuated syllables
- do not change non-Markdown output emitters

---

# Files Likely Affected

`src/akkapros/cli/printer.py`
`src/akkapros/lib/print.py`
`docs/akkapros/printer.md`
tests covering printer output serialization and representative fixtures

---

# Acceptance Criteria

- [x] Given `--bold`, `_accent_bold.md` preserves one rendered Markdown line
      per intended input line.
- [x] Given two adjacent logical lines in bold output, the first serialized
      line ends with a trailing backslash `\` so Markdown renders a hard line
      break.
- [x] Given the final logical line in bold output, it is not required to end
      with a trailing backslash.
- [x] Given bold-marked syllables, the existing `**...**` markup remains
      unchanged apart from the added line-break marker.
- [x] Given frontmatter in `_accent_bold.md`, it remains valid and unchanged by
      this CR.
- [x] Tests are added or updated to assert the exact serialized line-break
      shape in `_accent_bold.md`.
- [x] Documentation is updated to state that bold Markdown output uses
      backslash-based hard line breaks to preserve input lineation in Markdown
      readers.

---

# Risks / Edge Cases

Possible issues:

- Some Markdown tools may treat trailing backslashes differently if lines end
  with trailing spaces or escaping logic is altered elsewhere.
- Blank lines and terminal newlines must not accidentally gain extra visible
  escape markers.
- Existing snapshot tests may need fixture updates because the serialized `.md`
  output will change even though the intended visible layout is being fixed.

---

# Testing Strategy

Unit tests:

- serialize adjacent bold Markdown lines with trailing backslashes
- ensure the final logical line does not gain an unnecessary trailing
  backslash
- ensure bold markup remains correct on lines containing accentuated syllables

Integration tests:

- end-to-end printer run produces `_accent_bold.md` with the required
  backslash line-break markers
- representative corpus fixture covers multiple consecutive lines and blank-line
  behavior if present

Manual tests:

- open `_accent_bold.md` in a Markdown preview and verify adjacent lines render
  as separate visible lines rather than one paragraph

---

# Rollback Plan

Revert the bold Markdown serializer to its prior newline-only behavior if the
backslash-based line-break strategy proves incompatible, and update docs and
tests accordingly.

---

# Related Issues

- Falls under the bold Markdown output contract in
  [REQ-005](../req/005-multi-format-printer-output.md).
- Adjacent to printer/frontmatter work tracked in
  [CR-024](024-minimize-frontmatter-and-enable-source-flexible-stage-inputs.md),
  but independent of that metadata-contract change.

---

# Tasks

## Implementation

- [x] Update bold Markdown serialization to emit trailing backslashes at
      intended line breaks.
- [x] Preserve existing bold-marking and frontmatter behavior.

## Tests

- [x] Add focused unit coverage for serialized Markdown line breaks.
- [x] Update integration fixtures for `_accent_bold.md` output.
- [ ] Verify Markdown preview behavior manually or through documented review
      steps.

## Documentation

- [x] Update printer docs to describe Markdown hard line-break behavior in
      bold output.

## Review

- [x] Verify the chosen backslash strategy matches the desired Markdown readers
      used by the project.

---

# Notes for CR-025

This CR intentionally specifies the backslash hard-break form rather than the
two-space Markdown variant, because the requested fix explicitly prefers `\`
as the serializer for intended line breaks.

Implemented on 2026-03-29:

- Bold Markdown serialization now adds a trailing backslash before preserved
  newlines only when the current and following logical lines are both non-blank.
- Blank lines remain plain blank lines without forced Markdown escape markers.
- Printer docs, requirement acceptance text, self-tests, and integration
  fixtures were updated to the new serialized shape.