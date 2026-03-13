Diphthong Processing Workflow
=============================

Overview
--------
This document explains how diphthongs are handled by the Akkapros pipeline: how
they are split for syllabification, prosody-realized (if necessary), and restored back
into canonical diphthong forms. The implementation lives in
`src/akkapros/lib/_gen_diphthongs.py` and the generated replacement table is
written to `src/akkapros/lib/diphthongs.py` (via
`generate_diphthongs_file()`).

Why split diphthongs?
---------------------
To compute mora counts and apply moraic repairs, the syllabifier must treat
adjacent vowels as separate syllables. The syllabifier therefore inserts an
explicit separator between adjacent vowels (the module constants
`SYL_SEPARATOR` and `DIPH_SEPARATOR`), making sequences like â€œuÊ¾aâ€ or
â€œaÊ¾Ä~â€ unambiguous for the prosody realization algorithm.

After prosody realization, those two-vowel sequences must be mapped back to the correct
orthographic diphthong (e.g. `uÄ`, `uÃ¢`, `ua`, `uÄ~`, etc.). The mapping is
not trivial: it depends on vowel quality (short/long/circumflex), whether the
second vowel carries a tilde (``~``), and interactions where circumflex
forms take precedence.

High-level pipeline
-------------------
1. Syllabify: the syllabifier inserts `SYL_SEPARATOR + DIPH_SEPARATOR` between
   adjacent vowels (or an equivalent marker sequence used by the codebase).
2. prosody realization: the prosody realization stage may lengthen vowels or add tilde markers to signal
   added morae; it operates on the separated syllables.
3. Restore: once prosody realization is complete, a set of regex replacements is applied to
   convert the separated vowel pairs into final diphthong forms.

Rules summary
-------------
- Two main cases are handled: same-base vowel pairs (a+a, i+i, ...) and
  different-base pairs (u+a, a+i, etc.).
- If the second vowel has a tilde, those patterns are matched first to avoid
  shorter patterns shadowing longer, more specific ones.
- Circumflex forms (``circ``) take precedence where specified; the mapping
  chooses the circumflex when either side requires it according to the rule
  set.
- The result may carry a tilde depending on the interaction between the forms
  (e.g., a short first vowel + long/circ second with tilde -> result keeps
  tilde; other combinations may remove or add tilde).

Implementation mapping to code
------------------------------
- `_char(base, form)` : returns the character(s) for a vowel base and form
  token: `short`, `long`, `circ`, and the ``~`` variants (``long~``,
  ``circ~``).
- `_same_vowel_replacement(base, first_form, second_form)` : rules when both
  vowels share the same base.
- `_different_vowel_replacement(base1, base2, first_form, second_form)` : rules
  for mixed base pairs.
- `_replacement(base1, base2, first_form, second_form)` : convenience wrapper
  that dispatches to the appropriate function.
- `_build_entries()` : enumerates all combinations of bases and forms and
  produces raw (pattern, replacement, second_has_tilde) tuples.
- `_combine_entries(entries)` : groups patterns with identical replacements,
  builds alternations, and sorts entries so second-tilde patterns are first.
- `generate_diphthongs_file(filename)` : writes the final `ALL_REPLACEMENTS`
  list into the specified file.

Practical examples
------------------
Here are representative mappings (informal):

- Same-base examples (a + a):
  - `a.SEP.Ê¾Ä~` -> `Ä`        (short + long~ -> long without tilde)
  - `Ä.SEP.Ê¾Ã¢~` -> `Ã¢~`       (long + circ~ -> circ with tilde)
  - `a.SEP.Ê¾a` -> `Ã¢`         (short+short -> circumflex)

- Mixed-base examples (u + a):
  - `u.SEP.Ê¾Ä~` -> `uÄ~`      (short u + long~ a -> uÄ~)
  - `Å«.SEP.Ê¾Ä~` -> `uÄ`       (long Å« + long~ a -> uÄ)
  - `u.SEP.Ê¾a` -> `ua`        (short u + short a -> ua)

Note: `SEP` above stands in for the actual `SYL_SEPARATOR + DIPH_SEPARATOR`
sequence produced during syllabification.

Regenerating the replacement file
---------------------------------
To regenerate `diphthongs.py` from the generator, run the generator as a
script. From the repository root:

```bash
python src/akkapros/lib/_gen_diphthongs.py
```

This will write `diphthongs.py` next to the generator and print a summary of
how many combined regex rules were generated (counts for second-tilde vs
plain patterns).

Notes & cautions
----------------
- The generator produces regex patterns; the restoration stage must apply them
  using the same regex flavor and with the same notion of separators.
- The ordering of patterns is important: always apply second-tilde patterns
  first to prevent incorrect substitutions.
- If vowel inventories or form tokens are extended, update both the generator
  (`BASES`, `VOWELS`, `FIRST_FORMS`, `SECOND_FORMS`) and tests that cover the
  new combinations.

Further reading
---------------
- See `src/akkapros/lib/_gen_diphthongs.py` for the implementation.
- See `src/akkapros/lib/diphthongs.py` for the generated
  `ALL_REPLACEMENTS` table used at runtime.

Changelog
---------
Created: 2026-03-13 â€” initial documentation describing generation rules and
how the restoration fits into the syllabify/prosody realization pipeline.


