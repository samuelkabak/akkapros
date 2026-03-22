# `lib/utils.py` — Contributor Reference

**Module**: `akkapros.lib.utils`  
**Version**: 1.0.1  
**Location**: `src/akkapros/lib/utils.py`

This document describes every public function in `lib/utils.py` for
contributors who need to extend, debug, or consume them.

---

## Overview

`utils.py` is the canonical home for small, shared helpers that are
used by multiple pipeline modules.  It has **no runtime dependencies**
beyond the Python standard library plus `akkapros.lib.constants`.

Key groupings:

| Group | Functions |
|-------|-----------|
| Filename utilities | `simple_safe_filename` |
| CLI helpers | `print_startup_banner`, `add_standard_version_argument`, `RawDefaultsHelpFormatter` |
| Contextual regex | `compile_contextual_regex`, `contextualize_for_regex`, `strip_regex_sentinels`, `build_numeric_currency_pattern` |
| Format validation | `FormatValidationError`, `validate_intermediate_format` |
| Akkadian scoring | `akkadian_likelihood`, `classify_text` |
| Self-test harness | `run_tests` |

---

## Function Reference

### `simple_safe_filename(text: str) -> str`

Converts arbitrary text to a minimal filesystem-safe filename fragment.

Steps (in order):
1. NFKD-normalize and strip accent marks.
2. Replace filename-illegal chars and whitespace with `_`.
3. Remove remaining non-word chars (keeps `-` and `.`).
4. Collapse consecutive `_`, strip leading/trailing `._-`.
5. Return `"unnamed"` if the result is empty.

```python
simple_safe_filename('foo/bar baz?')  # → 'foo_bar_baz'
simple_safe_filename('')              # → 'unnamed'
```

**Why it exists**: Previously every CLI module had its own variation.
This single version is the canonical one (see CR-010).

---

### `print_startup_banner(program_title, version, args)`

Prints a stable, predictable banner at startup listing all effective
CLI parameters.  Used at the top of every CLI `main()` for reproducibility.

---

### `add_standard_version_argument(parser, tool_name)`

Attaches a `--version`/`-v` flag to an `argparse.ArgumentParser` that
prints the full multi-line version string from `get_version_display()`.

---

### `compile_contextual_regex(pattern, option_name, item_index) -> re.Pattern`

Compiles a user-supplied regex string after expanding the
`[:bol:]` / `[:eol:]` pseudo-tokens into internal sentinels
(`<<BOL>>` / `<<EOL>>`).  Raises `ValueError` on invalid regex.

The pseudo-token system allows users to write `[:bol:]word` instead of
the sentinel-heavy form `<<BOL>>word`.

---

### `contextualize_for_regex(text, *, at_sol, at_eol, at_eof) -> str`

Prepends `<<BOL>>` and/or appends `<<EOL>>` to a text fragment so that
contextual regex patterns compiled with `compile_contextual_regex` match
correctly at line/file boundaries.

---

### `strip_regex_sentinels(text: str) -> str`

Removes `<<BOL>>` and `<<EOL>>` sentinels from text after matching.

---

### `build_numeric_currency_pattern(*, number_pattern, currency_symbols) -> re.Pattern`

Returns a compiled regex that matches:
- `$42`, `€ 1,000.50` (currency symbol before number)
- `42 €`, `1,000.50$` (currency symbol after number)
- bare numbers

Used by the punctuation-whitelist system for financial text.

---

### `FormatValidationError(ValueError)`

Structured exception for pipeline format failures.  Attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `source` | `str` | File path |
| `reason` | `str` | Human-readable failure description |
| `line_number` | `int\|None` | First offending line (1-based), if known |
| `line_text` | `str\|None` | Content of the offending line |

The `str()` representation is formatted as:  
`<path>: [line N: ]<reason>[ | line content: '<text>']`

---

### `validate_intermediate_format(file_path, expected_kind) -> None`

Validates an input file before it enters a pipeline stage.

`expected_kind` must be one of `"atf"`, `"proc"`, `"syl"`, `"tilde"`.

| Check | All kinds | `atf` | `proc` | `syl` | `tilde` |
|-------|-----------|-------|--------|-------|---------|
| File exists and readable | ✓ | | | | |
| Not empty / not binary | ✓ | | | | |
| Valid UTF-8 | ✓ | | | | |
| No unprintable control chars | ✓ | | | | |
| Contains Akkadian letters | ✓ | | | | |
| Has `%n` content lines | | ✓ | | | |
| No raw ATF markup | | | ✓ | | |
| Likelihood guard (≥ 0.25, file ≥ 50 chars) | | | ✓ | | |
| Has `¦` word-ending markers | | | | ✓ | |
| No `¦` markers (wrong stage) | | | | | ✓ |

#### Likelihood guard (`proc` only)

For files longer than 50 stripped characters, `validate_intermediate_format`
calls `akkadian_likelihood(text, min_length=10)` and raises
`FormatValidationError` if the score is below `_VALIDATE_PROC_THRESHOLD`
(0.25 by default).

**Why only `proc`?**  Syllabified (`syl`) and accentuated (`tilde`) files
use dot-separated syllable notation (`ki.bab.ti¦`).  Word tokens are
sub-syllabic fragments that do not match the function-word set, causing
false-negative scores even for valid Akkadian text.  The check is
therefore restricted to the clean transliteration stage.

**To adjust the threshold or minimum length**, change the module-level
constants `_VALIDATE_PROC_THRESHOLD` and `_VALIDATE_PROC_MIN_CHARS` in
`utils.py`.

---

### `akkadian_likelihood(text, min_length=10) -> tuple[float, dict]`

Computes a `[0.0, 1.0]` likelihood that *text* is Akkadian transliteration.

#### Algorithm

Four-component weighted score:

```
score = 0.40 × distinctive_score
      + 0.20 × vowel_consonant_score
      + 0.30 × function_word_score
      + 0.10 × length_bonus
```

| Component | What it measures | How computed |
|-----------|-----------------|--------------|
| `distinctive` | Presence of chars only in Akkadian (`š`, `ṭ`, `ṣ`, `ḥ`, `ḫ`, `ʿ`, `ʾ`) | `ratio × 3`, capped at 1 |
| `vowel_consonant` | V/C ratio in the ideal Akkadian range 0.3–0.8 | 1.0 / 0.7 / 0.3 step function |
| `function_words` | Fraction of tokens that are known function words or enclitic-bearing | Ratio in ideal 0.25–0.6 with count bonus |
| `length` | Longer texts give more reliable estimates | `len / 500`, capped at 0.2 |

#### Short-text handling

Texts with fewer than `min_length` phonetic characters bypass the full
analysis and receive `0.5 × (len / min_length)`, giving a low but
non-zero score.

#### Zero scores

A score of exactly **0.0** means a character from `NON_AKKADIAN_CHARS`
(`o`, `f`, `x`, `v`, `j`, `c`) was found.  These characters cannot
appear in proper Akkadian transliteration.

#### Returns

`(score: float, details: dict)` where `details` contains:

| Key | Type | Description |
|-----|------|-------------|
| `length` | `int` | Character count after stripping punctuation |
| `has_non_akkadian` | `bool` | True if a forbidden char was found |
| `distinctive_count` | `int` | Count of distinctively-Akkadian characters |
| `vowel_count` | `int` | Akkadian vowel count |
| `consonant_count` | `int` | Akkadian consonant count |
| `function_word_matches` | `float` | Sum of full (1.0) + half (0.5) function-word / enclitic matches |
| `total_words` | `int` | Total tokens in the text |
| `function_word_ratio` | `float` | `function_word_matches / max(1, total_words)` |
| `scores` | `dict` | Per-component scores (`distinctive`, `vowel_consonant`, `function_words`, `length_bonus`) |
| `text_sample` | `str` | First 100 chars of the input (for diagnostics) |
| `confidence_penalty` | `float` | Only present for short texts; `len / min_length` |

#### Classification cut-offs (`AKKASCORE_THRESHOLDS`)

| Label | Score range |
|-------|-------------|
| HIGHLY LIKELY AKKADIAN | ≥ 0.75 |
| LIKELY AKKADIAN | ≥ 0.50 |
| POSSIBLY AKKADIAN | ≥ 0.25 |
| UNLIKELY AKKADIAN | < 0.25 |
| NOT AKKADIAN | = 0.0 (forbidden char) |

#### Constants driving the algorithm

All are module-level in `utils.py`, prefixed `_AKKASCORE_*`.  To tune
the scorer for a different application, adjust these without touching
the function body:

```python
_AKKASCORE_WEIGHTS          # component weights
_AKKASCORE_VOWEL_IDEAL      # V/C ideal range
_AKKASCORE_VOWEL_ACCEPTABLE # V/C acceptable range
_AKKASCORE_FW_IDEAL         # function-word ratio ideal range
_AKKASCORE_FW_ACCEPTABLE    # function-word ratio acceptable range
_AKKASCORE_DISTINCTIVE_MUL  # scale factor for distinctive ratio
_AKKASCORE_FW_BONUS_DENOM   # denominator for raw count bonus
_AKKASCORE_FW_BONUS_MAX     # cap on count bonus
_AKKASCORE_LEN_BONUS_DENOM  # denominator for length bonus
_AKKASCORE_LEN_BONUS_MAX    # cap on length bonus
_AKKASCORE_MIN_LENGTH       # short-text threshold
_AKKASCORE_BASE_SHORT       # base score for short texts
```

#### Limitations

The scorer was designed for clean `*_proc.txt` content (plain
transliteration, word-separated).  It gives **unreliable** results on:

- Syllabified text (`*_syl.txt`) — sub-syllabic tokens break function-word matching
- Tilde pivot text (`*_tilde.txt`) — same issue
- Raw ATF (`*_orig.txt`) — contains markup and logogram notation
- Very short excerpts (< 10 chars) — only confidence-penalised estimate
- Texts with no distinctive Akkadian characters and no function words —
  score ≈ 0.14–0.25 even if genuinely Akkadian

For pipeline validation use `validate_intermediate_format()`, which
applies the guard only where appropriate.

---

### `classify_text(text: str) -> str`

Convenience wrapper around `akkadian_likelihood`.  Returns one of the
five string labels shown in the table above.  Useful for quick
interactive or CLI-level diagnostics.

---

### `run_tests() -> bool`

Self-test harness.  Tests `simple_safe_filename` (correctness) and basic
smoke tests for `akkadian_likelihood` (score range, forbidden char
detection, function-word recognition, short-text penalty).

Called as part of `tests/test_selftests_lib.py`; also runnable directly:

```python
from akkapros.lib.utils import run_tests
run_tests()
```

---

## Extending the Akkadian Scorer

### Add a new function word

Add to `FUNCTION_WORDS` in `src/akkapros/lib/constants.py`.  The set is
shared with `lib/prosody.py` (used for merge decisions) — check that the
new entry does not conflict with prosody logic before adding.

### Add a new enclitic

Add to `AKKADIAN_ENCLITICS` in `src/akkapros/lib/constants.py`.  Keep
entries short (2–4 chars) to minimise false matches from the suffix
check.  Add a corresponding test case in
`tests/test_akkadian_likelihood.py`.

### Adjust scoring weights

Change `_AKKASCORE_WEIGHTS` in `utils.py`.  The values must sum to 1.0.
Run `utils.run_tests()` and the full test suite after any adjustment.

---

## Related ADRs and Specs

| Doc | Relevance |
|-----|-----------|
| [ADR-001](../internal/adr/001-cli-lib-separation.md) | lib/ vs cli/ separation |
| [ADR-009](../internal/adr/009-function-word-and-merge-policy.md) | `FUNCTION_WORDS` canonical definition |
| [CR-013](../internal/cr/013-migrate-akkascore-to-utils.md) | Migration from `akkascore.py` |
| [SPEC-010](../internal/specs/010-built-in-self-tests-and-test-infrastructure.md) | Self-test infrastructure |
