from __future__ import annotations


def _phonetize_module():
    from akkapros.lib import phonetize

    return phonetize


def run_tests() -> bool:
    mod = _phonetize_module()
    cases = [
        lambda: mod.CONSONANT_HIATUS == set('˙') and mod.CONSONANT_VOWEL_TRANSITION == set('¨'),
        lambda: mod.INPUT_CHARACTER_LABELS['ṣ'] == 'SUD' and mod.INPUT_CHARACTER_LENGTHS['û'] == 'L',
        lambda: mod.REALIZATION_CODE_METADATA['SP']['category'] == 'S' and mod.INPUT_TO_REALIZATION_CODES['ENA'] == ('WA', 'YI'),
        lambda: mod.REALIZATION_CODE_METADATA[mod.RESYNC_PAUSE_REALIZATION]['ipa'] == '.' and mod.INPUT_TO_REALIZATION_CODES[mod.RESYNC_PAUSE_LABEL] == (mod.RESYNC_PAUSE_REALIZATION,),
        lambda: mod.derive_original_tilde_text('u+ana&šar~.ri') == 'u+ana šar.ri',
        lambda: _test_emphatic_vowel_and_row_format(),
        lambda: _test_resync_pause_row_contract(),
        lambda: _test_boundary_reconstruction(),
        lambda: _test_transition_resolution(),
        lambda: _test_dual_stream_generation(),
        lambda: _test_finalized_stream_generation(),
        lambda: _test_intonation_normalization_and_assignment(),
        lambda: _test_shared_verification(),
        lambda: _test_mbrola_export(),
        lambda: _test_choose_ultraheavy_transition(),
        lambda: _test_expand_ultraheavy_rows_no_circumflex(),
        lambda: _test_expand_ultraheavy_rows_one_circumflex(),
        lambda: _test_expand_ultraheavy_rows_multiple_circumflex(),
        lambda: _test_expand_ultraheavy_rows_zero_split(),
        lambda: _test_expand_ultraheavy_rows_timing(),
        lambda: _test_expand_ultraheavy_rows_rising_intonation(),
        lambda: _test_expand_ultraheavy_rows_constant_intonation(),
        lambda: _test_expand_ultraheavy_rows_accent_preserved(),
        lambda: _test_expand_ultraheavy_rows_emphatic_preserved(),
        lambda: _test_produce_ultraheavy_rows_disabled(),
        lambda: _test_produce_ultraheavy_rows_enabled(),
    ]
    return all(case() for case in cases)


def _test_emphatic_vowel_and_row_format() -> bool:
    mod = _phonetize_module()
    rows = mod.build_phone_rows('qā')
    if rows[0]['realization'] != 'QU' or rows[1]['realization'] != 'AO':
        return False
    line = mod.serialize_phone_row(rows[0])
    return mod.parse_phone_row(line) == rows[0] and rows[0]['duration'] == mod.PHONE_ROW_DURATION_PLACEHOLDER


def _test_resync_pause_row_contract() -> bool:
    mod = _phonetize_module()
    row = mod._new_resync_pause_row()
    return (
        row['label'] == mod.RESYNC_PAUSE_LABEL
        and row['type'] == mod.RESYNC_PAUSE_TYPE
        and row['realization'] == mod.RESYNC_PAUSE_REALIZATION
        and mod.parse_phone_row(mod.serialize_phone_row(row))['text'] == mod.RESYNC_PAUSE_TEXT
    )


def _test_boundary_reconstruction() -> bool:
    mod = _phonetize_module()
    sample = 'šit·ku·nat-ma'
    rows = mod.build_phone_rows(sample)
    return mod.reconstruct_tilde_from_phone_rows(rows) == sample + '\n'


def _test_transition_resolution() -> bool:
    mod = _phonetize_module()
    rows = mod.build_phone_rows('a¨u')
    transition = next(row for row in rows if row['label'] == 'ENA')
    return transition['realization'] == 'WA'


def _test_dual_stream_generation() -> bool:
    mod = _phonetize_module()
    original_rows, accentuated_rows = mod.build_phone_streams('u+ana&šar~·ri')
    return (
        mod.reconstruct_tilde_from_phone_rows(original_rows) == 'u+ana šar·ri\n'
        and mod.reconstruct_tilde_from_phone_rows(accentuated_rows) == 'u+ana&šar~·ri\n'
    )


def _test_finalized_stream_generation() -> bool:
    mod = _phonetize_module()
    config = {'process': {'timing_model': {'drift_tolerance': 0}}}
    (original_rows, original_report), (accentuated_rows, accentuated_report) = mod.realize_phone_streams(
        'b~a, bāt~\n',
        config,
    )
    return (
        any(row['duration'] != mod.PHONE_ROW_DURATION_PLACEHOLDER for row in original_rows)
        and any(row['duration'] != mod.PHONE_ROW_DURATION_PLACEHOLDER for row in accentuated_rows)
        and all(row['intonation'] for row in original_rows)
        and all(row['intonation'] for row in accentuated_rows)
        and 'stddev' in original_report['unit_drift']
        and 'stddev' in accentuated_report['unit_drift']
    )


def _test_intonation_normalization_and_assignment() -> bool:
    mod = _phonetize_module()
    rows = mod.build_phone_rows('at·ta~?!')
    mod.realize_phone_rows(rows, allow_accentuation=True)
    mod.realize_row_intonation(rows, accentuated=True)
    return (
        mod._normalize_intonation_token('H2') == 'H2C'
        and mod._normalize_intonation_token('R1') == 'R1L'
        and rows[-2]['type'] == 'Q'
        and rows[-2]['intonation'] == 'H3C'
        and rows[-1]['type'] == 'S'
        and all(row['intonation'] == 'M0C' for row in rows[:2])
        and all(row['intonation'] == 'H3C' for row in rows[2:-1])
    )


def _test_shared_verification() -> bool:
    mod = _phonetize_module()
    defaults = mod.build_default_phonetize_verification_config()
    rendered = mod.render_phonetize_verification_lines(mod.verify_phonetize_config())
    return (
        'speech' not in defaults['process']['timing_model']
        and all('phonetize.process.timing_model.speech' not in line for line in rendered)
    )


def _test_mbrola_export() -> bool:
    mod = _phonetize_module()
    original_rows, accentuated_rows = mod.build_phone_streams('at~·ta')
    mod.realize_phone_rows(original_rows, allow_accentuation=False)
    mod.realize_phone_rows(accentuated_rows, allow_accentuation=True)
    mod.realize_row_intonation(original_rows, accentuated=False)
    mod.realize_row_intonation(accentuated_rows, accentuated=True)
    original_lines = mod.serialize_mbrola_rows(original_rows, accentuated=False).strip().splitlines()
    accentuated_lines = mod.serialize_mbrola_rows(accentuated_rows, accentuated=True).strip().splitlines()
    return (
        len(original_lines) > 0
        and len(accentuated_lines) > 0
        and all(len(line.split()) >= 3 for line in original_lines + accentuated_lines)
        and any(line.endswith(' 135') for line in accentuated_lines)
    )


def _test_choose_ultraheavy_transition() -> bool:
    mod = _phonetize_module()
    return (
        mod._choose_ultraheavy_transition('AA') == 'AL'
        and mod._choose_ultraheavy_transition('AO') == 'AL'
        and mod._choose_ultraheavy_transition('UU') == 'WA'
        and mod._choose_ultraheavy_transition('UO') == 'WA'
        and mod._choose_ultraheavy_transition('EE') == 'YI'
        and mod._choose_ultraheavy_transition('II') == 'YI'
        and mod._choose_ultraheavy_transition('EO') == 'YI'
        and mod._choose_ultraheavy_transition('IO') == 'YI'
        and mod._choose_ultraheavy_transition('XX') == 'AL'  # fallback
    )


def _make_circumflex_row(
    mod,
    label: str = 'AWI',
    realization: str = 'AA',
    duration: str = '0180',
    intonation: str = 'R1L',
    boundary: str = 'F',
    accent: str = 'F',
    text: str = 'â',
) -> dict[str, str]:
    return {
        'label': label,
        'category': 'V',
        'type': 'H',
        'length': 'L',
        'position': 'N',
        'boundary': boundary,
        'accent': accent,
        'realization': realization,
        'duration': duration,
        'drift': mod.PHONE_ROW_DRIFT_NEUTRAL,
        'intonation': intonation,
        'text': text,
    }


def _test_expand_ultraheavy_rows_no_circumflex() -> bool:
    mod = _phonetize_module()
    rows = [
        {'label': 'QU', 'category': 'C', 'type': 'F', 'length': 'S', 'position': 'O',
         'boundary': 'N', 'accent': 'F', 'realization': 'QU', 'duration': '0080',
         'drift': mod.PHONE_ROW_DRIFT_NEUTRAL, 'intonation': 'M0C', 'text': 'q'},
        {'label': 'AWI', 'category': 'V', 'type': 'H', 'length': 'L', 'position': 'N',
         'boundary': 'F', 'accent': 'F', 'realization': 'AA', 'duration': '0180',
         'drift': mod.PHONE_ROW_DRIFT_NEUTRAL, 'intonation': 'R1L', 'text': 'ā'},
    ]
    expanded = mod._expand_ultraheavy_rows(rows, 25)
    # 'ā' is not a circumflex vowel (label AWI but input is ā, not â)
    # Actually AWI is the label for â, so this should expand
    # Let's use a non-circumflex label instead
    rows2 = [
        {'label': 'QU', 'category': 'C', 'type': 'F', 'length': 'S', 'position': 'O',
         'boundary': 'N', 'accent': 'F', 'realization': 'QU', 'duration': '0080',
         'drift': mod.PHONE_ROW_DRIFT_NEUTRAL, 'intonation': 'M0C', 'text': 'q'},
        {'label': 'BA', 'category': 'V', 'type': 'H', 'length': 'L', 'position': 'N',
         'boundary': 'F', 'accent': 'F', 'realization': 'AA', 'duration': '0180',
         'drift': mod.PHONE_ROW_DRIFT_NEUTRAL, 'intonation': 'R1L', 'text': 'ā'},
    ]
    expanded2 = mod._expand_ultraheavy_rows(rows2, 25)
    return len(expanded2) == 2 and expanded2[0]['label'] == 'QU' and expanded2[1]['label'] == 'BA'


def _test_expand_ultraheavy_rows_one_circumflex() -> bool:
    mod = _phonetize_module()
    rows = [
        {'label': 'QU', 'category': 'C', 'type': 'F', 'length': 'S', 'position': 'O',
         'boundary': 'N', 'accent': 'F', 'realization': 'QU', 'duration': '0080',
         'drift': mod.PHONE_ROW_DRIFT_NEUTRAL, 'intonation': 'M0C', 'text': 'q'},
        _make_circumflex_row(mod, label='AWI', realization='AA', duration='0180', intonation='R1L', text='â'),
    ]
    expanded = mod._expand_ultraheavy_rows(rows, 25)
    return len(expanded) == 4  # 1 consonant + 3 expanded rows


def _test_expand_ultraheavy_rows_multiple_circumflex() -> bool:
    mod = _phonetize_module()
    rows = [
        _make_circumflex_row(mod, label='AWI', realization='AA', duration='0180', intonation='R1L', text='â'),
        {'label': 'QU', 'category': 'C', 'type': 'F', 'length': 'S', 'position': 'O',
         'boundary': 'N', 'accent': 'F', 'realization': 'QU', 'duration': '0080',
         'drift': mod.PHONE_ROW_DRIFT_NEUTRAL, 'intonation': 'M0C', 'text': 'q'},
        _make_circumflex_row(mod, label='UWI', realization='UU', duration='0200', intonation='F1L', text='û'),
    ]
    expanded = mod._expand_ultraheavy_rows(rows, 25)
    return len(expanded) == 7  # 2 circumflex * 3 + 1 consonant


def _test_expand_ultraheavy_rows_zero_split() -> bool:
    mod = _phonetize_module()
    # Z = 30, T = 25, Z - T = 5, so expansion should still happen
    # For Z <= T, use Z = 20, T = 25
    rows = [
        _make_circumflex_row(mod, label='AWI', realization='AA', duration='0020', intonation='R1L', text='â'),
    ]
    expanded = mod._expand_ultraheavy_rows(rows, 25)
    return len(expanded) == 1  # kept as-is because Z <= T


def _test_expand_ultraheavy_rows_timing() -> bool:
    mod = _phonetize_module()
    Z = 180
    T = 25
    rows = [
        _make_circumflex_row(mod, label='AWI', realization='AA', duration='0180', intonation='R1L', text='â'),
    ]
    expanded = mod._expand_ultraheavy_rows(rows, T)
    if len(expanded) != 3:
        return False
    U1 = int(0.5 * (Z - T))  # floor = 77
    U2 = int(0.5 * (Z - T) + 0.5)  # ceiling = 78
    d1 = int(expanded[0]['duration'])
    d2 = int(expanded[1]['duration'])
    d3 = int(expanded[2]['duration'])
    return d1 == U1 and d2 == T and d3 == U2 and (d1 + d2 + d3) == Z


def _test_expand_ultraheavy_rows_rising_intonation() -> bool:
    mod = _phonetize_module()
    rows = [
        _make_circumflex_row(mod, label='AWI', realization='AA', duration='0180', intonation='R1L', text='â'),
    ]
    expanded = mod._expand_ultraheavy_rows(rows, 25)
    if len(expanded) != 3:
        return False
    # R1L: start=120, end=135, mid_freq = 120 + 15 * (77/180) = 126
    # Row 1: R1L from 120 to 126
    # Row 2: M0C constant at 126
    # Row 3: R1L from 126 to 135
    return (
        expanded[0]['intonation'] != 'M0C'  # should be rising
        and expanded[1]['intonation'] == 'M0C'  # transition is constant
        and expanded[2]['intonation'] != 'M0C'  # should be rising
    )


def _test_expand_ultraheavy_rows_constant_intonation() -> bool:
    mod = _phonetize_module()
    rows = [
        _make_circumflex_row(mod, label='AWI', realization='AA', duration='0180', intonation='H2C', text='â'),
    ]
    expanded = mod._expand_ultraheavy_rows(rows, 25)
    if len(expanded) != 3:
        return False
    # H2C: constant at 135 Hz
    # All three segments should be constant
    return (
        expanded[0]['intonation'] == 'H2C'
        and expanded[1]['intonation'] == 'M0C'
        and expanded[2]['intonation'] == 'H2C'
    )


def _test_expand_ultraheavy_rows_accent_preserved() -> bool:
    mod = _phonetize_module()
    rows = [
        _make_circumflex_row(mod, label='AWI', realization='AA', duration='0180', intonation='R1L', accent='T', text='â'),
    ]
    expanded = mod._expand_ultraheavy_rows(rows, 25)
    if len(expanded) != 3:
        return False
    # First segment preserves accent, transition and second have no accent
    return (
        expanded[0]['accent'] == 'T'
        and expanded[1]['accent'] == 'F'
        and expanded[2]['accent'] == 'F'
    )


def _test_expand_ultraheavy_rows_emphatic_preserved() -> bool:
    mod = _phonetize_module()
    rows = [
        _make_circumflex_row(mod, label='AWI', realization='AO', duration='0180', intonation='R1L', text='â'),
    ]
    expanded = mod._expand_ultraheavy_rows(rows, 25)
    if len(expanded) != 3:
        return False
    # Both vowel segments should use emphatic realization AO
    # Transition should be AL (for AA/AO)
    return (
        expanded[0]['realization'] == 'AO'
        and expanded[1]['realization'] == 'AL'
        and expanded[2]['realization'] == 'AO'
    )


def _test_produce_ultraheavy_rows_disabled() -> bool:
    mod = _phonetize_module()
    rows = [
        _make_circumflex_row(mod, label='AWI', realization='AA', duration='0180', intonation='R1L', text='â'),
    ]
    config = {'process': {'realization': {'ultraheavy_hiatus_enable': False}}}
    result = mod.produce_ultraheavy_rows(rows, config)
    return result is rows  # returns original rows when disabled


def _test_produce_ultraheavy_rows_enabled() -> bool:
    mod = _phonetize_module()
    rows = [
        _make_circumflex_row(mod, label='AWI', realization='AA', duration='0180', intonation='R1L', text='â'),
    ]
    config = {
        'process': {
            'realization': {'ultraheavy_hiatus_enable': True},
            'timing_model': {
                'durations': {
                    'consonants': {
                        'sonorant': {
                            'special_realization': {
                                'vowel_transition': 25,
                            },
                        },
                    },
                },
            },
        },
    }
    result = mod.produce_ultraheavy_rows(rows, config)
    return result is not rows and len(result) == 3
