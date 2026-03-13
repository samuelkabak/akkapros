"""Generate diphthong replacement patterns from a two-vowel specification.

This module implements the rules and code used to restore diphthongs after
syllabification and repair. The syllabifier inserts an explicit separator
between adjacent vowels (controlled by `SYL_SEPARATOR` and
`DIPH_SEPARATOR`) so that the repair stage can operate on distinct syllables.
After repair, vowel pairs that originally formed diphthongs must be
reconstructed from the repaired output; this module generates the
regular-expression replacement patterns used to perform that reconstruction.

Key points
- The generator enumerates all pairs of base vowels (a, i, u, e) and all
    relevant forms for each vowel: short, long, and circumflex (circ). The
    second vowel may also carry a tilde (``~``) that marks a repaired/moraic
    lengthening.
- Replacement logic distinguishes two cases: "same vowel" (e.g. a + a)
    versus "different vowels" (e.g. u + a). Each case has deterministic rules
    that encode (a) how circumflex forms win, (b) when a tilde must be preserved,
    and (c) whether the result carries a tilde.
- Patterns where the *second* vowel has a tilde are emitted first to avoid
    regex clashes (longer / more specific matches must be applied before
    shorter ones).
- The generator groups identical replacements into alternations and sorts
    by pattern length so the produced list is efficient and unambiguous.

Public behavior
- `generate_diphthongs_file(filename)` writes a file (by default
    ``diphthongs.py``) that contains ``ALL_REPLACEMENTS`` — an ordered list of
    (regex, replacement) tuples. That output is consumed by the restoration
    stage of the pipeline to convert diæresis-separated vowel pairs back into
    canonical diphthong forms.

Implementation notes (mapping to functions)
- `_char(base, form)` : map a base vowel and a form token (``short``,
    ``long``, ``circ``, or variants that include ``~``) to the actual character
    sequence used in patterns.
- `_same_vowel_replacement(...)` and
    `_different_vowel_replacement(...)` : implement the rule sets for same vs
    different vowel pairs respectively. These encode precedence for circumflex
    forms and the conditions under which a tilde is preserved or introduced.
- `_build_entries()` : enumerate all combinations and produce raw
    (pattern, replacement, second_has_tilde) tuples.
- `_combine_entries()` : group patterns with identical replacements, build
    alternations, and sort so that second-tilde patterns come first.

Why this is necessary
---------------------
The syllabifier expands diphthongs into two vowel units (often inserting a
glottal marker) so that mora-counting and repair can operate deterministically.
Once repairs (lengthenings/gemination) are applied, the original diphthong
shapes must be reconstructed from the repaired tokens while preserving any
tilde marks that indicate added morae. This generator codifies the
phonologically motivated mapping between repaired vowel pairs and the final
orthographic diphthong forms.

See docs/diphthong-processing.md for a human-readable explanation and
examples of the rule set and how it maps to code.
"""

from collections import defaultdict
from pathlib import Path

from akkapros.lib.constants import SYL_SEPARATOR
from akkapros.lib.constants import DIPH_SEPARATOR


BASES = ('a', 'i', 'u', 'e')
VOWELS = {
    'a': {'short': 'a', 'long': 'ā', 'circ': 'â'},
    'i': {'short': 'i', 'long': 'ī', 'circ': 'î'},
    'u': {'short': 'u', 'long': 'ū', 'circ': 'û'},
    'e': {'short': 'e', 'long': 'ē', 'circ': 'ê'},
}

FIRST_FORMS = ('short', 'long', 'circ')
SECOND_FORMS = ('short', 'long', 'circ', 'long~', 'circ~')

# Diphthong splitter inserted by syllabifier between adjacent vowels.


def _char(base: str, form: str) -> str:
    if form == 'short':
        return VOWELS[base]['short']
    if form == 'long':
        return VOWELS[base]['long']
    if form == 'circ':
        return VOWELS[base]['circ']
    if form == 'long~':
        return VOWELS[base]['long'] + '~'
    if form == 'circ~':
        return VOWELS[base]['circ'] + '~'
    raise ValueError(f"Unknown vowel form: {form}")


def _is_circ(form: str) -> bool:
    return form.startswith('circ')


def _is_long(form: str) -> bool:
    return form.startswith('long')


def _has_second_tilde(second_form: str) -> bool:
    return second_form.endswith('~')


def _same_vowel_replacement(base: str, first_form: str, second_form: str) -> str:
    second_tilde = _has_second_tilde(second_form)

    if second_tilde:
        # e.g. a.ʾā~ -> ā ; ā.ʾâ~ -> â~
        second_core = second_form[:-1]
        if first_form == 'short':
            return _char(base, second_core)
        out_core = 'circ' if (_is_circ(first_form) or _is_circ(second_core)) else 'long'
        return _char(base, out_core) + '~'

    # no tilde on second
    if second_form == 'short':
        # e.g. a.ʾa -> â ; ā.ʾa -> ā~ ; â.ʾa -> â~
        if first_form == 'short':
            return _char(base, 'circ')
        if first_form == 'long':
            return _char(base, 'long') + '~'
        return _char(base, 'circ') + '~'

    # second is long or circ
    if first_form == 'short':
        # e.g. a.ʾā -> ā~ ; a.ʾâ -> â~
        return _char(base, second_form) + '~'

    # e.g. ā.ʾā -> ā ; ā.ʾâ -> â ; â.ʾā -> â
    out_core = 'circ' if (_is_circ(first_form) or _is_circ(second_form)) else 'long'
    return _char(base, out_core)


def _different_vowel_replacement(base1: str, base2: str, first_form: str, second_form: str) -> str:
    second_tilde = _has_second_tilde(second_form)

    if second_tilde:
        second_core = second_form[:-1]
        if first_form == 'short':
            # e.g. u.ʾā~ -> uā~ ; u.ʾâ~ -> uâ~
            return base1 + _char(base2, second_core) + '~'
        # e.g. ū.ʾā~ -> uā ; û.ʾā~ -> uâ
        out2 = 'circ' if (_is_circ(first_form) or _is_circ(second_core)) else 'long'
        return base1 + _char(base2, out2)

    # no tilde on second
    if second_form == 'short':
        if first_form == 'short':
            # e.g. u.ʾa -> ua
            return base1 + base2
        if first_form == 'long':
            # e.g. ū.ʾa -> uā
            return base1 + _char(base2, 'long')
        # e.g. û.ʾa -> uâ
        return base1 + _char(base2, 'circ')

    if first_form == 'short':
        # e.g. u.ʾā -> uā ; u.ʾâ -> uâ
        return base1 + _char(base2, second_form)

    # first is long/circ, second is long/circ
    out2 = 'circ' if (_is_circ(first_form) or _is_circ(second_form)) else 'long'
    if first_form == 'circ' and second_form == 'long':
        # per provided example: û.ʾā -> uâ (circ wins, no tilde)
        return base1 + _char(base2, out2)

    # e.g. ū.ʾā -> uā~ ; û.ʾâ -> uâ~ ; ū.ʾâ -> uâ~
    return base1 + _char(base2, out2) + '~'


def _replacement(base1: str, base2: str, first_form: str, second_form: str) -> str:
    if base1 == base2:
        return _same_vowel_replacement(base1, first_form, second_form)
    return _different_vowel_replacement(base1, base2, first_form, second_form)


def _build_entries():
    entries = []
    for base1 in BASES:
        for base2 in BASES:
            for first_form in FIRST_FORMS:
                for second_form in SECOND_FORMS:
                    v1 = _char(base1, first_form)
                    v2 = _char(base2, second_form)
                    pattern = rf"{v1}{SYL_SEPARATOR}{DIPH_SEPARATOR}{v2}"
                    repl = _replacement(base1, base2, first_form, second_form)
                    entries.append((pattern, repl, _has_second_tilde(second_form)))
    return entries


def _combine_entries(entries):
    grouped = defaultdict(list)
    for pattern, repl, second_tilde in entries:
        grouped[(second_tilde, repl)].append(pattern)

    combined = []
    for (second_tilde, repl), patterns in grouped.items():
        uniq = sorted(set(patterns), key=lambda p: (-len(p), p))
        if len(uniq) == 1:
            regex = uniq[0]
        else:
            regex = '(?:' + '|'.join(uniq) + ')'
        combined.append((regex, repl, second_tilde))

    # IMPORTANT: second-vowel-tilde patterns first to avoid clashes.
    combined.sort(key=lambda x: (0 if x[2] else 1, -len(x[0]), x[1], x[0]))
    return combined


def generate_diphthongs_file(filename: str = 'diphthongs.py'):
    entries = _build_entries()
    combined = _combine_entries(entries)

    out = Path(filename)
    with out.open('w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('Diphthong replacement patterns for all vowel combinations.\n')
        f.write('Generated from _gen_diphthongs.py using two-vowel spec rules.\n')
        f.write('Order matters: patterns with tilde on SECOND vowel come first.\n')
        f.write('Generated automatically - DO NOT EDIT MANUALLY\n')
        f.write('"""\n\n')

        f.write('ALL_REPLACEMENTS = [\n')
        f.write('    # ===== SECOND VOWEL WITH TILDE (must run first) =====\n')
        second_done = False
        for regex, repl, second_tilde in combined:
            if (not second_tilde) and (not second_done):
                f.write('\n    # ===== SECOND VOWEL WITHOUT TILDE =====\n')
                second_done = True
            f.write(f"    (r'{regex}', '{repl}'),\n")
        f.write(']\n\n')
        f.write("__all__ = ['ALL_REPLACEMENTS']\n")

    second_count = sum(1 for _, _, s in combined if s)
    plain_count = len(combined) - second_count
    print(f'Generated {len(combined)} combined regex rules in {out}')
    print(f'  - second vowel with tilde: {second_count}')
    print(f'  - second vowel without tilde: {plain_count}')


if __name__ == '__main__':
    generate_diphthongs_file(Path(__file__).with_name('diphthongs.py'))