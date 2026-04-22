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