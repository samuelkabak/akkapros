from __future__ import annotations


def _syllabify_module():
    from akkapros.lib import syllabify

    return syllabify


def run_tests() -> bool:
    mod = _syllabify_module()
    logger = mod.get_logger_with_fallback(__name__)
    preprocess_tests = [
        ('Preprocess single newline', 'šar\ngimir', 'šar gimir', False),
        ('Preprocess double newline', 'šar\n\ngimir', 'šar\ngimir', False),
        ('Preprocess markdown heading', 'šar\n# Title\ngimir', 'šar\n# Title\ngimir', False),
        ('Preprocess markdown numbered list', 'šar\n1. item one\n2. item two', 'šar\n1. item one\n2. item two', False),
        ('Preprocess markdown bullets', 'šar\n- item one\n* item two', 'šar\n- item one\n* item two', False),
        ('Preprocess markdown table', '| A | B |\n| --- | --- |\n| šar | gimir |', '| A | B |\n| --- | --- |\n| šar | gimir |', False),
        ('Preprocess markdown fence', '```\na\nb\n```\nšar', '```\na\nb\n```\nšar', False),
        ('Preprocess preserve lines', 'šar\ngimir', 'šar\ngimir', True),
        ('Preprocess hyphen before markdown', 'šar-\nma\n# Title', 'šar-ma\n# Title', False),
        ('Preprocess plus before markdown', 'šar+\nma\n# Title', 'šar+ma\n# Title', False),
        ('Preprocess hyphen requires immediate next letter', 'šar-\n ma', 'šar- ma', False),
        ('Preprocess plus requires immediate next letter', 'šar+\n ma', 'šar+ ma', False),
    ]
    tests = [
        ('CV', 'ša', 'ša¦'),
        ('CVC', 'šar', 'šar¦'),
        ('CVV', 'bā', 'bā¦'),
        ('CVVC', 'nāš', 'nāš¦'),
        ('#VC', 'ap', '˙ap¦'),
        ('#V', 'a', '˙a¦'),
        ('#VV', 'ī', '˙ī¦'),
        ('#VVC', 'ān', '˙ān¦'),
        ('CV-CVC', 'gimir', 'gi·mir¦'),
        ('CVC-CVV', 'dadmē', 'dad·mē¦'),
        ('CVV-CVV', 'bānû', 'bā·nû¦'),
        ('CVC-CVV-CV', 'kibrāti', 'kib·rā·ti¦'),
        ('CVC-CVC-CVC-CV', 'ḫendursanga', 'ḫen·dur·san·ga¦'),
        ('V-CVC', 'apil', '˙a·pil¦'),
        ('VC-CVC', 'ellil', '˙el·lil¦'),
        ('CVVC-CVV', 'rēštû', 'rēš·tû¦'),
        ('CVC-CV-geminate', 'ḫaṭṭi', 'ḫaṭ·ṭi¦'),
        ('CVVC-CV', 'ṣīrti', 'ṣīr·ti¦'),
        ('CVV-CVC', 'nāqid', 'nā·qid¦'),
        ('CVC-CVVC', 'ṣalmāt', 'ṣal·māt¦'),
        ('CVC-CV-CV', 'qaqqadi', 'qaq·qa·di¦'),
        ('CVV-CVV', 'rēʾû', 'rē·ʾû¦'),
        ('CV-CVV-CVV-CV', 'tenēšēti', 'te·nē·šē·ti¦'),
        ('VV-CVC', 'īšum', '˙ī·šum¦'),
        ('CVV-CV-CV', 'ṭābiḫu', 'ṭā·bi·ḫu¦'),
        ('CVC-CV', 'naʾdu', 'naʾ·du¦'),
        ('V-CV', 'ana', '˙a·na¦'),
        ('CV-CVV', 'našê', 'na·šê¦'),
        ('CVC-CVV-CV', 'kakkīšu', 'kak·kī·šu¦'),
        ('VC-CVV-CV', 'ezzūti', '˙ez·zū·ti¦'),
        ('CVV-CVV-CV', 'qātāšu', 'qā·tā·šu¦'),
        ('VC-CVV', 'asmā', '˙as·mā¦'),
        ('Hyphenated word - preserve', 'ḫendur-sanga', 'ḫen·dur-san·ga¦'),
        ('Hyphenated word - merge', 'ḫendur-sanga', 'ḫen·dur·san·ga¦', True),
        ('Multiple hyphens - preserve', 'amēlu-ša-īšum', '˙a·mē·lu-ša-˙ī·šum¦'),
        ('Multiple hyphens - merge', 'amēlu-ša-īšum', '˙a·mē·lu·ša·˙ī·šum¦', True),
        ('Word linker + preserve', 'apilellil+gimirdadmē', '˙a·pi·lel·lil+gi·mir·dad·mē¦'),
        ('Word linker + with syllabic words', 'apil+ellil', '˙a·pil+˙el·lil¦'),
        ('Mixed + and - separators', 'apil+el-lil', '˙a·pil+˙el-lil¦'),
        ('Hyphen at beginning', '-šar', '⟦-⟧šar¦'),
        ('Hyphen at end', 'šar-', 'šar⟦-⟧¦'),
        ('Linker at beginning', '+šar', '⟦+⟧šar¦'),
        ('Linker at end', 'šar+', 'šar⟦+⟧¦'),
        ('Dash with spaces', 'ḫendur - sanga', 'ḫen·dur¦⟦ - ⟧san·ga¦'),
        ('Hyphen+space', 'ḫendur- sanga', 'ḫen·dur-¦san·ga¦'),
        ('Space+hyphen', 'ḫendur -sanga', 'ḫen·dur¦-san·ga¦'),
        ('Single space between words', 'šar gimir', 'šar¦gi·mir¦'),
        ('Multiple spaces between words', 'šar   gimir', 'šar¦gi·mir¦'),
        ('Tab between words', 'šar\tgimir', 'šar¦gi·mir¦'),
        ('Newline between words', 'šar\ngimir', 'šar¦gi·mir¦'),
        ('Hyphen split across lines merge', 'ḫendur-\nsanga', 'ḫen·dur·san·ga¦', True),
        ('Spaced hyphen across lines no merge', 'ḫendur -\nsanga', 'ḫen·dur¦⟦ - ⟧san·ga¦'),
        ('Word linker split across lines', 'apil+\nellil', '˙a·pil+˙el·lil¦'),
        ('Spaced linker across lines no merge', 'apil +\nellil', '˙a·pil¦⟦ + ⟧˙el·lil¦'),
        ('Double newline', 'šar\n\ngimir', 'šar¦\ngi·mir¦'),
        ('Preserve lines single newline', 'šar\ngimir', 'šar¦\ngi·mir¦', False, True),
        ('Comma after word', 'šar, gimir', 'šar¦⟦, ⟧gi·mir¦'),
        ('Em-dash', 'šar — gimir', 'šar¦⟦ — ⟧gi·mir¦'),
        ('Ellipsis', 'šar … gimir', 'šar¦⟦ … ⟧gi·mir¦'),
        ('Number between words', 'šar 123 gimir', 'šar¦⟦ 123 ⟧gi·mir¦'),
        ('Number with commas', 'šar 12,345 gimir', 'šar¦⟦ 12,345 ⟧gi·mir¦'),
        ('Number with newline', 'šar 123\n456 gimir', 'šar¦⟦ 123⟧\n⟦456 ⟧gi·mir¦', False, True),
        ('Number with spaces and newline', 'šar 123\n  456 gimir', 'šar¦⟦ 123⟧\n⟦ 456 ⟧gi·mir¦', False, True),
        ('Number with tab and dash', 'šar 123  \t-  456 gimir', 'šar¦⟦ 123  \t-  456 ⟧gi·mir¦'),
        ('Currency before number', 'šar $123 gimir', 'šar¦⟦ $123 ⟧gi·mir¦'),
        ('Currency after number', 'šar 123$ gimir', 'šar¦⟦ 123$ ⟧gi·mir¦'),
        ('En-dash with spaces', 'šar – gimir', 'šar¦⟦ – ⟧gi·mir¦'),
        ('Punctuation newline preserved', 'šar ,\ngimir', 'šar¦⟦ ,⟧\ngi·mir¦', False, True),
        ('Preserve block newline preserved', 'šar {{x}}\ngimir', 'šar¦⟦ {{x}}⟧\ngi·mir¦', False, True),
        ('Hash at beginning of line', 'šar\n# 123\ngimir', 'šar¦\n⟦# 123⟧\ngi·mir¦', False, True),
        ('Bullet at beginning of line', 'šar\n- 123\ngimir', 'šar¦\n⟦- 123⟧\ngi·mir¦', False, True),
        ('Chinese characters', 'šar {{国王}} gimir', 'šar¦⟦ {{国王}} ⟧gi·mir¦'),
        ('Foreign character in word 1', 'šar? gimir{{test}}dun', 'šar¦⟦? ⟧gi·mir¦⟦{{test}}⟧dun¦'),
        ('Foreign character in word 2', 'šar? gimir{{test }}dun', 'šar¦⟦? ⟧gi·mir¦⟦{{test }}⟧dun¦'),
        ('Foreign character in word 3', 'šar? gimir{{ test }}dun', 'šar¦⟦? ⟧gi·mir¦⟦{{ test }}⟧dun¦'),
        ('Foreign character in word 4', 'šar? gimir {{test}}dun', 'šar¦⟦? ⟧gi·mir¦⟦ {{test}}⟧dun¦'),
        ('Foreign character in word 5', 'šar? gimir{{test}} dun', 'šar¦⟦? ⟧gi·mir¦⟦{{test}} ⟧dun¦'),
        ('Foreign character in word 6', 'šar? gimir {{test}} dun', 'šar¦⟦? ⟧gi·mir¦⟦ {{test}} ⟧dun¦'),
        ('Mixed with reserve brackets', 'šar gimir {{jamal@gmail·com}} muḫḫi.', 'šar¦gi·mir¦⟦ {{jamal@gmail·com}} ⟧muḫ·ḫi¦⟦.⟧'),
        ('Double-brace escape', 'šar {{English word}} gimir', 'šar¦⟦ {{English word}} ⟧gi·mir¦'),
        ('Tagged escape', 'šar {url{https://ex.am/ple}} gimir', 'šar¦⟦ {url{https://ex.am/ple}} ⟧gi·mir¦'),
        ('Internal tagged escape', 'šar {_mdf{---}} gimir', 'šar¦⟦ {_mdf{---}} ⟧gi·mir¦'),
        ('Preserve whitespace inside escape', 'šar {{  hello world  }} gimir', 'šar¦⟦ {{  hello world  }} ⟧gi·mir¦'),
        ('Escape spacing like punctuation', 'šar {{x}} gimir', 'šar¦⟦ {{x}} ⟧gi·mir¦'),
        ('Complex line', 'ikkaru ina muḫḫi … — ibakki ṣarpiš', '˙ik·ka·ru¦˙i·na¦muḫ·ḫi¦⟦ … — ⟧˙i·bak·ki¦ṣar·piš¦'),
        ('Diphthong ua', 'ua', '˙u·¨a¦'),
        ('Diphthong ai', 'ai', '˙a·¨i¦'),
        ('Diphthong iā', 'iā', '˙i·¨ā¦'),
        ('Multiple diphthongs', 'ua iā', '˙u·¨a¦˙i·¨ā¦'),
        ('Diphthong with consonant', 'šar ua', 'šar¦˙u·¨a¦'),
    ]
    error_tests = [
        ('Period after word', 'šar· gimir', 'undeclared punctuation'),
        ('Punctuation glued both sides', 'ab?kat', 'invalid punctuation spacing'),
        ('Punctuation suite glued both sides', 'ab?!kat', 'invalid punctuation spacing'),
        ('Number attached left', 'ab123 kar', 'invalid punctuation spacing'),
        ('Number attached right', 'ab 123kar', 'invalid punctuation spacing'),
        ('Currency attached left', 'ab$123 kar', 'invalid punctuation spacing'),
        ('Currency attached right', 'ab $123kar', 'invalid punctuation spacing'),
        ('En-dash attached left', 'ab– kar', 'invalid punctuation spacing'),
        ('En-dash attached right', 'ab –kar', 'invalid punctuation spacing'),
        ('Invalid number-format regex', 'šar 12,345 gimir', 'unterminated character set', False, False, '['),
    ]
    pattern_tests = [('BOL token accepted for hyphen line', [r'^[:bol:]\s*-\s+\d+[:eol:]$'], '- 123', True)]

    passed = 0
    total = len(preprocess_tests) + len(tests) + len(error_tests) + len(pattern_tests) + 1
    case_index = 0

    for name, inp, expected, preserve in preprocess_tests:
        case_index += 1
        label = mod.format_selftest_label(case_index, total, name)
        result = mod.text_preprocess_boundaries(inp, [], preserve_lines=preserve)
        if result == expected:
            passed += 1
            mod.log_selftest_result(logger, True, 'Syllabify', label)
        else:
            mod.log_selftest_result(logger, False, 'Syllabify', label, details=[f'input={inp!r}', f'expected={expected!r}', f'got={result!r}'])

    for test in tests:
        case_index += 1
        if len(test) == 3:
            name, inp, expected = test
            merge = False
            preserve_lines = False
            number_format = ''
        elif len(test) == 4:
            name, inp, expected, merge = test
            preserve_lines = False
            number_format = ''
        elif len(test) == 5:
            name, inp, expected, merge, preserve_lines = test
            number_format = ''
        else:
            name, inp, expected, merge, preserve_lines, number_format = test
        result = mod.syllabify_text(inp, merge_hyphen=merge, preserve_lines=preserve_lines, number_format=number_format)
        label = mod.format_selftest_label(case_index, total, name)
        if result == expected:
            passed += 1
            mod.log_selftest_result(logger, True, 'Syllabify', label)
        else:
            mod.log_selftest_result(logger, False, 'Syllabify', label, details=[f'input={inp!r}', f'expected={expected!r}', f'got={result!r}'])

    for test in error_tests:
        case_index += 1
        if len(test) == 3:
            name, inp, expected_reason = test
            merge = False
            preserve_lines = False
            number_regex = ''
        else:
            name, inp, expected_reason, merge, preserve_lines, number_regex = test
        label = mod.format_selftest_label(case_index, total, name)
        try:
            mod.syllabify_text(inp, merge_hyphen=merge, preserve_lines=preserve_lines, number_format=number_regex)
            mod.log_selftest_result(logger, False, 'Syllabify', label, details=[f'input={inp!r}', f'expected_error={expected_reason!r}', 'got=success'])
        except mod.PunctuationConfigError as exc:
            if expected_reason in str(exc).lower():
                passed += 1
                mod.log_selftest_result(logger, True, 'Syllabify', label)
            else:
                mod.log_selftest_result(logger, False, 'Syllabify', label, details=[f'input={inp!r}', f'expected_error={expected_reason!r}', f'got_error={exc!r}'])

    for name, custom_patterns, sample, should_match in pattern_tests:
        case_index += 1
        label = mod.format_selftest_label(case_index, total, name)
        try:
            compiled = mod._compile_regex_patterns(custom_patterns, '--extra-short-punct-pattern')
            contextual = mod.contextualize_for_regex(sample, at_sol=True, at_eol=True, at_eof=False)
            match = any(rx.search(contextual) for rx in compiled)
            if match == should_match:
                passed += 1
                mod.log_selftest_result(logger, True, 'Syllabify', label)
            else:
                mod.log_selftest_result(logger, False, 'Syllabify', label, details=[f'sample={sample!r}', f'expected_match={should_match}', f'got_match={match}'])
        except Exception as exc:
            mod.log_selftest_result(logger, False, 'Syllabify', label, details=[f'sample={sample!r}', f'error={exc!r}'])

    case_index += 1
    nested_label = mod.format_selftest_label(case_index, total, 'Nested escapes unsupported')
    nested = mod.parse_escape_at('{{a{{b}}}}', 0)
    if nested is None:
        passed += 1
        mod.log_selftest_result(logger, True, 'Syllabify', nested_label)
    else:
        mod.log_selftest_result(logger, False, 'Syllabify', nested_label, details=['expected=None', f'got={nested!r}'])

    mod.log_selftest_summary(logger, 'Syllabify', passed, total)
    return passed == total