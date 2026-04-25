from __future__ import annotations

from typing import Dict, List, Union

from akkapros.lib._prosody_text import parse_syl_line, postprocess_restore_diphthongs, AccentStyle, MoraMode
from akkapros.lib.constants import DIPH_SEPARATOR, SYL_SEPARATOR, WORD_LINKER
from akkapros.lib.prosody_engine import ProsodyEngine
from akkapros.lib.prosody_model import Word
from akkapros.lib.utils import (
    format_selftest_label,
    get_logger_with_fallback,
    log_selftest_result,
    log_selftest_summary,
)


def test_diphthong_restoration() -> bool:
    logger = get_logger_with_fallback(__name__)

    def restore_one(text: str) -> str:
        return postprocess_restore_diphthongs([text])[0]

    test_cases = [
        (f'u{SYL_SEPARATOR}{DIPH_SEPARATOR}a', f'u{SYL_SEPARATOR}{DIPH_SEPARATOR}a', 'Simple short u+a keeps pivot hiatus markers'),
        (f'u{SYL_SEPARATOR}{DIPH_SEPARATOR}ā', f'u{SYL_SEPARATOR}{DIPH_SEPARATOR}ā', 'Short+long u+a keeps pivot hiatus markers'),
        (f'ū{SYL_SEPARATOR}{DIPH_SEPARATOR}a', f'u{SYL_SEPARATOR}{DIPH_SEPARATOR}ā', 'Long+short u+a preserves boundary while normalizing length'),
        (f'ū{SYL_SEPARATOR}{DIPH_SEPARATOR}ā', f'u{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~', 'Long+long u+a preserves boundary and accent'),
        (f'i{SYL_SEPARATOR}{DIPH_SEPARATOR}ē', f'i{SYL_SEPARATOR}{DIPH_SEPARATOR}ē', 'Different-vowel hiatus keeps separator'),
        (f'i{SYL_SEPARATOR}{DIPH_SEPARATOR}ē~', f'i{SYL_SEPARATOR}{DIPH_SEPARATOR}ē~', 'Different-vowel hiatus with accent keeps separator'),
        (f'a{SYL_SEPARATOR}{DIPH_SEPARATOR}a', 'â', 'Identical short vowels -> circumflex'),
        (f'a{SYL_SEPARATOR}{DIPH_SEPARATOR}a~', 'â~', 'Identical short+tilde -> circumflex+tilde'),
        (f'ku{SYL_SEPARATOR}{DIPH_SEPARATOR}a', f'ku{SYL_SEPARATOR}{DIPH_SEPARATOR}a', 'Consonant context preserved'),
        (f'ti{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~m{SYL_SEPARATOR}tu', f'ti{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~m{SYL_SEPARATOR}tu', 'Pivot example keeps clear syllable separation'),
        (f'ba{DIPH_SEPARATOR}ru', f'ba{DIPH_SEPARATOR}ru', 'Existing diphthong memory is preserved'),
        (f'ta{SYL_SEPARATOR}{DIPH_SEPARATOR}a ki', 'tâ ki', 'In-line restoration in phrase'),
    ]

    total = len(test_cases)
    passed = 0
    for i, (inp, expected, desc) in enumerate(test_cases, 1):
        result = restore_one(inp)
        label = format_selftest_label(i, total, desc)
        if result == expected:
            passed += 1
            log_selftest_result(logger, True, 'Diphthongs', label)
        else:
            log_selftest_result(
                logger,
                False,
                'Diphthongs',
                label,
                details=[f'input={inp!r}', f'expected={expected!r}', f'got={result!r}'],
            )

    log_selftest_summary(logger, 'Diphthongs', passed, total)
    return passed == total


def run_tests():
    logger = get_logger_with_fallback(__name__)

    test_cases = [
        {
            'name': 'Basic line with merge and accentuation',
            'input': 'šar¦gi·mir¦dad·mē¦bā·nû¦kib·rā·ti¦⟦ ···⟧',
            'expected': {
                'lob': 'šar gi·mir&dad~·mē bā·nû kib·rā~·ti⟦ ···⟧',
                'sob': 'šar gi·mir&dad~·mē bā·nû kib·rā~·ti⟦ ···⟧',
            },
        },
        {
            'name': 'Line with multiple accentuation operations',
            'input': 'ḫen·dur·san·ga¦a·pil¦el·lil¦rēš·tû¦⟦ ···⟧',
            'expected': {
                'lob': 'ḫen·dur·san~·ga a·pil&el~·lil rēš·tû~⟦ ···⟧',
                'sob': 'ḫen·dur·san~·ga a·pil&el~·lil rē~š·tû⟦ ···⟧',
            },
        },
        {
            'name': 'Function words merge forward with content',
            'input': 'u¦˙a·na¦šar·ri¦',
            'expected': {'lob': 'u&˙a·na&šar·ri', 'sob': 'u&˙a·na&šar·ri'},
        },
        {
            'name': 'Function word at end merges backward',
            'input': 'šar·ru¦u¦',
            'expected': {'lob': 'šar·ru&u', 'sob': 'šar·ru&u'},
        },
        {
            'name': 'Word with final superheavy',
            'input': 'rēš·tû¦',
            'expected': {'lob': 'rēš·tû~', 'sob': 'rē~š·tû'},
        },
        {
            'name': 'Multiple function words with content',
            'input': 'u¦˙a·na¦˙i·na¦šar·ri¦',
            'expected': {'lob': 'u&˙a·na&˙i·na&šar·ri', 'sob': 'u&˙a·na&˙i·na&šar·ri'},
        },
        {
            'name': 'Word with hyphen - even morae (no accentuation)',
            'input': 'kam-du·tûm-lû¦',
            'expected': {'lob': 'kam-du·tûm-lû', 'sob': 'kam-du·tûm-lû'},
        },
        {
            'name': 'Word with hyphen - odd morae (accentuation needed)',
            'input': 'kam-du·tûm-lû·ma¦',
            'expected': {'lob': 'kam-du·tûm-lû~·ma', 'sob': 'kam-du·tûm-lû~·ma'},
        },
        {
            'name': 'Word with multiple hyphens - already syllabified',
            'input': 'a·mē·lu-ša-ī·šum¦',
            'expected': {'lob': 'a·mē·lu-ša-ī~·šum', 'sob': 'a·mē·lu-ša-ī~·šum'},
        },
        {
            'name': 'Word with -ma enclitic - even morae (no accentuation)',
            'input': 'ip-pa-lis-ma¦',
            'expected': {'lob': 'ip-pa-lis-ma', 'sob': 'ip-pa-lis-ma'},
        },
        {
            'name': 'Word with -ma enclitic - odd morae (accentuation needed)',
            'input': 'ī·ris·sū-ma¦',
            'expected': {'lob': 'ī·ris·sū~-ma', 'sob': 'ī·ris·sū~-ma'},
        },
        {
            'name': 'Mixed dots and hyphens - odd morae (accentuation needed)',
            'input': 'hen·dur-san·ga¦',
            'expected': {'lob': 'hen·dur-san~·ga', 'sob': 'hen·dur-san~·ga'},
        },
        {
            'name': 'Line with -ma enclitic',
            'input': 'ī·ris·sū-ma¦lib·ba·šu¦⟦ — ⟧e·pēš¦tā·ḫā·zi¦',
            'expected': {
                'lob': 'ī·ris·sū~-ma lib·ba·šu⟦ — ⟧e·pēš tā·ḫā~·zi',
                'sob': 'ī·ris·sū~-ma lib·ba·šu⟦ — ⟧e·pēš tā·ḫā~·zi',
            },
        },
        {
            'name': 'Multiple hyphens and enclitics',
            'input': 'ī·tam·mi¦˙a·na¦kak·kī·šu¦⟦ — ⟧lit·pa·tā¦˙i·mat¦mū·ti¦',
            'expected': {
                'lob': 'ī·tam~·mi ˙a·na&kak·kī~·šu⟦ — ⟧lit~·pa·tā ˙i·mat&mū·ti',
                'sob': 'ī·tam~·mi ˙a·na&kak·kī~·šu⟦ — ⟧lit~·pa·tā ˙i·mat&mū·ti',
            },
        },
        {
            'name': 'Explicit plus forms one accentuation unit',
            'input': 'a·pil+el·lil¦',
            'expected': {'lob': 'a·pil+el~·lil', 'sob': 'a·pil+el~·lil'},
        },
        {
            'name': 'Explicit plus keeps accentuation on linked tail (default strict)',
            'input': 'bā·nû+a·pil¦',
            'expected': {'lob': 'bā·nû+~a·pil', 'sob': 'bā·nû+~a·pil'},
        },
        {
            'name': 'Multiple explicit plus links: only last word eligible',
            'input': 'bā·nû+a·pil+el·lil¦',
            'expected': {'lob': 'bā·nû+a·pil+el~·lil', 'sob': 'bā·nû+a·pil+el~·lil'},
        },
        {
            'name': 'Explicit plus resolves internally before propagating further',
            'input': 'bā·nû+˙a·na·ku¦šar·ri¦',
            'expected': {'lob': 'bā·nû+˙a·na·ku&šar·ri', 'sob': 'bā·nû+˙a·na·ku&šar·ri'},
        },
        {
            'name': 'Explicit plus unresolved at punctuation uses last-resort on last word',
            'input': 'šar+˙a·na·ku¦⟦ ···⟧',
            'expected': {'lob': 'šar+˙~a·na·ku⟦ ···⟧', 'sob': 'šar+˙~a·na·ku⟦ ···⟧'},
        },
        {
            'name': 'Explicit plus coexists with algorithmic plus',
            'input': 'a·pil+el·lil¦gi·mir¦dad·mē¦',
            'expected': {
                'lob': 'a·pil+el~·lil gi·mir&dad~·mē',
                'sob': 'a·pil+el~·lil gi·mir&dad~·mē',
            },
        },
        {
            'name': 'Explicit plus then function words with content',
            'input': 'šar+bā·nû¦u¦˙a·na¦˙i·na¦šar·ri¦',
            'expected': {
                'lob': 'šar+bā·nû u&˙a·na&˙i·na&šar·ri',
                'sob': 'šar+bā·nû u&˙a·na&˙i·na&šar·ri',
            },
        },
    ]

    all_passed = True
    total_passed = 0

    for style in [AccentStyle.LOB, AccentStyle.SOB]:
        engine = ProsodyEngine(style=style)
        passed = 0
        total = 0
        category = f'Prosody/{style.value.upper()}'
        for test in test_cases:
            total += 1
            tokens = parse_syl_line(test['input'])
            result = engine.accentuation_line(tokens)
            expected = test['expected'][style.value]
            result = ' '.join(result.split())
            expected = ' '.join(expected.split())
            label = format_selftest_label(total, len(test_cases), test['name'])
            if result == expected:
                passed += 1
                total_passed += 1
                log_selftest_result(logger, True, category, label)
            else:
                all_passed = False
                log_selftest_result(
                    logger,
                    False,
                    category,
                    label,
                    details=[f'input={test["input"]!r}', f'expected={expected!r}', f'got={result!r}'],
                )
        log_selftest_summary(logger, category, passed, total)

    relaxed_cases = [
        {
            'name': 'relax_last allows propagation to previous linked word',
            'input': 'bā·nû+a·pil¦',
            'expected': {'lob': 'bā·nû~+a·pil', 'sob': 'bā·nû~+a·pil'},
        },
        {
            'name': 'relax_last still allows final linked accentuation in 3-word chain',
            'input': 'bā·nû+a·pil+el·lil¦',
            'expected': {'lob': 'bā·nû+a·pil+el~·lil', 'sob': 'bā·nû+a·pil+el~·lil'},
        },
        {
            'name': 'relax_last may place accentuation before linked tail when legal',
            'input': 'bā·nû+˙a·na·ku¦šar·ri¦',
            'expected': {'lob': 'bā·nû~+˙a·na·ku šar~·ri', 'sob': 'bā·nû~+˙a·na·ku šar~·ri'},
        },
        {
            'name': 'relax_last unresolved at punctuation uses last-resort on tail',
            'input': 'šar+˙a·na·ku¦⟦ ···⟧',
            'expected': {'lob': 'šar+˙~a·na·ku⟦ ···⟧', 'sob': 'šar+˙~a·na·ku⟦ ···⟧'},
        },
    ]

    relaxed_total = len(relaxed_cases) * 2
    relaxed_passed = 0
    relaxed_index = 0
    for style in [AccentStyle.LOB, AccentStyle.SOB]:
        engine = ProsodyEngine(style=style, only_last=False)
        category = f'Prosody/{style.value.upper()}'
        for test in relaxed_cases:
            relaxed_index += 1
            tokens = parse_syl_line(test['input'])
            result = engine.accentuation_line(tokens)
            expected = test['expected'][style.value]
            result = ' '.join(result.split())
            expected = ' '.join(expected.split())
            label = format_selftest_label(relaxed_index, relaxed_total, f"Relax last {test['name']}")
            if result == expected:
                relaxed_passed += 1
                total_passed += 1
                log_selftest_result(logger, True, category, label)
            else:
                all_passed = False
                log_selftest_result(
                    logger,
                    False,
                    category,
                    label,
                    details=[f'input={test["input"]!r}', f'expected={expected!r}', f'got={result!r}'],
                )
    log_selftest_summary(logger, 'Prosody relax', relaxed_passed, relaxed_total)

    mono_cases = [
        {
            'name': 'Mono mode accentuates even mora word with heavy candidate',
            'input': 'ip-pa-lis-ma¦',
            'expected': {'lob': 'ip-pa-lis~-ma', 'sob': 'ip-pa-lis~-ma'},
        },
        {
            'name': 'Mono mode skips forward merge and uses last resort on light word',
            'input': 'ba·na¦šar·ri¦',
            'expected': {'lob': 'ba·n~a šar~·ri', 'sob': 'ba·n~a šar~·ri'},
        },
        {
            'name': 'Mono mode keeps explicit pre-tail word locked before last resort',
            'input': 'bā·nû+˙a·na·ku¦šar·ri¦',
            'expected': {'lob': 'bā·nû+˙~a·na·ku šar~·ri', 'sob': 'bā·nû+˙~a·na·ku šar~·ri'},
        },
    ]

    mono_total = len(mono_cases) * 2
    mono_passed = 0
    mono_index = 0
    for style in [AccentStyle.LOB, AccentStyle.SOB]:
        engine = ProsodyEngine(style=style, mora_mode=MoraMode.MONO)
        category = f'Prosody mono/{style.value.upper()}'
        for test in mono_cases:
            mono_index += 1
            tokens = parse_syl_line(test['input'])
            result = engine.accentuation_line(tokens)
            expected = test['expected'][style.value]
            result = ' '.join(result.split())
            expected = ' '.join(expected.split())
            label = format_selftest_label(mono_index, mono_total, test['name'])
            if result == expected:
                mono_passed += 1
                total_passed += 1
                log_selftest_result(logger, True, category, label)
            else:
                all_passed = False
                log_selftest_result(
                    logger,
                    False,
                    category,
                    label,
                    details=[f'input={test["input"]!r}', f'expected={expected!r}', f'got={result!r}'],
                )
    log_selftest_summary(logger, 'Prosody mono', mono_passed, mono_total)

    matrix_cases = [
        {
            'name': 'Scenario 01 one word alone mora even',
            'input': '˙ap·sî¦',
            'structure': 'single',
            'word_count': 1,
            'group_parity': 'even',
            'last_word_parity': 'even',
            'expected': {'lob': {'bi': '˙ap·sî', 'mono': '˙ap·sî~'}, 'sob': {'bi': '˙ap·sî', 'mono': '˙ap~·sî'}},
        },
        {
            'name': 'Scenario 02 one word alone mora odd',
            'input': '˙i·lī¦',
            'structure': 'single',
            'word_count': 1,
            'group_parity': 'odd',
            'last_word_parity': 'odd',
            'expected': {'lob': {'bi': '˙i·lī~', 'mono': '˙i·lī~'}, 'sob': {'bi': '˙i·lī~', 'mono': '˙i·lī~'}},
        },
        {
            'name': 'Scenario 03 function group mora even last odd',
            'input': 'iš·tu¦˙i·lī¦',
            'structure': 'function',
            'word_count': 2,
            'group_parity': 'even',
            'last_word_parity': 'odd',
            'expected': {'lob': {'bi': 'iš·tu&˙i·lī', 'mono': 'iš·tu&˙i·lī~'}, 'sob': {'bi': 'iš·tu&˙i·lī', 'mono': 'iš·tu&˙i·lī~'}},
        },
        {
            'name': 'Scenario 04 function group mora even last even',
            'input': '˙a·na¦˙ap·sî¦',
            'structure': 'function',
            'word_count': 2,
            'group_parity': 'even',
            'last_word_parity': 'even',
            'expected': {'lob': {'bi': '˙a·na&˙ap·sî', 'mono': '˙a·na&˙ap·sî~'}, 'sob': {'bi': '˙a·na&˙ap·sî', 'mono': '˙a·na&˙ap~·sî'}},
        },
        {
            'name': 'Scenario 05 function group mora odd last odd',
            'input': '˙a·na¦˙i·lī¦',
            'structure': 'function',
            'word_count': 2,
            'group_parity': 'odd',
            'last_word_parity': 'odd',
            'expected': {'lob': {'bi': '˙a·na&˙i·lī~', 'mono': '˙a·na&˙i·lī~'}, 'sob': {'bi': '˙a·na&˙i·lī~', 'mono': '˙a·na&˙i·lī~'}},
        },
        {
            'name': 'Scenario 06 function group mora odd last even',
            'input': 'iš·tu¦˙ap·sî¦',
            'structure': 'function',
            'word_count': 2,
            'group_parity': 'odd',
            'last_word_parity': 'even',
            'expected': {'lob': {'bi': 'iš·tu&˙ap·sî~', 'mono': 'iš·tu&˙ap·sî~'}, 'sob': {'bi': 'iš·tu&˙ap~·sî', 'mono': 'iš·tu&˙ap~·sî'}},
        },
        {
            'name': 'Scenario 07 explicit group mora even last odd',
            'input': 'u·lam·min+˙i·lī¦',
            'structure': 'explicit',
            'word_count': 2,
            'group_parity': 'even',
            'last_word_parity': 'odd',
            'expected': {'lob': {'bi': 'u·lam·min+˙i·lī', 'mono': 'u·lam·min+˙i·lī~'}, 'sob': {'bi': 'u·lam·min+˙i·lī', 'mono': 'u·lam·min+˙i·lī~'}},
        },
        {
            'name': 'Scenario 08 explicit group mora even last even',
            'input': 'a·nan·ta+˙ap·sî¦',
            'structure': 'explicit',
            'word_count': 2,
            'group_parity': 'even',
            'last_word_parity': 'even',
            'expected': {'lob': {'bi': 'a·nan·ta+˙ap·sî', 'mono': 'a·nan·ta+˙ap·sî~'}, 'sob': {'bi': 'a·nan·ta+˙ap·sî', 'mono': 'a·nan·ta+˙ap~·sî'}},
        },
        {
            'name': 'Scenario 09 explicit group mora odd last odd',
            'input': 'a·nan·ta+˙i·lī¦',
            'structure': 'explicit',
            'word_count': 2,
            'group_parity': 'odd',
            'last_word_parity': 'odd',
            'expected': {'lob': {'bi': 'a·nan·ta+˙i·lī~', 'mono': 'a·nan·ta+˙i·lī~'}, 'sob': {'bi': 'a·nan·ta+˙i·lī~', 'mono': 'a·nan·ta+˙i·lī~'}},
        },
        {
            'name': 'Scenario 10 explicit group mora odd last even',
            'input': 'u·lam·min+˙ap·sî¦',
            'structure': 'explicit',
            'word_count': 2,
            'group_parity': 'odd',
            'last_word_parity': 'even',
            'expected': {'lob': {'bi': 'u·lam·min+˙ap·sî~', 'mono': 'u·lam·min+˙ap·sî~'}, 'sob': {'bi': 'u·lam·min+˙ap~·sî', 'mono': 'u·lam·min+˙ap~·sî'}},
        },
        {
            'name': 'Scenario 11 function plus explicit group even last odd',
            'input': '˙a·na+u·lam·min+˙i·lī¦',
            'structure': 'function_plus_explicit',
            'word_count': 3,
            'group_parity': 'even',
            'last_word_parity': 'odd',
            'expected': {'lob': {'bi': '˙a·na+u·lam·min+˙i·lī', 'mono': '˙a·na+u·lam·min+˙i·lī~'}, 'sob': {'bi': '˙a·na+u·lam·min+˙i·lī', 'mono': '˙a·na+u·lam·min+˙i·lī~'}},
        },
        {
            'name': 'Scenario 12 function plus explicit group even last even',
            'input': '˙a·na+a·nan·ta+˙ap·sî¦',
            'structure': 'function_plus_explicit',
            'word_count': 3,
            'group_parity': 'even',
            'last_word_parity': 'even',
            'expected': {'lob': {'bi': '˙a·na+a·nan·ta+˙ap·sî', 'mono': '˙a·na+a·nan·ta+˙ap·sî~'}, 'sob': {'bi': '˙a·na+a·nan·ta+˙ap·sî', 'mono': '˙a·na+a·nan·ta+˙ap~·sî'}},
        },
        {
            'name': 'Scenario 13 function plus explicit group odd last odd',
            'input': '˙a·na+a·nan·ta+˙i·lī¦',
            'structure': 'function_plus_explicit',
            'word_count': 3,
            'group_parity': 'odd',
            'last_word_parity': 'odd',
            'expected': {'lob': {'bi': '˙a·na+a·nan·ta+˙i·lī~', 'mono': '˙a·na+a·nan·ta+˙i·lī~'}, 'sob': {'bi': '˙a·na+a·nan·ta+˙i·lī~', 'mono': '˙a·na+a·nan·ta+˙i·lī~'}},
        },
        {
            'name': 'Scenario 14 function plus explicit group odd last even',
            'input': '˙a·na+u·lam·min+˙ap·sî¦',
            'structure': 'function_plus_explicit',
            'word_count': 3,
            'group_parity': 'odd',
            'last_word_parity': 'even',
            'expected': {'lob': {'bi': '˙a·na+u·lam·min+˙ap·sî~', 'mono': '˙a·na+u·lam·min+˙ap·sî~'}, 'sob': {'bi': '˙a·na+u·lam·min+˙ap~·sî', 'mono': '˙a·na+u·lam·min+˙ap~·sî'}},
        },
    ]

    def _parity_label(morae: int) -> str:
        return 'even' if morae % 2 == 0 else 'odd'

    def _matrix_shape(tokens: List[Union[Word, str]]) -> Dict[str, Union[int, str, bool]]:
        words = [token for token in tokens if isinstance(token, Word)]
        explicit_links = sum(1 for token in tokens if token == WORD_LINKER)
        structure = 'single'
        if len(words) == 2 and explicit_links == 0 and words[0].is_function_word:
            structure = 'function'
        elif len(words) == 2 and explicit_links == 1:
            structure = 'explicit'
        elif len(words) == 3 and explicit_links == 2 and words[0].is_function_word:
            structure = 'function_plus_explicit'

        return {
            'structure': structure,
            'word_count': len(words),
            'group_parity': _parity_label(sum(word.morae for word in words)),
            'last_word_parity': _parity_label(words[-1].morae),
        }

    matrix_coherence_total = len(matrix_cases)
    matrix_coherence_passed = 0
    for index, test in enumerate(matrix_cases, start=1):
        tokens = parse_syl_line(test['input'])
        observed = _matrix_shape(tokens)
        expected_shape = {
            'structure': test['structure'],
            'word_count': test['word_count'],
            'group_parity': test['group_parity'],
            'last_word_parity': test['last_word_parity'],
        }
        label = format_selftest_label(index, matrix_coherence_total, f"Coherence {test['name']}")
        if observed == expected_shape:
            matrix_coherence_passed += 1
            total_passed += 1
            log_selftest_result(logger, True, 'Prosody matrix coherence', label)
        else:
            all_passed = False
            log_selftest_result(
                logger,
                False,
                'Prosody matrix coherence',
                label,
                details=[f'input={test["input"]!r}', f'expected_shape={expected_shape!r}', f'observed_shape={observed!r}'],
            )
    log_selftest_summary(logger, 'Prosody matrix coherence', matrix_coherence_passed, matrix_coherence_total)

    matrix_total = len(matrix_cases) * 4
    matrix_passed = 0
    matrix_index = 0
    for style in [AccentStyle.LOB, AccentStyle.SOB]:
        for mora_mode in [MoraMode.BI, MoraMode.MONO]:
            engine = ProsodyEngine(style=style, mora_mode=mora_mode)
            category = f'Prosody matrix/{style.value.upper()}/{mora_mode.value.upper()}'
            combo_passed = 0
            for test in matrix_cases:
                matrix_index += 1
                tokens = parse_syl_line(test['input'])
                result = engine.accentuation_line(tokens)
                expected = test['expected'][style.value][mora_mode.value]
                result = ' '.join(result.split())
                expected = ' '.join(expected.split())
                label = format_selftest_label(matrix_index, matrix_total, test['name'])
                if result == expected:
                    combo_passed += 1
                    matrix_passed += 1
                    total_passed += 1
                    log_selftest_result(logger, True, category, label)
                else:
                    all_passed = False
                    log_selftest_result(
                        logger,
                        False,
                        category,
                        label,
                        details=[f'input={test["input"]!r}', f'expected={expected!r}', f'got={result!r}'],
                    )
            log_selftest_summary(logger, category, combo_passed, len(matrix_cases))

    log_selftest_summary(logger, 'Prosody matrix', matrix_passed, matrix_total)
    total_cases = (len(test_cases) * 2) + relaxed_total + mono_total + matrix_coherence_total + matrix_total
    log_selftest_summary(logger, 'Prosody', total_passed, total_cases)
    return all_passed