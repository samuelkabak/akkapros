from akkapros.lib.phonetize import (
    CONSONANT_CLOSURE,
    CONSONANT_FRICATIVE,
    CONSONANT_HIATUS,
    CONSONANT_SONORANT,
    CONSONANT_VOWEL_TRANSITION,
    EMPHATIC_CONSONANTS,
    INPUT_CHARACTER_LABELS,
    INPUT_CHARACTER_LENGTHS,
    INPUT_TO_REALIZATION_CODES,
    PHONE_ROW_DURATION_PLACEHOLDER,
    REALIZATION_CODE_METADATA,
    build_default_phonetize_verification_config,
    build_phone_streams,
    build_phone_rows,
    derive_original_tilde_text,
    parse_phone_row,
    render_phonetize_verification_lines,
    realize_phone_rows,
    realize_phone_streams,
    reconstruct_tilde_from_phone_rows,
    serialize_mbrola_rows,
    serialize_phone_row,
    verify_phonetize_config,
)


def test_canonical_consonant_sets_match_cr036() -> None:
    assert CONSONANT_HIATUS == set('˙')
    assert CONSONANT_VOWEL_TRANSITION == set('¨')
    assert CONSONANT_CLOSURE == set('bdgkptṭqʾ')
    assert CONSONANT_FRICATIVE == set('szšṣḥḫʿ')
    assert CONSONANT_SONORANT == set('lrmnwy')
    assert EMPHATIC_CONSONANTS == {'q', 'ṣ', 'ṭ'}


def test_input_inventory_and_realization_inventory_are_explicit() -> None:
    assert INPUT_CHARACTER_LABELS['ṣ'] == 'SUD'
    assert INPUT_CHARACTER_LABELS['˙'] == 'ARU'
    assert INPUT_CHARACTER_LABELS['¨'] == 'ENA'
    assert INPUT_CHARACTER_LENGTHS['ā'] == 'L'
    assert INPUT_TO_REALIZATION_CODES['ENA'] == ('WA', 'YI')
    assert REALIZATION_CODE_METADATA['SP'] == {
        'ipa': '|',
        'category': 'S',
        'type': 'S',
        'emphaticity': 'P',
    }


def test_build_phone_rows_emits_canonical_flat_line_contract() -> None:
    rows = build_phone_rows('ṣa')
    assert rows == [
        {
            'label': 'SUD',
            'category': 'C',
            'type': 'F',
            'length': 'S',
            'position': 'O',
            'boundary': 'N',
            'accent': 'F',
            'realization': 'SU',
            'duration': PHONE_ROW_DURATION_PLACEHOLDER,
            'text': 'ṣ',
        },
        {
            'label': 'AYA',
            'category': 'V',
            'type': 'L',
            'length': 'S',
            'position': 'N',
            'boundary': 'F',
            'accent': 'F',
            'realization': 'AO',
            'duration': PHONE_ROW_DURATION_PLACEHOLDER,
            'text': 'a',
        },
        {
            'label': 'ZEN',
            'category': 'S',
            'type': 'S',
            'length': 'L',
            'position': 'S',
            'boundary': 'N',
            'accent': 'P',
            'realization': 'ZP',
            'duration': PHONE_ROW_DURATION_PLACEHOLDER,
            'text': '<EOL>',
        },
    ]
    line = serialize_phone_row(rows[0])
    assert line == 'SUD-C-F-S-O-N-F-SU-0000:ṣ'
    assert parse_phone_row(line) == rows[0]


def test_boundaries_preserve_internal_enclitic_and_unit_edges() -> None:
    rows = build_phone_rows('šit·ku·nat-ma')
    assert [row['boundary'] for row in rows if row['boundary'] != 'N'] == ['I', 'I', 'E', 'F']
    assert reconstruct_tilde_from_phone_rows(rows) == 'šit·ku·nat-ma\n'


def test_internal_and_explicit_merges_round_trip() -> None:
    sample = 'u+ana&šar~·ri'
    rows = build_phone_rows(sample)
    assert reconstruct_tilde_from_phone_rows(rows) == sample + '\n'
    assert [row['boundary'] for row in rows if row['boundary'] in {'X', 'L', 'I', 'F'}] == ['X', 'L', 'I', 'F']


def test_pause_rows_and_transition_rows_use_canonical_codes() -> None:
    rows = build_phone_rows('a¨u,\n')
    assert rows[1]['label'] == 'ENA'
    assert rows[1]['type'] == 'T'
    assert rows[1]['realization'] == 'WA'
    assert rows[3]['label'] == 'SES'
    assert rows[3]['realization'] == 'SP'
    assert rows[3]['text'] == ','
    assert rows[4]['label'] == 'ZEN'
    assert rows[4]['realization'] == 'ZP'
    assert rows[4]['text'] == '<EOL>'


def test_original_stream_derivation_matches_cr039_examples() -> None:
    assert derive_original_tilde_text('u+ana&šar~.ri') == 'u+ana šar.ri'
    assert derive_original_tilde_text('gi.mir&dad~.mē') == 'gi.mir dad.mē'
    assert derive_original_tilde_text('šit·ku·nat-ma') == 'šit·ku·nat-ma'
    assert derive_original_tilde_text('ana+šar~.ri') == 'ana+šar.ri'
    assert derive_original_tilde_text('u&ana+šar~.ri') == 'u ana+šar.ri'


def test_dual_phone_streams_preserve_accentuated_and_original_forms() -> None:
    original_rows, accentuated_rows = build_phone_streams('u+ana&šar~·ri')

    assert reconstruct_tilde_from_phone_rows(accentuated_rows) == 'u+ana&šar~·ri\n'
    assert reconstruct_tilde_from_phone_rows(original_rows) == 'u+ana šar·ri\n'
    assert all(row['duration'] == PHONE_ROW_DURATION_PLACEHOLDER for row in original_rows)
    assert all(row['duration'] == PHONE_ROW_DURATION_PLACEHOLDER for row in accentuated_rows)


def test_original_stream_differs_only_by_deaccentuation_when_no_internal_merge() -> None:
    original_rows, accentuated_rows = build_phone_streams('ana+šar~.ri')

    assert reconstruct_tilde_from_phone_rows(original_rows) == 'ana+šar·ri\n'
    assert reconstruct_tilde_from_phone_rows(accentuated_rows) == 'ana+šar~·ri\n'


def test_missing_final_break_is_normalized_to_long_pause_row() -> None:
    rows = build_phone_rows('qat')

    assert rows[-1]['category'] == 'S'
    assert rows[-1]['length'] == 'L'
    assert rows[-1]['text'] == '<EOL>'
    assert reconstruct_tilde_from_phone_rows(rows) == 'qat\n'


def test_mixed_armored_punctuation_suite_prefers_long_pause() -> None:
    rows = build_phone_rows('at·tā⟦ ?!!! ⟧ā·lik')

    pause_rows = [row for row in rows if row['category'] == 'S']
    assert len(pause_rows) == 2
    assert pause_rows[0]['length'] == 'L'
    assert pause_rows[0]['text'] == '?!!!'


def test_armored_punctuation_is_accepted_by_phonetizer() -> None:
    rows = build_phone_rows('šar⟦ : ⟧ti·¨ā~m·tu')

    pause_rows = [row for row in rows if row['category'] == 'S']
    assert len(pause_rows) == 2
    assert pause_rows[0]['label'] == 'SES'
    assert pause_rows[0]['realization'] == 'SP'
    assert pause_rows[0]['text'] == ':'


def test_armored_punctuation_inherits_extra_chars_from_frontmatter() -> None:
    frontmatter = {
        'metadata': {
            'options': {
                'extra_short_punct_chars': 'o',
                'extra_long_punct_chars': '',
                'extra_short_punct_pattern': [],
                'extra_long_punct_pattern': [],
            }
        }
    }

    rows = build_phone_rows('šar⟦ o ⟧ti', input_frontmatter=frontmatter)

    pause_rows = [row for row in rows if row['category'] == 'S']
    assert len(pause_rows) == 2
    assert pause_rows[0]['label'] == 'SES'
    assert pause_rows[0]['text'] == 'o'


def test_unknown_armored_content_fails_in_phonetizer() -> None:
    try:
        build_phone_rows('šar⟦ @ ⟧ti')
        raise AssertionError('Expected unsupported armored phonetizer content to fail')
    except ValueError as exc:
        assert '⟦ @ ⟧' in str(exc)


def test_phase2_baseline_realization_uses_non_zero_durations() -> None:
    rows = build_phone_rows('qat')

    report = realize_phone_rows(rows, allow_accentuation=False)

    assert [row['duration'] for row in rows[:-1]] == ['0108', '0085', '0103']
    assert rows[-1]['length'] == 'L'
    assert int(rows[-1]['duration']) >= 1200
    assert report['one_mora_ref'] == 152.5
    assert report['two_mora_ref'] == 305.0
    assert report['three_mora_ref'] == 457.5
    assert report['drift']['label'] in {'Ahead (rushing)', 'On the beat', 'Behind (dragging)'}


def test_phase2_same_consonant_pair_honors_geminate_policy() -> None:
    corrective_rows = build_phone_rows('at·ta')
    cumulative_rows = build_phone_rows('at·ta')
    cumulative_config = {
        'process': {
            'timing_model': {
                'geminate_policy': 'cumulative',
            },
        }
    }

    realize_phone_rows(corrective_rows, allow_accentuation=False)
    realize_phone_rows(cumulative_rows, cumulative_config, allow_accentuation=False)

    assert corrective_rows[1]['duration'] == '0103'
    assert corrective_rows[2]['duration'] == '0092'
    assert cumulative_rows[1]['duration'] == '0103'
    assert cumulative_rows[2]['duration'] == '0108'
    assert corrective_rows[3]['duration'] != PHONE_ROW_DURATION_PLACEHOLDER
    assert cumulative_rows[3]['duration'] != PHONE_ROW_DURATION_PLACEHOLDER


def test_phase2_supports_all_active_accent_classes() -> None:
    extensible = {
        'process': {
            'timing_model': {
                'drift_policy': 'extensible',
                'drift_tolerance': 0,
            },
        }
    }
    samples = ['b~a', 'bā~', 'bat~', 'bāt~']

    for sample in samples:
        rows = build_phone_rows(sample)
        report = realize_phone_rows(rows, extensible, allow_accentuation=True)
        assert all(row['duration'] != PHONE_ROW_DURATION_PLACEHOLDER for row in rows)
        assert report['drift']['max'] >= 0


def test_phase2_pause_discharge_and_stream_reports_are_emitted() -> None:
    config = {
        'process': {
            'timing_model': {
                'drift_policy': 'extensible',
                'drift_tolerance': 0,
            },
        }
    }

    (original_rows, original_report), (accentuated_rows, accentuated_report) = realize_phone_streams(
        'b~a, bāt~\n',
        config,
    )

    assert any(row['category'] == 'S' and row['duration'] != PHONE_ROW_DURATION_PLACEHOLDER for row in original_rows)
    assert any(row['category'] == 'S' and row['duration'] != PHONE_ROW_DURATION_PLACEHOLDER for row in accentuated_rows)
    assert original_report['drift']['stddev'] >= 0
    assert accentuated_report['drift']['stddev'] >= 0
    assert 'label' in original_report['drift'] and 'label' in accentuated_report['drift']


def test_mbrola_rows_use_baseline_and_stress_rise_f0() -> None:
    original_rows, accentuated_rows = build_phone_streams('at·ta~')
    realize_phone_rows(original_rows, allow_accentuation=False)
    realize_phone_rows(accentuated_rows, allow_accentuation=True)

    original_lines = serialize_mbrola_rows(original_rows, accentuated=False).strip().splitlines()
    accentuated_lines = serialize_mbrola_rows(accentuated_rows, accentuated=True).strip().splitlines()

    assert all(len(line.split()) == 3 for line in original_lines)
    assert all(line.endswith(' 120') for line in original_lines)
    assert any(line.endswith(' 135') for line in accentuated_lines)


def test_mbrola_rows_merge_adjacent_identical_symbol_and_frequency() -> None:
    rows = build_phone_rows('at·ta')
    realize_phone_rows(rows, allow_accentuation=False)

    lines = serialize_mbrola_rows(rows, accentuated=False).strip().splitlines()

    assert any(line.startswith('TA 195 120') for line in lines)


def test_verification_rejects_non_positive_intonation_f0() -> None:
    result = verify_phonetize_config({'process': {'intonation': {'f0': 0}}})

    assert result.status == 'failure'
    assert any(issue.path == 'phonetize.process.intonation.f0' for issue in result.failures)


def test_phase2_short_pause_can_leave_residual_drift_when_band_blocks_full_discharge() -> None:
    config = {
        'process': {
            'timing_model': {
                'drift_policy': 'extensible',
                'drift_tolerance': 0,
                'durations': {
                    'cvc_reference': 200,
                    'pauses': {
                        'short': {
                            'min': 600,
                            'max': 600,
                        },
                    },
                },
            },
        },
    }

    rows = build_phone_rows('qat,')
    report = realize_phone_rows(rows, config, allow_accentuation=False)

    pause_rows = [row for row in rows if row['category'] == 'S']
    assert len(pause_rows) == 2
    assert pause_rows[0]['length'] == 'S'
    assert pause_rows[0]['duration'] == '0600'
    assert pause_rows[1]['length'] == 'L'
    assert report['drift']['current'] == 0
    assert report['drift']['label'] == 'On the beat'


def test_phase2_long_pause_resets_running_drift_to_zero() -> None:
    config = {
        'process': {
            'timing_model': {
                'drift_policy': 'extensible',
                'drift_tolerance': 0,
                'durations': {
                    'cvc_reference': 200,
                    'pauses': {
                        'short': {
                            'min': 600,
                            'max': 600,
                        },
                        'long': {
                            'min': 1200,
                            'max': 1780,
                        },
                    },
                },
            },
        },
    }

    rows = build_phone_rows('qat\n')
    report = realize_phone_rows(rows, config, allow_accentuation=False)

    pause_rows = [row for row in rows if row['category'] == 'S']
    assert len(pause_rows) == 1
    assert pause_rows[0]['length'] == 'L'
    assert 1200 <= int(pause_rows[0]['duration']) <= 1780
    assert report['drift']['current'] == 0
    assert report['drift']['label'] == 'On the beat'


def test_phase2_extensible_reports_drift_summary_and_extensions() -> None:
    rows = build_phone_rows('bā~')

    report = realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_policy': 'extensible',
                    'drift_tolerance': 0,
                },
            }
        },
        allow_accentuation=True,
    )

    assert set(report['drift']) == {'max', 'mean', 'stddev', 'current', 'label'}
    assert report['drift']['max'] > 0
    assert report['drift_extension_count'] > 0
    assert report['max_drift_extension'] > 0


def test_phase2_strict_mode_can_finish_on_normalized_terminal_long_pause() -> None:
    rows = build_phone_rows('bā~')

    report = realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_policy': 'strict',
                },
            },
        },
        allow_accentuation=True,
    )

    assert report['drift']['current'] == 0
    assert report['drift']['label'] == 'On the beat'


def test_shared_verification_uses_extensible_canonical_drift_default() -> None:
    defaults = build_default_phonetize_verification_config()

    assert defaults['process']['timing_model']['accentuation_distribution_policy'] == '85_15'
    assert defaults['process']['timing_model']['drift_policy'] == 'extensible'


def test_shared_verification_warns_on_high_pause_ratio() -> None:
    result = verify_phonetize_config({'process': {'timing_model': {'speech': {'pause_ratio': 71}}}})
    lines = render_phonetize_verification_lines(result)

    assert result.status == 'pass-with-warnings'
    assert not result.failures
    assert any('phonetize.process.timing_model.speech.pause_ratio' in line for line in lines)
    assert any('pause_ratio > 70' in line for line in lines)


def test_shared_verification_blocks_invalid_pause_ratio() -> None:
    result = verify_phonetize_config({'process': {'timing_model': {'speech': {'pause_ratio': 100}}}})
    lines = render_phonetize_verification_lines(result)

    assert result.status == 'failure'
    assert result.failures
    assert any('0 < pause_ratio < 100' in line for line in lines)