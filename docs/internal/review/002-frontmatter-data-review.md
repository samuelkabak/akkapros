Status: Draft

# Code and Project Review — Front Matter Data Minimization for Pipeline Steps

Review ID: review-002
Date: 2026-03-27
Reviewer: GitHub Copilot (GPT-5.4)
Scope: `docs/internal/adr/027-yaml-front-matter-for-cli-pipeline-files.md`, `docs/internal/req/013-cli-file-front-matter-and-metadata-propagation.md`, `docs/internal/cr/018-add-cli-file-front-matter-and-metadata-propagation.md`, and the current stage contracts in `docs/internal/req/001`, `002`, `003`, `004`, `005`, and `007`.

---

## 1. Executive Summary

The front matter `metadata.data` blocks should stay deliberately small and should carry only scalar values that are either needed downstream or useful for cross-step validation. The best minimal design is an append-only per-step record with 3 to 5 counters per stage, emphasizing repeated counts that can expose silent drift: `line_count`, `word_count`, `function_word_count`, `explicit_word_link_count`, `syllable_count`, `prosodic_unit_count`, and `accentuated_syllable_count` where applicable. The most important immediate decision for `CR-018` is to make `function_word_count` and `word_count` appear in both `syllabify` and `prosody`, and to make the explicit user word-link count a distinct field rather than inferring it later from transformed output.

## 2. Architecture Assessment

### 2.1 Strengths

- The staged pipeline already provides natural checkpoints where compact validation counters can be attached without changing the content model.
- `ADR-027` correctly separates shared metadata from file content and makes per-step `metadata.data` blocks the right place for propagated validation facts.
- Repeating a small number of counts across steps is justified here because the pipeline is research-grade and silent drift is more costly than a few extra metadata lines.

### 2.2 Areas for Improvement

- `CR-018` currently defines the front matter container but not a compact field inventory, so implementation could become verbose or inconsistent across stages.
- Some counts are semantically unstable unless they are defined precisely. In particular, an explicit word-link counter is ambiguous unless the spec states whether it counts literal link markers, linked groups, or words participating in those groups.
- The pipeline also has a line-integrity edge case when a content line ends with attached `-` or `+` and the lexical group continues on the next line without whitespace. Auto-merging those lines hides malformed input and invalidates `line_count` as a validation signal.
- Later stages should not dump report-level detail into front matter. The full metrics body already carries rich output; the front matter should carry only validation and propagation facts.

## 3. Code Quality Assessment

- For this feature, the key code-quality risk is not complexity but semantic drift: if different stages compute “word count” or “function word count” differently, the front matter will create false mismatches.
- The review therefore recommends a small set of counters with stable definitions and explicit exclusion rules for punctuation, escaped non-Akkadian spans, and format-only tokens.
- The review also recommends rejecting implicit cross-line continuation after terminal `-` or `+` rather than silently merging lines, because preserving trustworthy line counts is more valuable than repairing a rare malformed input case.
- Scalar integers and booleans are sufficient. Do not store token lists, line previews, or per-word annotations in front matter.

## 4. Documentation Assessment

- `CR-018` should define field semantics explicitly, especially for `word_count`, `function_word_count`, and explicit word-link handling.
- The spec should state that upstream stage data is propagated unchanged; each current stage adds only its own block and must not rewrite earlier blocks.
- The spec should also state that empty current-stage blocks are omitted. This matters especially for `print`, where a minimal design may justify no additional step-specific counters.
- The spec should define the dangling line-link policy explicitly: a line ending with attached `-` or `+` that continues on the next physical line is an input error, not a line merge.

## 5. Research / Functional Assessment

The review goal here is not to maximize metadata, but to choose a compact validation spine that catches the kinds of silent errors the pipeline is vulnerable to. The earlier function-word syllabification problem is a good example: if `function_word_count` had been present in both `syllabify` and `prosody`, the mismatch would have surfaced immediately.

### 5.1 Recommended Rules

- Keep `metadata.data.<step>` limited to scalar values only.
- Prefer counts and small booleans over derived ratios or report metrics.
- Repeat a few strategically chosen counts across steps when that repetition validates invariants.
- Use one canonical field name per concept across all steps.
- Count explicit user word links separately from automatic prosodic merging.
- Do not store anything in front matter that can only be interpreted by re-reading a large body of stage-specific content.
- Preserve `line_count` as a hard validation signal by rejecting malformed cross-line continuation instead of repairing it silently.

### 5.2 Canonical Field Definitions

| Field | Definition | Notes |
|---|---|---|
| `line_count` | Number of physical content lines after removing front matter | Useful for line-preservation checks |
| `non_empty_line_count` | Number of content lines containing Akkadian material after trimming whitespace | Useful in `atfparse`; optional elsewhere |
| `word_count` | Number of Akkadian lexical words in content, excluding punctuation-only and escaped non-Akkadian chunks | Keep this definition stable across steps |
| `function_word_count` | Number of words classified by the function-word inventory at that stage | Recommended in multiple steps for validation |
| `explicit_word_link_count` | Number of literal user-provided word-link markers inherited from input. In current scope this is the count of explicit `+` links, not automatic merges added by prosody | Prefer this over ambiguous “premerged word count” |
| `syllable_count` | Number of Akkadian syllables represented in the stage output | Useful from `syllabify` onward |
| `prosodic_unit_count` | Number of final prosodic units after prosody grouping | Prosody-specific downstream fact |
| `automatic_merge_count` | Number of automatic cross-word merges introduced by prosody, excluding explicit `+` links inherited from input | Useful if merge validation is desired |
| `accentuated_syllable_count` | Number of syllables marked as accentuated in the prosody output | Compact and useful downstream |

### 5.3 Recommended Minimal Set by Step

| Step | Recommended fields | Why this is enough |
|---|---|---|
| `atfparse` | `line_count`, `non_empty_line_count`, `word_count` | Captures line preservation and cleaned-text size without encoding parser internals |
| `syllabify` | `line_count`, `word_count`, `syllable_count`, `function_word_count`, `explicit_word_link_count` | Adds the first strong validation layer and can expose tokenization or function-word drift |
| `prosody` | `word_count`, `function_word_count`, `explicit_word_link_count`, `prosodic_unit_count`, `accentuated_syllable_count` | Satisfies the requested minimum and adds one compact grouping counter plus one compact accent counter |
| `metrics` | `word_count`, `function_word_count`, `explicit_word_link_count`, `syllable_count`, `accentuated_syllable_count` | Repeats validation-critical counts without duplicating the metrics report itself |
| `print` | No required new fields; optionally `word_count` only if implementation wants a final render check | Upstream data already propagates, so adding more usually increases verbosity without adding value |

### 5.4 Recommended Optional Extension Set

These fields are useful, but only if you want a slightly richer validation layer:

- `atfparse.translation_line_count`: useful only if translation side outputs remain part of the validation story.
- `syllabify.hyphen_boundary_count`: useful if hyphen policy is a recurring failure point.
- `prosody.automatic_merge_count`: useful if merge behavior is under active tuning and needs quick regression visibility.
- `metrics.prosodic_unit_count`: useful if metrics re-parses merged units and you want a downstream agreement check with `prosody`.

### 5.5 Line-Continuation Edge Case Analysis

Problem:
Some malformed inputs may end a physical line with attached `-` or `+` and continue the same lexical or prosodic group on the following line with no intervening whitespace. Repairing this by auto-merging the two lines makes the content look valid but changes `line_count`, which front matter is supposed to preserve as a validation signal.

Option 1:
Reject this situation and emit a clear error.

- Pros: preserves physical line integrity as a stable invariant
- Pros: keeps `line_count` trustworthy for validation across the pipeline
- Pros: makes malformed inputs visible immediately
- Cons: requires user correction before processing continues

Option 2:
Auto-merge the lines and report a line delta.

- Pros: can salvage malformed input automatically
- Cons: weakens `line_count` as a validation signal
- Cons: adds extra reporting logic for a rare edge case
- Cons: risks hiding a broken source file or upstream formatting problem

Recommendation:
Choose Option 1. This edge case is expected to be uncommon, and preserving line-count integrity is more valuable than repairing it implicitly. If Option 2 is ever revived, `line_delta` should be emitted only when non-zero.

### 5.6 Recommended Non-Goals for `metadata.data`

- Do not store lists of function words.
- Do not store per-line statistics.
- Do not store syllable-type distributions in front matter; those belong in metrics outputs.
- Do not store rendered-format details in `print` beyond a minimal validation counter.
- Do not store values that are already carried better by `file`, `step`, `format`, or `options`.

## 6. Process and Engineering Practices

| Practice | Recommendation |
|---|---|
| Stable naming | Approve canonical snake_case field names before implementation |
| Cross-step validation | Intentionally duplicate a small number of counts across steps |
| Append-only propagation | Earlier stage blocks should be copied forward unchanged |
| Size control | Target 3 to 5 fields per populated step block |
| Ambiguity control | Define `explicit_word_link_count` precisely and avoid vague “premerged word count” wording |
| Line integrity | Reject implicit cross-line continuation after terminal `-` or `+` |
| Terminal stages | Allow `print` to add nothing if no compact new validation fact is needed |

## 7. Recommendations (Priority Order)

1. High: In `CR-018`, define a strict minimal data spine using `word_count`, `function_word_count`, and `explicit_word_link_count`, with `syllable_count`, `prosodic_unit_count`, and `accentuated_syllable_count` added only where they naturally belong.
2. High: Specify that `explicit_word_link_count` counts literal user-provided word-link markers inherited from upstream input. In current scope this means explicit `+` links, not automatic merges introduced by prosody.
3. High: Require `function_word_count` to be computed at both `syllabify` and `prosody`, because this is the smallest useful duplicated signal for catching silent classification or tokenization problems.
4. High: Reject malformed cross-line continuation after terminal `-` or `+` with a clear error; do not auto-merge lines, because that breaks `line_count` as a validation invariant.
5. Medium: Keep `print` step data empty by default unless a concrete validation need appears; propagated upstream blocks are already enough for most print outputs.
6. Medium: If merge behavior needs active monitoring, add `automatic_merge_count` to `prosody` and optionally repeat `prosodic_unit_count` in `metrics`.
7. Low: If parser regressions around line handling remain a concern, add `translation_line_count` or `hyphen_boundary_count` as optional fields, but keep them out of the default minimal set.

## 8. Summary Verdict

The project is ready to extend `CR-018` with a compact, implementation-ready front matter data contract, provided the spec adopts a small scalar-only field set and treats repeated counts as deliberate validation signals rather than redundancy.

---

Notes for selection into `CR-018`:

- Safest minimal default set:
  - `atfparse`: `line_count`, `non_empty_line_count`, `word_count`
  - `syllabify`: `line_count`, `word_count`, `syllable_count`, `function_word_count`, `explicit_word_link_count`
  - `prosody`: `word_count`, `function_word_count`, `explicit_word_link_count`, `prosodic_unit_count`, `accentuated_syllable_count`
  - `metrics`: `word_count`, `function_word_count`, `explicit_word_link_count`, `syllable_count`, `accentuated_syllable_count`
  - `print`: none

- If you want one extra prosody validation field, add `automatic_merge_count` there and nowhere else first.
- Recommended line policy: reject attached terminal `-` / `+` continuation across physical lines instead of repairing it silently.
