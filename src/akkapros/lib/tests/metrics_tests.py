from __future__ import annotations


def _metrics_module():
    from akkapros.lib import metrics

    return metrics


def _utils_module():
    from akkapros.lib import utils

    return utils


# ------------------------------------------------------------
# Unit tests
# ------------------------------------------------------------


def test_small_text() -> bool:
    """Test syllable counting on a small sample."""
    mod = _metrics_module()
    logger = mod.get_logger_with_fallback(__name__)
    test_text = "šar gi·mir+dad~·mē bā·nû kib·rā~·ti"

    # Expected original counts (without accentuation)
    expected_original = {
        'CV': 2,   # gi, ti
        'CVC': 4,  # šar, mir, dad, kib
        'CVV': 4,  # mē, bā, nû, rā
        'total': 10
    }
    
    # Expected accentuated counts (with accentuation)
    expected_accentuated = {
        'CV': 2,      # gi, ti
        'CVC': 3,     # šar, mir, kib
        'CVV': 3,     # mē, bā, nû
        'CVC:': 1,    # dad~
        'CVV:': 1,    # rā~
        'total': 10
    }

    ok = True

    # Test original
    original_stats = mod.analyze_text(test_text.replace('~', ''), is_accentuated=False)

    # Verify original counts
    for typ, expected in expected_original.items():
        if typ == 'total':
            continue
        actual = original_stats['syllable_counts'].get(typ, 0)
        if actual != expected:
            ok = False
            mod.log_selftest_result(
                logger,
                False,
                'Metrics sample',
                f'Original {typ}',
                details=[
                    f'text={test_text!r}',
                    f'got={actual}',
                    f'expected={expected}',
                ],
            )

    total = sum(original_stats['syllable_counts'].values())
    if total != expected_original['total']:
        ok = False
        mod.log_selftest_result(
            logger,
            False,
            'Metrics sample',
            'Original total',
            details=[
                f'text={test_text!r}',
                f'got={total}',
                f'expected={expected_original["total"]}',
            ],
        )

    # Test accentuated
    accentuated_stats = mod.analyze_text(test_text, is_accentuated=True)

    # Verify accentuated counts
    for typ, expected in expected_accentuated.items():
        if typ == 'total':
            continue
        actual = accentuated_stats['syllable_counts'].get(typ, 0)
        if actual != expected:
            ok = False
            mod.log_selftest_result(
                logger,
                False,
                'Metrics sample',
                f'Accentuated {typ}',
                details=[
                    f'text={test_text!r}',
                    f'got={actual}',
                    f'expected={expected}',
                ],
            )

    total = sum(accentuated_stats['syllable_counts'].values())
    if total != expected_accentuated['total']:
        ok = False
        mod.log_selftest_result(
            logger,
            False,
            'Metrics sample',
            'Accentuated total',
            details=[
                f'text={test_text!r}',
                f'got={total}',
                f'expected={expected_accentuated["total"]}',
            ],
        )

    if ok:
        mod.log_selftest_result(logger, True, 'Metrics sample', 'Small text syllable counting')
    return ok

def debug_mean_calculation(text: str, label: str):
    """Debug mean interval calculation."""
    mod = _metrics_module()
    logger = mod.get_logger_with_fallback(__name__)
    logger.info('Debug MeanC | %s | text=%r', label, text)
    
    preprocessed = mod.preprocess_text(text)
    logger.info('Debug MeanC | %s | preprocessed=%r', label, preprocessed)
    
    # Get segments and distances
    consonants, vowels = mod.extract_segments(preprocessed)
    logger.info('Debug MeanC | %s | consonants=%s', label, consonants)
    logger.info('Debug MeanC | %s | vowels_after=%s', label, vowels)
    
    distances = mod.compute_consonant_distances(consonants, vowels)
    logger.info('Debug MeanC | %s | distances=%s', label, distances)
    
    if distances:
        mean = sum(distances) / len(distances)
        logger.info('Debug MeanC | %s | mean=%.4f', label, mean)
    else:
        logger.info('Debug MeanC | %s | no distances', label)
    
    return distances

def _test_word_pattern_matching() -> bool:
    """Unit test: word pattern matching."""
    mod = _metrics_module()
    import re
    word_pattern = mod.build_word_pattern()
    full_word_pattern = re.compile(f'^(?:{word_pattern.pattern})$')
    test_cases = [
        ('at·tā', True),
        ('˙a·na', True),
        ('ā·lik', True),
        ('maḫ·rim~-ma', True),
        ('i·lū~', True),
        ('~a', True),
        ('ana+kâ·ša', True),
        ('ka+', False),
        ('$word', False),
        ('word$', False),
        ('_word', False),
        ('word+', False),
    ]
    for inp, should in test_cases:
        if bool(full_word_pattern.match(inp)) != should:
            return False
    return True


def _test_tokenizer() -> bool:
    """Unit test: tokenizer."""
    mod = _metrics_module()
    word_pattern = mod.build_word_pattern()
    cases = [
        ('at·tā ā·lik', [('WORD', 'at·tā'), ('SPACES', ' '), ('WORD', 'ā·lik')]),
        ('at·tā, ā·lik!', [('WORD', 'at·tā'), ('PUNCT', ','), ('SPACES', ' '), ('WORD', 'ā·lik'), ('PUNCT', '!')]),
        ('at·tā⟦ : ⟧ā·lik', [('WORD', 'at·tā'), ('PUNCT', '⟦ : ⟧'), ('WORD', 'ā·lik')]),
        ('ana+kâ·ša lu·ṣī-ma', [('WORD', 'ana+kâ·ša'), ('SPACES', ' '), ('WORD', 'lu·ṣī-ma')]),
        ('at·tā   ā·lik', [('WORD', 'at·tā'), ('SPACES', '   '), ('WORD', 'ā·lik')]),
        ('  at·tā ā·lik', [('SPACES', '  '), ('WORD', 'at·tā'), ('SPACES', ' '), ('WORD', 'ā·lik')]),
        ('at·tā ā·lik  ', [('WORD', 'at·tā'), ('SPACES', ' '), ('WORD', 'ā·lik'), ('SPACES', '  ')]),
    ]
    for inp, expected in cases:
        if mod.tokenize_line(inp, word_pattern) != expected:
            return False
    return True


def _test_word_processing() -> bool:
    mod = _metrics_module()
    cases = [
        ('at·tā', 'ʾat·tā'),
        ('˙a·na', 'ʾa·na'),
        ('ā·lik', 'ʾā·lik'),
        ('maḫ·rim~-ma', 'maḫ·rim:-ma'),
        ('~a', ':a'),
        ('k~a', 'k:a'),
        ('dad~', 'dad:'),
    ]
    for inp, expected in cases:
        if mod.process_word(inp) != expected:
            return False
    return True


def _test_preprocessing() -> bool:
    mod = _metrics_module()
    cases = [
        ('at·tā ā·lik', 'ʾat·tāʾā·lik'),
        ('˙a·na i·lī', 'ʾa·naʾi·lī'),
        ('maḫ·rim~-ma dad~', 'maḫ·rim:-madad:'),
        ('ana+kâ·ša lu·ṣī-ma', 'ʾana+kâ·šalu·ṣī-ma'),
    ]
    for inp, expected in cases:
        if mod.preprocess_text(inp) != expected:
            return False
    return True


def _test_segment_extraction() -> bool:
    mod = _metrics_module()
    cases = [
        ('mas·ta', ['m', 's', 't'], ['a', '', 'a']),
        ('mas~·ta', ['m', 's', 't'], ['a', ':', 'a']),
        ('˙a·na', ['ʾ', 'n'], ['a', 'a']),
    ]
    for inp, exp_cons, exp_vows in cases:
        pre = mod.preprocess_text(inp)
        cons, vows = mod.extract_segments(pre)
        if cons != exp_cons or vows != exp_vows:
            return False
    return True


def _test_distance_calculation() -> bool:
    mod = _metrics_module()
    cases = [
        ('mas·ta', [1, 0, 1]),
        ('mas~·ta', [1, 1, 1]),
        ('a·na', [1, 1]),
    ]
    for inp, expected in cases:
        pre = mod.preprocess_text(inp)
        cons, vows = mod.extract_segments(pre)
        d = mod.compute_consonant_distances(cons, vows)
        if d != expected:
            return False
    return True


def _test_consonant_distance_definitions() -> bool:
    """Regression test for core consonant-distance definitions used by DeltaC.

    Target definitions (between two consonants):
    - CC = 0
    - C:C = 1
    - CVC = 1
    - CVVC = 2
    - CVV:C = 3
    """
    mod = _metrics_module()
    # CC: use the s->t pair inside mas·ta (distances = [1, 0, 1]).
    pre = mod.preprocess_text('mas·ta')
    cons, vows = mod.extract_segments(pre)
    d = mod.compute_consonant_distances(cons, vows)
    if len(d) < 2 or d[1] != 0:
        return False

    # C:C: s->t pair inside mas~·ta (mas:·ta after preprocessing).
    pre = mod.preprocess_text('mas~·ta')
    cons, vows = mod.extract_segments(pre)
    d = mod.compute_consonant_distances(cons, vows)
    if len(d) < 2 or d[1] != 1:
        return False

    # CVC: m->s in ma·sa.
    pre = mod.preprocess_text('ma·sa')
    cons, vows = mod.extract_segments(pre)
    d = mod.compute_consonant_distances(cons, vows)
    if not d or d[0] != 1:
        return False

    # CVVC: m->s in mā·sa.
    pre = mod.preprocess_text('mā·sa')
    cons, vows = mod.extract_segments(pre)
    d = mod.compute_consonant_distances(cons, vows)
    if not d or d[0] != 2:
        return False

    # CVV:C: m->s in mà·sa.
    pre = mod.preprocess_text('mà·sa')
    cons, vows = mod.extract_segments(pre)
    d = mod.compute_consonant_distances(cons, vows)
    if not d or d[0] != 3:
        return False

    return True


def _test_punctuation_marks_segment_boundaries() -> bool:
    """Punctuation must create WORD_BOUNDARY markers in preprocessing."""
    mod = _metrics_module()
    pre = mod.preprocess_text('ab⟦ ,⟧ta')
    if mod.WORD_BOUNDARY not in pre:
        return False
    return True


def _test_pause_metrics_grouping() -> bool:
    mod = _metrics_module()
    text = "at·tā⟦ ?!!! ⟧ā·lik⟦ ), ⟧i·lī⟦ ... ⟧bā·nû"
    stats = mod.analyze_text(text, is_accentuated=True)
    rows = mod.build_phone_rows(text)
    pm = mod.compute_pause_metrics(rows, stats)
    if pm['raw_counts']['spaces'] != 0:
        return False
    if pm['raw_counts']['short_punctuation'] != 2:
        return False
    if pm['raw_counts']['long_punctuation'] != 2:
        return False
    return True


def _test_unknown_punctuation_raises() -> bool:
    mod = _metrics_module()
    text = "at·tā⟦ @ ⟧ā·lik"
    stats = mod.analyze_text(text, is_accentuated=True)
    rows = mod.build_phone_rows(text)
    pause_rows = [row for row in rows if row['category'] == 'S']
    if len(pause_rows) != 2:
        return False
    if pause_rows[0]['type'] != 'I' or pause_rows[0]['length'] != 'S':
        return False
    pm = mod.compute_pause_metrics(rows, stats)
    return pm['raw_counts']['short_punctuation'] == 1 and pm['raw_counts']['long_punctuation'] == 1


def _test_armored_pause_token_classification() -> bool:
    mod = _metrics_module()
    if mod._classify_pause_punctuation_token('⟦ : ⟧') != 'short':
        return False
    if mod._classify_pause_punctuation_token('⟦ ... ⟧') != 'short':
        return False
    if mod._classify_pause_punctuation_token('⟦ @ ⟧') is not None:
        return False
    return True


def _test_mora_totals_and_original_speech() -> bool:
    """Unit test: total morae and row-derived speech metrics are exposed."""
    mod = _metrics_module()
    text = "tā·ḫā~·za ik~·ta·ṣar"
    result = mod.process_filetext(
        text,
        prominence_statistics={
            'function_word_count': 0,
            'explicit_word_link_count': 0,
        },
    )

    orig_total = result['original']['stats']['mora_stats']['total']
    accentuated_total = result['accentuated']['stats']['mora_stats']['total']
    if not isinstance(orig_total, int) or not isinstance(accentuated_total, int):
        return False
    # Original (without ~): tā·ḫā·za ik·ta·ṣar = 10 morae.
    if orig_total != 10:
        return False
    # Accentuated (with two ~): tā·ḫā~·za ik~·ta·ṣar = 12 morae.
    if accentuated_total != 12:
        return False
    if accentuated_total <= orig_total:
        return False

    orig_speech = result['original'].get('speech', {})
    accentuated_speech = result['accentuated'].get('speech', {})
    required = {'total_duration_ms', 'pause_duration_ms', 'articulation_duration_ms', 'wpm', 'pause_ratio', 'pause_row_count'}
    if set(orig_speech.keys()) != required:
        return False
    if set(accentuated_speech.keys()) != required:
        return False
    if orig_speech['total_duration_ms'] <= 0 or accentuated_speech['total_duration_ms'] <= 0:
        return False
    if orig_speech['pause_duration_ms'] < 0 or accentuated_speech['pause_duration_ms'] < 0:
        return False
    if orig_speech['articulation_duration_ms'] != orig_speech['total_duration_ms'] - orig_speech['pause_duration_ms']:
        return False
    if accentuated_speech['articulation_duration_ms'] != accentuated_speech['total_duration_ms'] - accentuated_speech['pause_duration_ms']:
        return False

    # Morae per word must differ when accentuation adds morae.
    orig_mpw = result['original']['stats']['word_stats']['morae_per_word']['mean']
    accentuated_mpw = result['accentuated']['stats']['word_stats']['morae_per_word']['mean']
    if accentuated_mpw <= orig_mpw:
        return False

    return True


def _test_table_new_fields_and_no_csv() -> bool:
    """Unit test: table exposes current fields and CSV writer is removed."""
    mod = _metrics_module()
    text = "šar gi·mir+dad~·mē bā·nû kib·rā~·ti"
    result = mod.process_filetext(
        text,
        prominence_statistics={
            'function_word_count': 1,
            'explicit_word_link_count': 1,
        },
    )

    table = mod.format_table(result)
    if "Syllable statistics:" not in table:
        return False
    if "Total morae:" not in table:
        return False
    if "Std dev morae per syllable:" in table:
        return False
    if "Total syllables:" not in table:
        return False
    if table.count("Speech metrics:") != 2:
        return False
    if "Speech rate (original):" in table or "Speech rate (accentuated):" in table:
        return False
    if "Pause metrics:" in table or "Pause duration allocation" in table:
        return False
    if "SPS (speech):" in table or "Average syllable duration:" in table:
        return False
    if "Prominence statistics:" not in table:
        return False
    if "Function words: 1 words" not in table:
        return False
    if "Explicitly linked words: 1 words" not in table:
        return False
    if "Prominence candidates: 3 words" not in table:
        return False
    if "meanC:" not in table or "meanV:" not in table:
        return False
    if "ΔC:" not in table or "ΔV:" not in table:
        return False
    if "rPVI-C:" not in table or "nPVI-V:" not in table:
        return False
    if "Unit drift max:" not in table or "Unit drift stddev:" not in table:
        return False
    if "VarcoC: " not in table or "%" in "\n".join(
        line for line in table.splitlines() if "VarcoC:" in line
    ):
        return False
    if "ΔC_mora:" in table or "MeanC_mora:" in table:
        return False

    # Ordering checks: word statistics must precede prominence and mora statistics.
    if table.find("Word statistics:") > table.find("Prominence statistics:"):
        return False
    if table.find("Prominence statistics:") > table.find("Mora statistics:"):
        return False

    # Ordering checks: speech blocks should come before acoustic blocks.
    if table.find("Speech metrics:") > table.find("Acoustic metrics (original):"):
        return False
    if table.rfind("Speech metrics:") > table.find("Acoustic metrics (accentuated):"):
        return False
    return 'format_csv' not in globals()


def _test_small_corpus_metrics_consistency() -> bool:
    """Unit test: all core metrics equations stay consistent on a small corpus."""
    mod = _metrics_module()
    from akkapros.lib.prosody import AccentStyle, ProsodyEngine, parse_syl_line, postprocess_restore_diphthongs
    from akkapros.lib.syllabify import syllabify_text

    sample_proc = (
        "appūnā-ma ištēn-ešret : kīma šuāti uštabši\n"
        "ina ilī bukrīša : šūt iškunūši puḫra\n"
        "ušašqi qingu : ina birīšunu šâšu ušrabbīš\n"
        "ālikūt maḫri pān ummāni muʾerrūt puḫri\n"
    )

    syllabified = syllabify_text(sample_proc, preserve_lines=True)
    engine = ProsodyEngine(style=AccentStyle.LOB)
    accentuated_lines = []
    for line in syllabified.splitlines():
        if not line.strip():
            accentuated_lines.append('')
            continue
        accentuated_lines.append(engine.accentuation_line(parse_syl_line(line)))
    tilde_text = '\n'.join(postprocess_restore_diphthongs(accentuated_lines)) + '\n'

    result = mod.process_filetext(
        tilde_text,
        prominence_statistics={
            'function_word_count': 2,
            'explicit_word_link_count': 1,
        },
    )

    for section in ('original', 'accentuated'):
        stats = result[section]['stats']
        speech = result[section]['speech']
        total_syllables = stats['total_syllables']
        total_words = stats['word_stats']['total_words']
        total_morae = stats['mora_stats']['total']
        if sum(stats['syllable_counts'].values()) != total_syllables:
            return False
        if total_words <= 0:
            return False
        if not __import__('math').isclose(
            stats['word_stats']['syllables_per_word']['mean'],
            total_syllables / total_words,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            return False
        if not __import__('math').isclose(
            stats['word_stats']['morae_per_word']['mean'],
            total_morae / total_words,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            return False
        if speech['articulation_duration_ms'] != speech['total_duration_ms'] - speech['pause_duration_ms']:
            return False
        expected_wpm = total_words / (speech['total_duration_ms'] / 60000.0) if speech['total_duration_ms'] else 0.0
        expected_pause_ratio = (speech['pause_duration_ms'] / speech['total_duration_ms'] * 100.0) if speech['total_duration_ms'] else 0.0
        if not __import__('math').isclose(speech['wpm'], expected_wpm, rel_tol=0.0, abs_tol=1e-12):
            return False
        if not __import__('math').isclose(speech['pause_ratio'], expected_pause_ratio, rel_tol=0.0, abs_tol=1e-12):
            return False

    pause_counts = mod._count_pause_rows(mod.build_phone_rows(tilde_text))
    if pause_counts['punctuation'] <= 0:
        return False

    accentuation_stats = result['accentuation_stats']
    original_total_syllables = result['original']['stats']['total_syllables']
    if not __import__('math').isclose(
        accentuation_stats['accentuation_rate'],
        accentuation_stats['accentuated_syllables'] / original_total_syllables * 100.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        return False

    table = mod.format_table(result)
    if "Syllable statistics:" not in table:
        return False
    if f"Total syllables: {result['original']['stats']['total_syllables']} syllables" not in table:
        return False
    if f"Total syllables: {result['accentuated']['stats']['total_syllables']} syllables" not in table:
        return False
    if "Word statistics:" not in table or "Mora statistics:" not in table:
        return False
    if "Prominence statistics:" not in table:
        return False
    if table.find("Word statistics:") > table.find("Prominence statistics:"):
        return False
    if table.find("Prominence statistics:") > table.find("Mora statistics:"):
        return False
    if "Total morae number:" in table:
        return False

    return True


def _test_small_corpus_exact_surface_values() -> bool:
    """Unit test: representative public metrics surfaces stay pinned on a fixed sample."""
    mod = _metrics_module()
    from akkapros.lib.prosody import AccentStyle, ProsodyEngine, parse_syl_line, postprocess_restore_diphthongs
    from akkapros.lib.syllabify import syllabify_text

    sample_proc = (
        "appūnā-ma ištēn-ešret : kīma šuāti uštabši\n"
        "ina ilī bukrīša : šūt iškunūši puḫra\n"
        "ušašqi qingu : ina birīšunu šâšu ušrabbīš\n"
        "ālikūt maḫri pān ummāni muʾerrūt puḫri\n"
    )

    syllabified = syllabify_text(sample_proc, preserve_lines=True)
    engine = ProsodyEngine(style=AccentStyle.LOB)
    accentuated_lines = []
    for line in syllabified.splitlines():
        if not line.strip():
            accentuated_lines.append('')
            continue
        accentuated_lines.append(engine.accentuation_line(parse_syl_line(line)))
    tilde_text = '\n'.join(postprocess_restore_diphthongs(accentuated_lines)) + '\n'

    result = mod.process_filetext(
        tilde_text,
        prominence_statistics={
            'function_word_count': 2,
            'explicit_word_link_count': 1,
        },
    )

    original = result['original']
    accentuated = result['accentuated']
    accentuation = result['accentuation_stats']
    if original['stats']['total_syllables'] != 60:
        return False
    if original['stats']['word_stats']['total_words'] != 24:
        return False
    if original['stats']['mora_stats']['total'] != 100:
        return False
    if original['stats']['syllable_counts'] != {
        'CV': 22,
        'CVC': 10,
        'CVV': 9,
        'CVVC': 6,
        'V': 4,
        'VC': 7,
        'VV': 2,
    }:
        return False
    if original['speech']['total_duration_ms'] <= 0:
        return False
    if original.get('prominence_statistics') != {
        'function_word_count': 2,
        'explicit_word_link_count': 1,
        'prominence_candidate_word_count': 21,
    }:
        return False
    if accentuated['stats']['mora_stats']['total'] != 116:
        return False
    if accentuated['stats']['syllable_counts'] != {
        'CV': 22,
        'CVC': 5,
        'CVC:': 5,
        'CVV': 2,
        'CVV:': 7,
        'CVV:C': 3,
        'CVVC': 3,
        'V': 4,
        'VC': 6,
        'VC:': 1,
        'VV': 2,
    }:
        return False
    if accentuated['speech']['total_duration_ms'] <= original['speech']['total_duration_ms']:
        return False
    if not __import__('math').isclose(accentuation['accentuation_rate'], 26.666666666666668, rel_tol=0.0, abs_tol=1e-12):
        return False
    if accentuation['accentuation_types'] != {
        'CVC:': 5,
        'CVV:': 7,
        'CVV:C': 3,
        'VC:': 1,
    }:
        return False
    return True


def _test_interval_metrics_zero_case() -> bool:
    """Unit test: empty interval inputs return zeros across the public surface."""
    mod = _metrics_module()
    acoustic = mod.compute_interval_metrics([])
    return acoustic == {
        'intervals': [],
        'v_intervals_ms': [],
        'c_intervals_ms': [],
        'p_intervals_ms': [],
        'total_duration_ms': 0,
        'percent_v': 0.0,
        'percent_c': 0.0,
        'mean_v_ms': 0.0,
        'mean_c_ms': 0.0,
        'delta_v_ms': 0.0,
        'delta_c_ms': 0.0,
        'varco_v': 0.0,
        'varco_c': 0.0,
        'rpvi_c': 0.0,
        'npvi_v': 0.0,
    }


def _write_phone_pair_fixture(document_text: str):
    mod = _metrics_module()
    phonetize_config = mod.build_default_phonetize_config()
    (ophone_rows, ophone_report), (phone_rows, phone_report) = mod.realize_phone_streams(
        document_text,
        phonetize_config,
        None,
    )
    ophone_doc = mod.compose_text_document(
        {
            'package': {'name': 'akkapros', 'version': mod.__version__},
            'pipeline': 'pipeline',
            'step': 'phonetize',
            'file': {'id': 'ophone-id', 'title': 'Metrics Test', 'format': 'phone', 'version': '1.0.0', 'date': '2026-04-10'},
            'metadata': {'input_file_id': 'tilde-id', 'options': {}, 'data': {'phonetize': {'unit_drift': ophone_report['unit_drift']}}},
        },
        mod.serialize_phone_rows(ophone_rows),
    )
    phone_doc = mod.compose_text_document(
        {
            'package': {'name': 'akkapros', 'version': mod.__version__},
            'pipeline': 'pipeline',
            'step': 'phonetize',
            'file': {'id': 'phone-id', 'title': 'Metrics Test', 'format': 'phone', 'version': '1.0.0', 'date': '2026-04-10'},
            'metadata': {'input_file_id': 'tilde-id', 'options': {}, 'data': {'phonetize': {'unit_drift': phone_report['unit_drift']}}},
        },
        mod.serialize_phone_rows(phone_rows),
    )
    import tempfile
    with tempfile.NamedTemporaryFile('w+', suffix='_ophone.txt', encoding='utf-8', delete=False) as ohandle:
        ohandle.write(ophone_doc)
        ophone_path = ohandle.name
    with tempfile.NamedTemporaryFile('w+', suffix='_phone.txt', encoding='utf-8', delete=False) as phandle:
        phandle.write(phone_doc)
        phone_path = phandle.name
    return phone_path, ophone_path


def _test_process_file_derives_prominence_counts_from_phone_rows() -> bool:
    mod = _metrics_module()
    text = 'šar gi·mir+dad~·mē bā·nû kib·rā~·ti\n'
    phone_path, ophone_path = _write_phone_pair_fixture(text)
    from pathlib import Path
    try:
        result = mod.process_file(phone_path, ophone_filename=ophone_path)
    finally:
        Path(phone_path).unlink(missing_ok=True)
        Path(ophone_path).unlink(missing_ok=True)

    prominence = result['original'].get('prominence_statistics') or {}
    return prominence == {
        'function_word_count': 0,
        'explicit_word_link_count': 1,
        'prominence_candidate_word_count': 4,
    }


def _test_process_file_missing_sibling_ophone_fails() -> bool:
    mod = _metrics_module()
    text = 'šar gi·mir+dad~·mē bā·nû kib·rā~·ti\n'
    phone_path, ophone_path = _write_phone_pair_fixture(text)
    from pathlib import Path
    try:
        Path(ophone_path).unlink(missing_ok=True)
        try:
            mod.process_file(phone_path)
            return False
        except ValueError as exc:
            return 'Derived original phone file does not exist' in str(exc)
    finally:
        Path(phone_path).unlink(missing_ok=True)
        Path(ophone_path).unlink(missing_ok=True)


def _test_percent_v_fallback_safe() -> bool:
    """Unit test: %V fallback remains correct without cached mora totals."""
    mod = _metrics_module()
    stats = {
        'syllable_counts': {
            'CV': 2,
            'VC:': 1,
            'VV:C': 1,
            mod.UNCLASSIFIED_SYLLABLE_TYPE: 5,
        },
        'mora_stats': {},
    }

    expected_vowel_morae = 2 * 1 + 1 * 1 + 1 * 3
    expected_total_morae = 2 * 1 + 1 * 3 + 1 * 4
    expected_percent_v = expected_vowel_morae / expected_total_morae * 100

    return __import__('math').isclose(
        mod.compute_percent_v_from_stats(stats),
        expected_percent_v,
        rel_tol=0.0,
        abs_tol=1e-12,
    )



def run_tests():
    """Run the full test suite by composing unit chunks.

    This preserves the original `run_tests()` entrypoint while allowing
    pytest to import and execute individual `_test_...` functions.
    """
    mod = _metrics_module()
    suites = [
        ("Word pattern matching", _test_word_pattern_matching),
        ("Tokenizer", _test_tokenizer),
        ("Word processing", _test_word_processing),
        ("Preprocessing", _test_preprocessing),
        ("Segment extraction", _test_segment_extraction),
        ("Distance calculation", _test_distance_calculation),
        ("Consonant distance definitions", _test_consonant_distance_definitions),
        ("Punctuation segment boundaries", _test_punctuation_marks_segment_boundaries),
        ("Pause metrics grouping", _test_pause_metrics_grouping),
        ("Unknown punctuation strict error", _test_unknown_punctuation_raises),
        ("Armored pause token classification", _test_armored_pause_token_classification),
        ("Mora totals and original speech", _test_mora_totals_and_original_speech),
        ("Table fields and CSV removal", _test_table_new_fields_and_no_csv),
        ("Small corpus metrics consistency", _test_small_corpus_metrics_consistency),
        ("Small corpus exact public values", _test_small_corpus_exact_surface_values),
        ("Phone-row prominence counts", _test_process_file_derives_prominence_counts_from_phone_rows),
        ("Missing sibling ophone fails", _test_process_file_missing_sibling_ophone_fails),
        ("Interval metrics zero-case", _test_interval_metrics_zero_case),
        ("%V fallback safety", _test_percent_v_fallback_safe),
    ]

    logger = mod.get_logger_with_fallback(__name__)
    utils = _utils_module()
    return utils.run_simple_selftest_suite(logger, 'Metrics', suites)