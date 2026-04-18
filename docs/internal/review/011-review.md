---
review_id: review-011
status: Done
created: 2026-04-18
updated: 2026-04-18
reviewer: GitHub Copilot (GPT-5.4)
scope: >-
  src/akkapros/lib/phonetize.py,
  src/akkapros/lib/constants.py,
  src/akkapros/lib/utils.py,
  tests/test_phonetize_lib.py,
  docs/internal/cr/047-close-phonetizer-pause-and-reconstruction-gaps.md,
  docs/internal/cr/050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md,
  and docs/internal/cr/058-remove-synthetic-pause-allocation-from-metricalc.md.
---

# Code and Project Review — Phonetizer Punctuation Suites and EOL Pause Handling

## 1. Executive Summary

The current phonetizer behavior is internally consistent, but it is narrower
than the user goal of accepting journalistic punctuation around quotations and
paragraph structure. The live row builder in
[src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
deliberately treats punctuation suites and explicit newlines as different kinds
of input events: punctuation is consumed only until whitespace or newline,
while `\n` always emits its own long `<EOL>` pause row. That means input such
as `ba ..\nna` necessarily becomes two pause rows today, one for `..` and one
for `<EOL>`. The main problem is not an implementation bug, but a contract gap:
the repository has no explicit paragraph-break model, so it cannot yet express
the difference between sentence-final punctuation followed by a line break and
an actual paragraph break formed by two successive line breaks.

## 2. Architecture Assessment

### 2.1 Strengths

- The Phase 1 row builder in
  [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
  is straightforward to audit because branch order directly encodes pause-row
  ownership. The `build_phone_rows()` loop handles `\n` before ordinary segment
  continuation and emits `<EOL>` through a dedicated `_new_pause_row()` call.
- Punctuation-suite grouping is explicit rather than accidental. The helper
  `_consume_pause_suite()` in
  [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
  stops at whitespace and newline, so plain punctuation never silently absorbs
  a following line break.
- Punctuation classification precedence is already pinned. The helper
  `_classify_pause_suite()` in
  [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
  applies `Q > E > S > C > I` after grouping, which matches the intent of
  [docs/internal/cr/050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md](../cr/050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md).
- Existing tests already protect the current contract. In
  [tests/test_phonetize_lib.py](../../../tests/test_phonetize_lib.py),
  `test_pause_rows_and_transition_rows_use_canonical_codes()` pins newline as a
  separate `<EOL>` row, and
  `test_grouped_punctuation_suite_uses_cr050_precedence()` shows suite typing
  only after grouping has been decided.

### 2.2 Areas for Improvement

- High: the current grouping boundary is too shallow for journalistic text.
  `_consume_pause_suite()` stops on any whitespace, so punctuation that is
  logically one clause-final cluster but written with spaces or a following
  quote/newline is split before classification. This is why `..\n` yields two
  pause rows instead of one composite end-of-sentence event plus a structural
  line/paragraph signal.
- High: paragraph semantics are absent from the pause-row contract. Newline is
  typed as ordinary statement silence `S` with long length in the current
  model, but there is no distinct representation for “sentence-final punctuation
  followed by line break” versus “blank-line paragraph break” versus “final
  document break.”
- Medium: the current system conflates two separate questions:
  “what punctuation cluster closed the clause?” and
  “what layout boundary followed it?”. The live row schema can serialize two
  adjacent pause rows, but there is no governing rule for when that adjacency is
  desirable, mandatory, or compressible.
- Medium: EOF and EOL are normalized together for regex context in
  [src/akkapros/lib/utils.py](../../../src/akkapros/lib/utils.py), but the row
  builder still makes an explicit structural distinction by materializing only
  actual newlines as `<EOL>` and normalizing missing final breaks separately.
  That asymmetry is acceptable today, but it should be documented more clearly
  if paragraph-aware behavior is added.

## 3. Code Quality Assessment

- Current behavior is not ambiguous in code. In
  [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py), the
  relevant control flow is:
  `space -> finish syllable only`,
  `newline -> finish syllable + append <EOL> long pause row`,
  `punctuation char -> consume suite until whitespace/newline + classify suite + append one pause row`.
- The separation is reinforced by helper design:
  `_consume_pause_suite()` never includes newline,
  `_append_armored_pause_rows()` classifies exactly one normalized armored span,
  and `_classify_pause_suite()` never sees a mixed punctuation-plus-newline
  suite from plain text input.
- The review found no evidence that multiple adjacent punctuation marks are
  merged incorrectly under the current contract. They are merged intentionally
  when contiguous and non-whitespace-separated, for example `?!!!` or `...:`.
  The issue is instead that line breaks and whitespace terminate grouping too
  early for some journalistic layouts.
- The current tests are good for the existing contract but do not yet cover the
  paragraph-oriented cases the user described, especially:
  punctuation followed by closing quotes then newline,
  punctuation followed by one newline versus two newlines, and
  paragraph-adjacent consecutive pause rows as a first-class design choice.

## 4. Documentation Assessment

- The active internal records already pin the present split model.
  [docs/internal/cr/047-close-phonetizer-pause-and-reconstruction-gaps.md](../cr/047-close-phonetizer-pause-and-reconstruction-gaps.md)
  states that explicit newlines are encoded as `<EOL>` long-pause rows, while
  grouped punctuation suites are classified by suite precedence.
- [docs/internal/cr/050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md](../cr/050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)
  likewise documents newline as its own pause source and suite precedence only
  after grouping.
- What is missing is one explicit governing record for paragraph-sensitive pause
  modeling. The current documentation says what newline and punctuation do
  separately, but not what should happen when they occur together in prose-like
  formatting.

## 5. Research / Functional Assessment

Current functional behavior for the reviewed question is as follows.

- Contiguous punctuation characters are grouped into one consumed suite if they
  are adjacent and belong to the allowed punctuation inventory.
- That grouped suite is typed by precedence in `_classify_pause_suite()`:
  any `?` yields `Q`, else any `!` yields `E`, else any `.` yields `S`, else
  continuation punctuation or ellipsis yields `C`, else residual allowed marks
  yield `I`.
- A literal newline is not part of that suite. It is handled earlier and always
  emits its own long `<EOL>` pause row.
- Therefore `ba ..\nna` is expected to produce two silence events in Phase 1:
  one punctuation-owned pause for `..` and one structural newline-owned pause
  for `<EOL>`.

That behavior is coherent, but it leaves the repository without a good way to
model paragraph-sensitive prose pauses.

The best implementation direction is not to make newline disappear into the
preceding punctuation suite. That would erase structural information needed for
future secondary-pause or paragraph-final behavior. Instead, the repository
should keep newline structurally visible and add an explicit paragraph-break
layer or pause subtype contract on top of the existing pause rows.

Recommended functional model:

1. Keep punctuation-cluster ownership and newline ownership separate in Phase 1.
2. Introduce explicit paragraph-break detection after row construction, not by
   making `_consume_pause_suite()` absorb newline.
3. Distinguish at least these cases in the contract:
   - sentence-final punctuation followed by one newline
   - bare one-newline line break without sentence-final punctuation
   - two successive newlines as paragraph break
   - final EOF break without literal trailing newline
4. Represent paragraph break either as:
   - one new dedicated pause subtype or label, or
   - two adjacent pause rows with an explicit higher-level grouping rule that
     downstream duration and metrics code can interpret deterministically.

The cleaner design is a dedicated paragraph-aware pause event rather than
trying to overload ordinary `S` plus `<EOL>` rows.

For the user’s two prose cases, a good future contract would be:

- `Sentence punctuation + one newline`
  Keep the punctuation-owned clause-final pause and preserve a structural line
  break signal, but let a later paragraph/pause policy decide whether the two
  adjacent rows collapse to one realized clause-final pause or remain two
  distinct pause events.
- `Two successive newlines`
  Recognize this as paragraph break, not as two independent ordinary `<EOL>`
  rows with no higher meaning. This is the point where a secondary pause or a
  longer final pause can be introduced once the policy is decided.

## 6. Process and Engineering Practices

- The repository already follows a strong pattern of pinning row-contract
  behavior in CRs and unit tests. This should continue: paragraph-sensitive
  pause behavior should be introduced through a new ADR or CR rather than by ad
  hoc implementation.
- The current internal specs are good historical grounding because they make it
  clear that the present behavior was intentional. That means any change here is
  a contract extension, not a bug fix disguised as cleanup.
- The next governance artifact should state whether downstream tools such as
  metrics and printer should see paragraph break as:
  one special row,
  one grouped pair of rows, or
  one ordinary row plus extra metadata.

## 7. Recommendations (Priority Order)

1. High: add a governing record for paragraph-aware pause semantics in the
   phonetizer. Minimal next step: write an ADR or CR that defines how one
   newline, two successive newlines, and punctuation-plus-newline combinations
   should be represented in Phase 1 rows.
2. High: preserve newline as a structurally distinct signal rather than merging
   it into ordinary punctuation suites. Minimal next step: explicitly reject any
   design that simply extends `_consume_pause_suite()` to swallow `\n`.
3. High: define a paragraph-break contract for the prose cases described by the
   user. Minimal next step: specify whether paragraph break becomes a new pause
   subtype/label or a deterministic grouping of adjacent pause rows.
4. Medium: add focused unit tests for prose-style punctuation adjacency,
   especially quote-wrapped sentence-final punctuation before newline and blank-
   line paragraph breaks. Minimal next step: add cases parallel to the existing
   suite-grouping tests in
   [tests/test_phonetize_lib.py](../../../tests/test_phonetize_lib.py).
5. Medium: document the distinction between punctuation-owned pause rows and
   layout-owned pause rows in public phonetizer docs once the paragraph model is
   chosen. Minimal next step: add one short section describing why `<EOL>` is
   separate from punctuation suites and what paragraph break means in the row
   contract.

## 8. Summary Verdict

The current phonetizer implementation handles adjacent punctuation suites and
explicit `<EOL>` rows consistently, but it is not yet equipped with a proper
paragraph-break contract; the next safe step is a spec-level extension that
keeps newline structurally distinct while adding deterministic paragraph-aware
pause semantics.
