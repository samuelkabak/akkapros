"""Generate diphthong replacement patterns from a two-vowel specification.

This module is a code generator. It emits the runtime lookup table used by
`akkapros.lib.prosody` to restore diphthongs after syllabification and
accentuation.
"""

from collections import defaultdict
from pathlib import Path

from akkapros.lib.constants import DIPH_SEPARATOR
from akkapros.lib.constants import SYL_SEPARATOR


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
        second_core = second_form[:-1]
        if first_form == 'short':
            return _char(base, second_core)
        out_core = 'circ' if (_is_circ(first_form) or _is_circ(second_core)) else 'long'
        return _char(base, out_core) + '~'

    if second_form == 'short':
        if first_form == 'short':
            return _char(base, 'circ')
        if first_form == 'long':
            return _char(base, 'long') + '~'
        return _char(base, 'circ') + '~'

    if first_form == 'short':
        return _char(base, second_form) + '~'

    out_core = 'circ' if (_is_circ(first_form) or _is_circ(second_form)) else 'long'
    return _char(base, out_core)


def _different_vowel_replacement(base1: str, base2: str, first_form: str, second_form: str) -> str:
    second_tilde = _has_second_tilde(second_form)

    if second_tilde:
        second_core = second_form[:-1]
        if first_form == 'short':
            return base1 + _char(base2, second_core) + '~'
        out2 = 'circ' if (_is_circ(first_form) or _is_circ(second_core)) else 'long'
        return base1 + _char(base2, out2)

    if second_form == 'short':
        if first_form == 'short':
            return base1 + base2
        if first_form == 'long':
            return base1 + _char(base2, 'long')
        return base1 + _char(base2, 'circ')

    if first_form == 'short':
        return base1 + _char(base2, second_form)

    out2 = 'circ' if (_is_circ(first_form) or _is_circ(second_form)) else 'long'
    if first_form == 'circ' and second_form == 'long':
        return base1 + _char(base2, out2)

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

    # Keep second-vowel-tilde patterns first to avoid regex shadowing.
    combined.sort(key=lambda x: (0 if x[2] else 1, -len(x[0]), x[1], x[0]))
    return combined


def _default_output_path() -> Path:
    return Path(__file__).resolve().parents[1] / 'lib' / 'diphthongs.py'


def generate_diphthongs_file(filename: str | Path | None = None) -> Path:
    entries = _build_entries()
    combined = _combine_entries(entries)

    out = Path(filename) if filename is not None else _default_output_path()
    with out.open('w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('Diphthong replacement patterns for all vowel combinations.\n')
        f.write('This file is autogenerated by src/akkapros/_gencode/lib_diphthongs.py\n')
        f.write('Do not edit directly.\n')
        f.write('Order matters: patterns with tilde on SECOND vowel come first.\n')
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
    return out


if __name__ == '__main__':
    generate_diphthongs_file()
