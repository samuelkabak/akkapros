---
cr_id: CR-103
status: Done
priority: High
impact: Mutative
created: 2026-05-10
updated: 2026-05-10
implements: ''
---

# Change Request: Count Lexical Words (Not Merged Words) in Metrics

## Summary

`analyze_text()` in `_metrics_stats.py` currently counts merged words (words containing `+` or `&`) as single words. This undercounts `total_words` and produces incorrect `syllables_per_word` and `morae_per_word` statistics. The fix is to split merged words into their lexical parts before computing word-level statistics, while keeping syllable-level and mora-level statistics unchanged.

Example: `šar+gi·mir&dad~·mē` is currently counted as **1 word** but should count as **3 lexical words**: `šar`, `gimir`, `dadmē`.

---

## Motivation

Bug fix. Words linked with `+` or `&` are merged **prosodically** (they form a single prosodic unit) but remain separate **lexical** words. The metrics stage must count lexical words for:

- `Total words` — the primary word count displayed to users
- `Syllables per word` — mean and std computed over lexical words
- `Morae per word` — mean and std computed over lexical words
- `Prominence candidates` — derived from `total_words`
- `WPM` — derived from `total_words`

The merge statistics (`Merged words`, `Merged units`, `Average unit size`) already correctly count lexical parts and should be preserved as-is.

---

## Scope

### Included

- Modify `analyze_text()` in `src/akkapros/lib/_metrics_stats.py` to split merged words into lexical parts before computing word-level statistics
- Update `syllables_per_word` and `morae_per_word` lists to contain one entry per lexical part
- Update `total_words` to count lexical parts
- Preserve syllable-level and mora-level statistics unchanged (they operate on individual syllables, not words)
- Preserve merge statistics unchanged (`count_merged_units()` already correctly counts lexical parts)
- Update `SMALL_SAMPLE_REFERENCE` in `tests/test_metrics_stats.py` to reflect new expected values
- Update the erra_construct demo reference metrics output

### Not Included

- Changing `extract_words()` or `build_word_pattern()` — the word pattern is correct for its purpose (matching prosodic units)
- Changing `count_merged_units()` — it already correctly counts lexical parts
- Changing `count_function_words()` or `extract_lexical_words()` in `frontmatter.py` — they already split on merge linkers
- Changing prominence statistics computation — only `total_words` input changes
- Changing phone-level or interval-level metrics — they operate on phone rows, not word counts

---

## Current Behavior

### How `analyze_text()` works

1. `extract_words(text, word_pattern)` returns merged words (e.g., `šar+gi·mir&dad~·mē` as one match)
2. `total_words = len(words)` — counts merged words, not lexical words
3. `syllables_per_word` and `morae_per_word` are computed per merged word
4. Merge statistics (`count_merged_units()`) correctly counts lexical parts

### Concrete example: erra_construct

Input tilde text:
```
šar+gi·mir&dad~·mē bā·nû kib·rā~·ti
```

Current output:
- `Total words: 4` (3 merged words + 1 space-separated word)
- Expected: `Total words: 5` (šar, gimir, dadmē, bānû, kibrāti)

### Concrete example: small corpus test

The `SMALL_SAMPLE_REFERENCE` in `tests/test_metrics_stats.py` currently expects `total_words: 22` for the sample text. After the fix, the sample text has 24 lexical words (because `˙i·na&˙i·lī` splits into 2 and `˙i·na&bi·rī~·šu·nu` splits into 2).

---

## Proposed Change

### In `analyze_text()`:

After building the `syllables_per_word` and `morae_per_word` lists from merged words, add a second pass that splits merged words into lexical parts and recomputes these lists.

**Algorithm:**

```
for each word in words:
    # First pass: classify syllables and build morae_list (unchanged)
    syllables = split word on ., -, +, &, ¨
    for each syllable:
        classify and count morae
        append to morae_list
        increment syllable_counts
    
    # Second pass: split into lexical parts for word-level stats
    lexical_parts = split word on + and &
    if len(lexical_parts) > 1:
        # Track syllable index within this word
        syl_idx = 0
        for each part in lexical_parts:
            part_syls = split part on ., -, ¨
            part_syl_count = count non-empty part_syls
            part_mora_count = sum(morae_list[syl_idx + i] for i in range(part_syl_count))
            append part_syl_count to syllables_per_word
            append part_mora_count to morae_per_word
            syl_idx += part_syl_count
    else:
        append word_syllable_count to syllables_per_word
        append word_mora_count to morae_per_word
```

**Key invariant:** `sum(morae_per_word) == sum(morae_list)` — the total morae must be preserved.

### Updated `total_words`:

`total_words = len(syllables_per_word)` (or `len(morae_per_word)`) — this now counts lexical parts.

---

## Technical Design

### Components

- `src/akkapros/lib/_metrics_stats.py` — `analyze_text()` function

### Algorithm details

The lexical splitting uses `WORD_LINKER` (`+`) and `INTERNAL_WORD_LINKER` (`&`) as separators. These are defined in `src/akkapros/lib/constants.py` as `MERGE_LINKERS`.

The syllable separator regex for splitting a lexical part is:
```python
re.split(rf'[\{SYL_SEPARATOR}\{HYPHEN}\{DIPH_SEPARATOR}]+', part)
```

Note: `WORD_LINKER` and `INTERNAL_WORD_LINKER` are NOT included in the part-level split — they were already consumed by the lexical split.

### Mora lookup

The mora for each syllable is already computed in the first pass and stored in `morae_list`. The lexical part's mora count is the sum of `morae_list[syl_idx + i]` for `i` in `range(part_syl_count)`, where `syl_idx` is the cumulative syllable index within the current word.

### Edge cases

- **Word with no merge linkers:** No change — single entry in `syllables_per_word` and `morae_per_word`
- **Word with only `+`:** e.g., `šar+gi·mir` → 2 lexical parts
- **Word with only `&`:** e.g., `˙i·na&˙i·lī` → 2 lexical parts
- **Word with both `+` and `&`:** e.g., `šar+gi·mir&dad~·mē` → 3 lexical parts
- **Empty lexical part:** Should not occur in valid input, but guard with `if not part.strip(): continue`

---

## Files Likely Affected

- `src/akkapros/lib/_metrics_stats.py` — `analyze_text()` function
- `tests/test_metrics_stats.py` — `SMALL_SAMPLE_REFERENCE` values
- `demo/akkapros/lexlinks/results/erra_construct_metrics.txt` — reference output

---

## Acceptance Criteria

- [x] Given a tilde text with merged words (containing `+` or `&`), when `analyze_text()` is called, then `total_words` equals the count of lexical parts (not merged words)
- [x] Given a tilde text with merged words, when `analyze_text()` is called, then `sum(morae_per_word) == sum(morae_list)` (total morae preserved)
- [x] Given a tilde text with merged words, when `analyze_text()` is called, then `len(syllables_per_word) == len(morae_per_word) == total_words`
- [x] Given a tilde text without merge linkers, when `analyze_text()` is called, then all word-level statistics are unchanged
- [x] Given the small corpus sample text, when `analyze_text()` is called, then `total_words == 24` (was 22)
- [x] Given the erra_construct sample (`šar+gi·mir&dad~·mē bā·nû kib·rā~·ti`), when `analyze_text()` is called, then `total_words == 5` (was 4)
- [x] Given the small corpus sample text, when `analyze_text()` is called, then `morae_per_word mean == total_morae / total_words` (formula consistency preserved)
- [x] Given the small corpus sample text, when `analyze_text()` is called, then `syllables_per_word mean == total_syllables / total_words` (formula consistency preserved)
- [x] Merge statistics (`count_merged_units()`) are unchanged

---

## Risks / Edge Cases

- **Test reference values must be updated:** `SMALL_SAMPLE_REFERENCE` in `tests/test_metrics_stats.py` has hardcoded `total_words: 22`, `syllables_per_word mean: 2.727...`, `morae_per_word mean: 4.545...`. These must be recomputed.
- **Demo reference output must be updated:** `demo/akkapros/lexlinks/results/erra_construct_metrics.txt` has `Total words: 4` which must become `Total words: 5`.
- **Prominence statistics will shift:** `prominence_candidate_word_count` is derived from `total_words`. The erra_construct example will change from `Prominence candidates: 3` to `Prominence candidates: 4` (5 total - 0 function - 1 explicit link).
- **WPM will shift:** `WPM` is derived from `total_words`. The erra_construct example will change from `48.48` to `60.61` (5/4 * 48.48).

---

## Testing Strategy

### Unit tests

- Test `analyze_text()` with a text containing `+` and `&` merged words, verify `total_words` equals lexical count
- Test `analyze_text()` with a text without merge linkers, verify no regression
- Test formula consistency: `morae_per_word mean == total_morae / total_words`
- Test formula consistency: `syllables_per_word mean == total_syllables / total_words`

### Integration tests

- Run `test_small_corpus_metrics_formula_consistency` — it should pass after updating `SMALL_SAMPLE_REFERENCE`
- Run the fullprosmaker pipeline on the erra_construct demo and verify metrics output

### Manual verification

- For `šar+gi·mir&dad~·mē bā·nû kib·rā~·ti`:
  - Lexical words: šar (1 syl, 1 mora), gimir (2 syls, 2 morae), dadmē (2 syls, 3 morae), bānû (2 syls, 4 morae), kibrāti (3 syls, 4 morae)
  - Total: 5 words, 10 syllables, 14 morae
  - Mean syllables/word: 2.0
  - Mean morae/word: 2.8

---

## Rollback Plan

Revert changes to `analyze_text()` in `_metrics_stats.py` and restore `SMALL_SAMPLE_REFERENCE` to previous values.

---

## Related Issues

- CR-056: Broaden Metrics Coverage to High-Confidence Indicator Verification (umbrella for metrics confidence)
- CR-020: Metrics Word Stats Lex Input (previous word-count related work)

---

## Tasks

### Implementation

- [x] Modify `analyze_text()` in `_metrics_stats.py` to split merged words into lexical parts
- [x] Update `total_words` to count lexical parts
- [x] Update `syllables_per_word` and `morae_per_word` to contain one entry per lexical part

### Tests

- [x] Update `SMALL_SAMPLE_REFERENCE` in `tests/test_metrics_stats.py`
- [x] Verify formula consistency tests pass
- [x] Add test for erra_construct-style input

### Documentation

- [x] Update demo reference output in `demo/akkapros/lexlinks/results/erra_construct_metrics.txt`

### Review

- [x] Verify all acceptance criteria
- [x] Run full test suite

---

## Implementation Blockers

None currently.

---

## Notes

### Code inspection results

The current `analyze_text()` at line 585-729 of `_metrics_stats.py`:

1. Extracts words via `extract_words(text, word_pattern)` — returns merged words
2. For each word, splits syllables on `[.\\-+&¨]+` and classifies each syllable
3. Appends `word_syllable_count` and `word_mora_count` to `syllables_per_word` and `morae_per_word`
4. Sets `total_words = len(words)` — this is the bug

The `count_merged_units()` function at line 373-398 already correctly counts lexical parts:
```python
for word in words:
    if any(linker in word for linker in MERGE_LINKERS):
        merged_units += 1
        total_merged_words += sum(word.count(linker) for linker in MERGE_LINKERS) + 1
```

The `extract_lexical_words()` function in `frontmatter.py` at line 699-714 already correctly splits on merge linkers:
```python
for piece in MERGE_LINKER_RE.split(token):
    if any(ch in AKKADIAN_LETTERS for ch in piece):
        words.append(piece)
```

### Affected reference values (small corpus)

Current `SMALL_SAMPLE_REFERENCE`:
- `total_words: 22` → should be `24`
- `syllables_per_word mean: 2.727...` → should be `2.5` (60/24)
- `morae_per_word mean: 4.545...` → should be `4.166...` (100/24)

### Affected reference values (erra_construct)

Current output:
- `Total words: 4` → should be `5`
- `Syllables per word: 2.500 ± 0.577` → should be `2.000 ± 0.707`
- `Prominence candidates: 3` → should be `4`
- `WPM: 48.48` → should be `60.61`
- `Mean morae per word: 4.500 ± 0.577` → should be `2.800 ± 1.304`
