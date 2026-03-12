"""Generate diphthong regex replacements from two-vowel spec rules.

Diphthongs are a challenge to syllabificaiton.

To make it easy, the syllabier inserts a special separator between adjacent 
vowels, and after reparation we apply regex replacements to convert these into 
the correct diphthong forms.

Rules are derived below
- two cases: same vowel vs different vowels
- second vowel with tilde MUST be emitted first to avoid regex clashes
- circumflex wins where specified

Examples with vowels a and u

1) same vowel, example a
(r'a\.ʾā~', 'ā'), # 4 -> 2
(r'a\.ʾâ~', 'â'),  # 4 -> 2
(r'ā\.ʾā~', 'ā~'),  # 5 -> 3
(r'â\.ʾâ~', 'â~'),  # 5 -> 3
(r'ā\.ʾâ~', 'â~'),  # 5 -> 3 curcumflex win
(r'â\.ʾā~', 'â~'),  # 5 -> 3 curcumflex win
(r'a\.ʾā', 'ā~'), #  3 remains
(r'a\.ʾâ', 'â~'),  # 3 remains
(r'ā\.ʾā', 'ā'),  # 4 -> 2
(r'â\.ʾâ', 'â'),  # 4 -> 2
(r'ā\.ʾâ', 'â'),  # 4 -> 2 curcumflex win
(r'â\.ʾā', 'â'),  # 4 -> 2 curcumflex win
(r'a\.ʾa', 'â'),  # 2 remains curcumflex forced

When we have two different vowels, lets say the first is u and teh second is a

(r'u\.ʾā~', 'uā~'), # 4 remains
(r'u\.ʾâ~', 'uâ~'),  # 4 remains
(r'ū\.ʾā~', 'uā'),  # 5 -> 3
(r'û\.ʾâ~', 'uâ'),  # 5 -> 3
(r'ū\.ʾâ~', 'uâ'),  # 5 -> 3 curcumflex win
(r'û\.ʾā~', 'uâ'),  # 5 -> 3 curcumflex win
(r'u\.ʾā', 'uā'), #  3 remains
(r'u\.ʾâ', 'uâ'),  # 3 remains
(r'ū\.ʾā', 'uā~'),  # 4 remains
(r'û\.ʾâ', 'uâ~'),  # 4 remains
(r'ū\.ʾâ', 'uâ~'),  # 4 remains curcumflex win
(r'û\.ʾā', 'uâ'),  # 4 remains  curcumflex win
(r'u\.ʾa', 'ua'),  # 2

Optimized by grouping patterns with same replacement and second vowel tilde 
status, and sorting by length to ensure longest match first.

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