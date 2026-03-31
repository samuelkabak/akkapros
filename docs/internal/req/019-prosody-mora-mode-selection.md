---
req_id: REQ-019
status: Draft
priority: High
impact: Mutative
created: 2026-03-30
updated: 2026-03-31
related_adrs: 'ADR-034, ADR-008, ADR-009, ADR-020'
implemented_by: 'CR-027'
---

# Requirement: Prosody Mora Mode Selection

# Summary

The system shall add a new prosody configuration option named `mora_mode`
with CLI surface `--mora-mode {bi|mono}` in both `prosmaker` and
`fullprosmaker`.

Mode `bi` shall remain the default and shall preserve the current bimoraic
behavior exactly. Mode `mono` shall reuse the same accentuation candidate
selection, legality rules, structural grouping rules, and style handling
(`lob` / `sob`), but it shall remove the current requirement that a standalone
word or eligible prosodic unit must have an odd mora count before accentuation
is attempted.

This requirement exists to support comparison between the toolkit's bimoraic
prosody model and an academic non-bimoraic accentuation workflow used in
Assyriology.

---

# Motivation

The current prosody engine is explicitly bimoraic: it checks mora parity and
only activates accentuation when a word or merge candidate has odd mora count.
That behavior is correct for the repository's current stress-timed realization
model, but it makes direct comparison with the conventional academic model more
difficult.

Researchers need a switchable mode that preserves the existing accentuation
hierarchy and repair legality while disabling the bimoraic gating rule. This
allows side-by-side processing of the same syllabified input under two
interpretations:

- `bi`: accentuation is driven by odd-to-even mora balancing.
- `mono`: accentuation is driven by the existing style hierarchy without a
  parity prerequisite.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given `prosmaker` is invoked without `--mora-mode`, when prosody output is
      generated, then behavior is identical to the current implementation and is
      equivalent to explicit `--mora-mode bi`.
- [ ] Given `fullprosmaker` is invoked without `--mora-mode`, when the full
      pipeline is run, then the prosody stage behavior is identical to the
      current implementation and is equivalent to explicit `--mora-mode bi`.
- [ ] Given `--mora-mode bi`, when a non-function standalone word has even morae,
      then the engine leaves it unaccentuated exactly as it does today.
- [ ] Given `--mora-mode bi`, when a non-function standalone word has odd morae,
      then the engine attempts accentuation exactly as it does today.
- [ ] Given `--mora-mode mono`, when a non-function standalone word is processed,
      then the engine may attempt accentuation regardless of whether its current
      mora count is odd or even.
- [ ] Given `--mora-mode mono`, when a standalone word has an even mora count
      and a legal accentuation candidate exists, then accentuation may be
      applied once using the same `lob` / `sob` selection priorities already in
      use for candidate choice.
- [ ] Given `--mora-mode mono`, when a standalone word has an odd mora count and
      a legal accentuation candidate exists, then accentuation may still be
      applied once using the same candidate rules.
- [ ] Given any mora mode, when a token is a function word, then function-word
      exclusion and merge behavior remain unchanged.
- [ ] Given any mora mode, when input contains explicit `+` links, then
      explicit-link grouping semantics remain unchanged and linked words before
      the eligible tail remain structurally ineligible for accentuation even
      when they are not function words.
- [ ] Given any mora mode, when a legal accentuation candidate is selected, then
      the set of allowed operations remains unchanged: vowel lengthening,
      non-final coda gemination, and existing last-resort onset/glottal
      accentuation.
- [ ] Given `--mora-mode mono`, when internal accentuation is not available for
      a structurally determined unit, then the engine does not forward-merge to
      search for bimoraic resolution and instead falls through directly to the
      existing last-resort onset/glottal accentuation.
- [ ] Given prosody output written by `prosmaker`, when YAML front matter is
      emitted, then `metadata.options.mora_mode` is present with value `bi` or
      `mono`.
- [ ] Given output written by `fullprosmaker`, when stage outputs inherit
      options, then `metadata.options.mora_mode` is preserved through prosody
      output and downstream generated artifacts.
- [ ] Given existing self-tests and pytest coverage, when the feature is
      implemented, then all pre-existing tests pass unchanged.
- [ ] Given new behavior is implemented, when tests are added, then they cover
      `prosmaker` self-tests, CLI option parsing, front matter propagation, and
      representative mono-mode accentuation cases without rewriting existing
      bi-mode expectations.
- [ ] Given documentation is updated, when users read prosody and full-pipeline
      docs, then they can see the exact semantic difference between `bi` and
      `mono`, the default, and representative examples of changed output.
- [ ] Given the demo corpus scripts are run, when prosody branches are
      generated from the shared `corpus_syl.txt`, then they additionally
      produce `corpus-mono-lob_*` artifacts for mono-mode LOB alongside the
      existing bimoraic LOB and SOB branches.

---

# User Story (optional)
> As a researcher comparing the bimoraic prosody model with the conventional
> academic accentuation model, I want a switchable mora mode so that I can run
> the same text through both interpretations without forking the codebase.

---

# Interface Notes
- Input: syllabified `*_syl.txt` input for `prosmaker`; `*_proc.txt` input for
  `fullprosmaker`.
- CLI additions:
  - `prosmaker --mora-mode {bi,mono}`
  - `fullprosmaker --mora-mode {bi,mono}`
- Default: `bi`
- YAML front matter:
  - `metadata.options.mora_mode: bi|mono`
- Affected components:
  - `src/akkapros/lib/prosody.py`
  - `src/akkapros/cli/prosmaker.py`
  - `src/akkapros/cli/fullprosmaker.py`
  - prosody/front matter utilities as needed for option propagation
  - prosody self-tests and pytest coverage
  - user documentation for `prosmaker` and `fullprosmaker`
      - `demo/akkapros/prosmaker/corpus-demo.ps1`
      - `demo/akkapros/prosmaker/corpus-demo.sh`
      - `demo/README.md`

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Preferred implementation shape: centralize the mora-mode gate in one
  mode-aware eligibility policy used by both `Word` and `MergedUnit`, rather
  than scattering duplicated `if mode == ...` checks across multiple branches.
- Explicit `+` links must keep pre-tail linked words structurally locked from
      accentuation in both modes, even when those words are content words.
- Mono mode should replace parity as a completion shortcut with structural
      grouping only: determine the unit, attempt internal accentuation, then fall
      directly to last resort if no legal candidate exists.
- Migration: none for existing users because `bi` remains default; update docs,
  self-tests, fixtures, and demo wrappers only where new `mono` coverage is
  introduced.

# Related
- Related ADRs: [ADR-034](../adr/034-prosody-mora-modes-and-explicit-link-locking.md),
  [ADR-008](../adr/008-bimoraic-prosody-and-accent-styles.md),
  [ADR-009](../adr/009-function-word-and-merge-policy.md),
  [ADR-020](../adr/020-deterministic-merge-traversal.md)
- Related REQs: [REQ-003](003-bimoraic-prosody-realization-algorithm.md),
  [REQ-007](007-full-pipeline-orchestration.md),
  [REQ-013](013-cli-file-front-matter-and-metadata-propagation.md),
  [REQ-010](010-built-in-self-tests-and-test-infrastructure.md)
- Implementation CRs: [CR-027](../cr/027-add-prosody-mora-mode-selection.md)

# Non-Goals
- This requirement does not change the existing `lob` / `sob` accentuation
  site-selection priorities.
- This requirement does not introduce new accentuation operations or legalize
  final consonant gemination.
- This requirement does not rename existing output files or add a new file
  format.
- This requirement does not alter the existing default behavior of any CLI.

# Security / Safety Considerations
- This change is behavioral rather than security-sensitive, but the selected
  `mora_mode` must be recorded in front matter so downstream analysis is not
  silently misinterpreted.
- Documentation must state clearly that `mono` is a comparative research mode
  and not the repository's current bimoraic default.