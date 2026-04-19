import re

import pytest

from akkapros.lib import constants as lib_constants
from akkapros.lib.phonetize import (
    ACCENTUATION_DISTRIBUTION_CHOICES,
    CONSONANT_CLOSURE,
    CONSONANT_FRICATIVE,
    CONSONANT_HIATUS,
    CONSONANT_SONORANT,
    CONSONANT_VOWEL_TRANSITION,
    EMPHATIC_CONSONANTS,
    INPUT_CHARACTER_LABELS,
    INPUT_CHARACTER_LENGTHS,
    INPUT_TO_REALIZATION_CODES,
    MINI_PAUSE_LABEL,
    MINI_PAUSE_REALIZATION,
    MINI_PAUSE_TEXT,
    MINI_PAUSE_TYPE,
    PHONE_ROW_DRIFT_NEUTRAL,
    PHONE_ROW_DURATION_PLACEHOLDER,
    REALIZATION_CODE_ROWS,
    REALIZATION_CODE_METADATA,
    _apply_accent_increment,
    _adjacent_accent_index,
    _analyze_syllable,
    _consonant_timing_key,
    _format_row_drift_token,
    _is_chrono_checkpoint_row,
    _normalize_drift_to_nearest_branch,
    _partition_phone_units,
    _maybe_insert_mini_pause,
    _merge_phonetize_config,
    _primary_accent_index,
    _round_half_up,
    _resolve_synchronization_basis,
    _runtime_view_phonetize_config,
    _validate_chrono_checkpoints,
    build_default_phonetize_verification_config,
    build_phone_streams,
    build_phone_rows,
    derive_original_tilde_text,
    parse_phone_row,
    render_phonetize_verification_lines,
    realize_row_intonation,
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
        'mbrola_xsampa': '_',
        'category': 'S',
        'type': 'S',
        'emphaticity': 'P',
    }
    assert INPUT_TO_REALIZATION_CODES[MINI_PAUSE_LABEL] == (MINI_PAUSE_REALIZATION,)
    assert REALIZATION_CODE_METADATA[MINI_PAUSE_REALIZATION] == {
        'ipa': '.',
        'mbrola_xsampa': '_',
        'category': 'S',
        'type': 'S',
        'emphaticity': 'P',
    }


def test_realization_inventory_exposes_canonical_mbrola_xsampa_mapping() -> None:
    row_map = {code: (ipa, mbrola_xsampa) for code, ipa, mbrola_xsampa, *_rest in REALIZATION_CODE_ROWS}

    assert row_map['GI'] == ('ɡ', 'g')
    assert row_map['ET'] == ('ħ', 'X')
    assert row_map['HE'] == ('x', 'x')
    assert row_map['AL'] == ('ʔ', '?')
    assert row_map['AO'] == ('ɑ', 'a.')
    assert row_map[MINI_PAUSE_REALIZATION] == ('.', '_')
    assert row_map['SP'] == ('|', '_')
    assert row_map['ZP'] == ('‖', '_')


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
            'drift': PHONE_ROW_DRIFT_NEUTRAL,
            'intonation': 'M0C',
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
            'drift': PHONE_ROW_DRIFT_NEUTRAL,
            'intonation': 'M0C',
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
            'drift': PHONE_ROW_DRIFT_NEUTRAL,
            'intonation': 'M0C',
            'text': '<EOL>',
        },
    ]
    line = serialize_phone_row(rows[0])
    assert line == 'SUD|C|F|S|O|N|F|SU|0000|+000|M0C|ṣ'
    assert parse_phone_row(line) == rows[0]


def test_row_drift_token_format_is_canonical() -> None:
    assert _format_row_drift_token(0.0) == '+000'
    assert _format_row_drift_token(-12.2) == '-012'
    assert _format_row_drift_token(3.4) == '+003'

    with pytest.raises(ValueError, match='exceeds three digits'):
        _format_row_drift_token(1000.0)


def test_parse_phone_row_rejects_legacy_row_shape() -> None:
    with pytest.raises(ValueError, match='Invalid phone row'):
        parse_phone_row('SUD-C-F-S-O-N-F-SU-0000-M0C:ṣ')


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
    assert rows[3]['type'] == 'C'
    assert rows[3]['realization'] == 'SP'
    assert rows[3]['text'] == ','
    assert rows[4]['label'] == 'ZEN'
    assert rows[4]['type'] == 'S'
    assert rows[4]['realization'] == 'ZP'
    assert rows[4]['text'] == '<EOL>'


def test_consecutive_newlines_coalesce_without_changing_newline_row_placement() -> None:
    single_rows = build_phone_rows('ba\nma')
    repeated_rows = build_phone_rows('ba\n\n\nma')

    single_newline_rows = [row for row in single_rows if row['category'] == 'S' and '<EOL>' in row['text']]
    repeated_newline_rows = [row for row in repeated_rows if row['category'] == 'S' and '<EOL>' in row['text']]
    single_newline_positions = [index for index, row in enumerate(single_rows) if row['category'] == 'S' and '<EOL>' in row['text']]
    repeated_newline_positions = [index for index, row in enumerate(repeated_rows) if row['category'] == 'S' and '<EOL>' in row['text']]

    assert len(single_newline_rows) == len(repeated_newline_rows) == 2
    assert single_newline_positions == repeated_newline_positions
    assert [row['text'] for row in single_newline_rows] == ['<EOL>', '<EOL>']
    assert [row['text'] for row in repeated_newline_rows] == ['<EOL><EOL><EOL>', '<EOL>']


def test_repeated_eol_text_reconstructs_repeated_newlines() -> None:
    rows = build_phone_rows('ba\n\n\nma')

    assert reconstruct_tilde_from_phone_rows(rows) == 'ba\n\n\nma\n'


def test_punctuation_and_repeated_newlines_stay_separate_pause_rows() -> None:
    rows = build_phone_rows('ba?!\n\nma')

    pause_rows = [row for row in rows if row['category'] == 'S']

    assert len(pause_rows) == 3
    assert pause_rows[0]['text'] == '?!'
    assert pause_rows[1]['text'] == '<EOL><EOL>'
    assert pause_rows[2]['text'] == '<EOL>'


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
    assert pause_rows[0]['type'] == 'Q'
    assert pause_rows[0]['text'] == '?!!!'


def test_armored_punctuation_is_accepted_by_phonetizer() -> None:
    rows = build_phone_rows('šar⟦ : ⟧ti·¨ā~m·tu')

    pause_rows = [row for row in rows if row['category'] == 'S']
    assert len(pause_rows) == 2
    assert pause_rows[0]['label'] == 'SES'
    assert pause_rows[0]['type'] == 'C'
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
    assert pause_rows[0]['type'] == 'I'
    assert pause_rows[0]['text'] == 'o'


def test_unknown_armored_punctuation_maps_to_internal_pause_type() -> None:
    rows = build_phone_rows('šar⟦ @ ⟧ti')

    pause_rows = [row for row in rows if row['category'] == 'S']
    assert len(pause_rows) == 2
    assert pause_rows[0]['type'] == 'I'
    assert pause_rows[0]['text'] == '@'


def test_grouped_punctuation_suite_uses_cr050_precedence() -> None:
    rows = build_phone_rows('at?! ...: \n')

    pause_rows = [row for row in rows if row['category'] == 'S']
    assert [row['type'] for row in pause_rows] == ['Q', 'C', 'S']
    assert [row['length'] for row in pause_rows] == ['L', 'S', 'L']


def test_phase2_baseline_realization_uses_non_zero_durations() -> None:
    rows = build_phone_rows('qat')

    report = realize_phone_rows(rows, allow_accentuation=False)

    assert [row['duration'] for row in rows[:-1]] == ['0089', '0110', '0087']
    assert [row['drift'] for row in rows[:2]] == ['+000', '+000']
    assert rows[2]['drift'].startswith(('-', '+'))
    assert rows[-1]['length'] == 'L'
    assert rows[-1]['drift'] == _format_row_drift_token(report['unit_drift']['current'])
    assert int(rows[-1]['duration']) >= 1200
    assert report['one_mora_ref'] == 150.0
    assert report['two_mora_ref'] == 300.0
    assert report['three_mora_ref'] == 450.0
    assert report['unit_drift']['label'] in {'Ahead (rushing)', 'On the beat', 'Behind (dragging)'}


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

    assert corrective_rows[1]['duration'] == '0087'
    assert corrective_rows[2]['duration'] == '0088'
    assert cumulative_rows[1]['duration'] == '0087'
    assert cumulative_rows[2]['duration'] == '0089'
    assert corrective_rows[3]['duration'] != PHONE_ROW_DURATION_PLACEHOLDER
    assert cumulative_rows[3]['duration'] != PHONE_ROW_DURATION_PLACEHOLDER


def test_phase2_supports_all_active_accent_classes() -> None:
    extensible = {'process': {'timing_model': {'drift_tolerance': 0}}}
    samples = ['b~a', 'bā~', 'bat~', 'bāt~']

    for sample in samples:
        rows = build_phone_rows(sample)
        report = realize_phone_rows(rows, extensible, allow_accentuation=True)
        assert all(row['duration'] != PHONE_ROW_DURATION_PLACEHOLDER for row in rows)
        assert report['unit_drift']['max'] >= 0


def test_phase2_pause_discharge_and_stream_reports_are_emitted() -> None:
    config = {'process': {'timing_model': {'drift_tolerance': 0}}}

    (original_rows, original_report), (accentuated_rows, accentuated_report) = realize_phone_streams(
        'b~a, bāt~\n',
        config,
    )

    assert any(row['category'] == 'S' and row['duration'] != PHONE_ROW_DURATION_PLACEHOLDER for row in original_rows)
    assert any(row['category'] == 'S' and row['duration'] != PHONE_ROW_DURATION_PLACEHOLDER for row in accentuated_rows)
    assert all(re.fullmatch(r'[+-]\d{3}', row['drift']) for row in original_rows)
    assert all(re.fullmatch(r'[+-]\d{3}', row['drift']) for row in accentuated_rows)
    assert original_report['unit_drift']['stddev'] >= 0
    assert accentuated_report['unit_drift']['stddev'] >= 0
    assert 'label' in original_report['unit_drift'] and 'label' in accentuated_report['unit_drift']


def test_phase2_resolves_synchronization_basis_from_mora_mode_and_stream() -> None:
    config = {
        'timing_model': {
            'durations': {
                'cvc_reference': 305,
            }
        }
    }
    bi_frontmatter = {'metadata': {'options': {'mora_mode': 'bi'}}}
    mono_frontmatter = {'metadata': {'options': {'mora_mode': 'mono'}}}

    assert _resolve_synchronization_basis(
        config,
        allow_accentuation=True,
        input_frontmatter=bi_frontmatter,
    ) == 305.0
    assert _resolve_synchronization_basis(
        config,
        allow_accentuation=True,
        input_frontmatter=mono_frontmatter,
    ) == 152.5
    assert _resolve_synchronization_basis(
        config,
        allow_accentuation=False,
        input_frontmatter=bi_frontmatter,
    ) == 152.5


def test_phase2_pause_target_uses_half_beat_for_mono_and_original_streams() -> None:
    config = {
        'process': {
            'timing_model': {
                'drift_tolerance': 0,
                'durations': {
                    'cvc_reference': 305,
                    'pauses': {
                        'short': {
                            'min': 600,
                            'max': 850,
                        },
                    },
                },
            },
        },
    }
    bi_frontmatter = {'metadata': {'options': {'mora_mode': 'bi'}}}
    mono_frontmatter = {'metadata': {'options': {'mora_mode': 'mono'}}}

    bi_rows = build_phone_rows('qat,')
    mono_rows = build_phone_rows('qat,')
    original_rows = build_phone_rows('qat,')

    realize_phone_rows(
        bi_rows,
        config,
        allow_accentuation=True,
        input_frontmatter=bi_frontmatter,
    )
    realize_phone_rows(
        mono_rows,
        config,
        allow_accentuation=True,
        input_frontmatter=mono_frontmatter,
    )
    realize_phone_rows(
        original_rows,
        config,
        allow_accentuation=False,
        input_frontmatter=bi_frontmatter,
    )

    bi_short_pause = next(row for row in bi_rows if row['category'] == 'S' and row['text'] == ',')
    mono_short_pause = next(row for row in mono_rows if row['category'] == 'S' and row['text'] == ',')
    original_short_pause = next(row for row in original_rows if row['category'] == 'S' and row['text'] == ',')

    assert bi_short_pause['duration'] == '0629'
    assert mono_short_pause['duration'] == '0782'
    assert original_short_pause['duration'] == '0782'


def test_phase2_mini_pause_eligibility_uses_half_beat_basis_for_mono_and_ophone() -> None:
    runtime_config = _runtime_view_phonetize_config(
        _merge_phonetize_config(
            {
                'process': {
                    'timing_model': {
                        'durations': {
                            'cvc_reference': 305,
                            'pauses': {
                                'mini': {
                                    'min': 50,
                                    'max': 80,
                                },
                            },
                        },
                    },
                },
            }
        )
    )
    rows = build_phone_rows('qat pa')
    units = _partition_phone_units(rows)
    analysis = _analyze_syllable(rows, units[0]['indices'])
    bi_frontmatter = {'metadata': {'options': {'mora_mode': 'bi'}}}
    mono_frontmatter = {'metadata': {'options': {'mora_mode': 'mono'}}}

    bi_basis = _resolve_synchronization_basis(
        runtime_config,
        allow_accentuation=True,
        input_frontmatter=bi_frontmatter,
    )
    mono_basis = _resolve_synchronization_basis(
        runtime_config,
        allow_accentuation=True,
        input_frontmatter=mono_frontmatter,
    )
    original_basis = _resolve_synchronization_basis(
        runtime_config,
        allow_accentuation=False,
        input_frontmatter=bi_frontmatter,
    )

    assert _maybe_insert_mini_pause(
        rows,
        units,
        0,
        analysis,
        runtime_config,
        100.0,
        bi_basis,
    ) is None

    mono_pause = _maybe_insert_mini_pause(
        rows,
        units,
        0,
        analysis,
        runtime_config,
        100.0,
        mono_basis,
    )
    original_pause = _maybe_insert_mini_pause(
        rows,
        units,
        0,
        analysis,
        runtime_config,
        100.0,
        original_basis,
    )

    assert mono_pause is not None
    assert mono_pause[1] == 52.0
    assert original_pause is not None
    assert original_pause[1] == 52.0


def test_phase2_non_final_rows_keep_last_completed_unit_drift() -> None:
    rows = build_phone_rows('qat pa')

    realize_phone_rows(rows, allow_accentuation=False)

    assert [row['drift'] for row in rows[:2]] == ['+000', '+000']
    assert rows[2]['drift'].startswith(('-', '+'))
    assert rows[3]['drift'] == rows[2]['drift']


def test_pass3_assigns_row_level_intonation_tokens() -> None:
    original_rows, accentuated_rows = build_phone_streams('at·ta~?!')
    realize_phone_rows(original_rows, allow_accentuation=False)
    realize_phone_rows(accentuated_rows, allow_accentuation=True)
    realize_row_intonation(original_rows, accentuated=False)
    realize_row_intonation(accentuated_rows, accentuated=True)

    assert [row['intonation'] for row in original_rows[:2]] == ['M0C', 'M0C']
    assert [row['intonation'] for row in original_rows[2:4]] == ['H3C', 'H3C']
    assert original_rows[-2]['type'] == 'Q'
    assert original_rows[-2]['intonation'] == 'H3C'
    assert original_rows[-1]['type'] == 'S'
    assert [row['intonation'] for row in accentuated_rows[:2]] == ['M0C', 'M0C']
    assert [row['intonation'] for row in accentuated_rows[2:4]] == ['H3C', 'H3C']
    assert accentuated_rows[-2]['type'] == 'Q'
    assert accentuated_rows[-2]['intonation'] == 'H3C'
    assert accentuated_rows[-1]['type'] == 'S'


def test_mbrola_rows_use_row_level_intonation_tokens() -> None:
    original_rows, accentuated_rows = build_phone_streams('at~·ta?')
    realize_phone_rows(original_rows, allow_accentuation=False)
    realize_phone_rows(accentuated_rows, allow_accentuation=True)
    realize_row_intonation(original_rows, accentuated=False)
    realize_row_intonation(accentuated_rows, accentuated=True)

    original_lines = serialize_mbrola_rows(original_rows, accentuated=False).strip().splitlines()
    accentuated_lines = serialize_mbrola_rows(accentuated_rows, accentuated=True).strip().splitlines()

    assert all(len(line.split()) >= 3 for line in original_lines)
    assert all(not line.startswith(('AA ', 'TA ', 'SP ', 'ZP ')) for line in original_lines)
    assert any(line.startswith('a ') for line in original_lines)
    assert any(line.startswith('t ') for line in original_lines)
    assert [row['intonation'] for row in original_rows[:2]] == ['M0C', 'M0C']
    assert [row['intonation'] for row in accentuated_rows[:2]] == ['H2C', 'H2C']
    assert any(any(target != 120 for target in map(int, line.split()[2:])) for line in original_lines)
    assert any(line.endswith(' 135') for line in accentuated_lines)


def test_mbrola_rows_merge_adjacent_identical_symbol_and_frequency() -> None:
    rows = build_phone_rows('at·ta·ka')
    realize_phone_rows(rows, allow_accentuation=False)
    realize_row_intonation(rows, accentuated=False)

    lines = serialize_mbrola_rows(rows, accentuated=False).strip().splitlines()

    assert any(line.startswith('t 175 120') for line in lines)


def test_mbrola_rows_emit_xsampa_pause_and_colored_vowels() -> None:
    rows = build_phone_rows('qa,\n')
    realize_phone_rows(rows, allow_accentuation=False)
    realize_row_intonation(rows, accentuated=False)

    lines = serialize_mbrola_rows(rows, accentuated=False).strip().splitlines()

    assert any(line.startswith('q ') for line in lines)
    assert any(line.startswith('a. ') for line in lines)
    assert any(line.startswith('_ ') for line in lines)


def test_mbrola_rows_emit_variable_length_pitch_tails_for_linear_tokens() -> None:
    rows = build_phone_rows('at~,')
    realize_phone_rows(rows, allow_accentuation=True)
    realize_row_intonation(rows, {'process': {'intonation': {'continuation': 'R1'}}}, accentuated=True)

    lines = serialize_mbrola_rows(rows, accentuated=False).strip().splitlines()

    assert any(len(line.split()) == 4 for line in lines if line.startswith(('a ', 't ', '_ ')))


def test_verification_rejects_non_positive_intonation_f0() -> None:
    result = verify_phonetize_config({'process': {'intonation': {'f0': 0}}})

    assert result.status == 'failure'
    assert any(issue.path == 'phonetize.process.intonation.f0' for issue in result.failures)


def test_phase2_short_pause_can_leave_residual_drift_when_band_blocks_full_discharge() -> None:
    config = {
        'process': {
            'timing_model': {
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
    assert report['unit_drift']['current'] == 0
    assert report['unit_drift']['label'] == 'On the beat'


def test_phase2_short_vowels_stay_hard_during_ordinary_drift_recovery() -> None:
    rows = build_phone_rows('qat')

    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 0,
                    'durations': {
                        'cvc_reference': 350,
                    },
                },
            }
        },
        allow_accentuation=False,
    )

    assert rows[1]['duration'] == '0110'


def test_phase2_long_vowels_remain_available_for_ordinary_drift_recovery() -> None:
    rows = build_phone_rows('qā')

    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 0,
                    'durations': {
                        'cvc_reference': 400,
                    },
                },
            }
        },
        allow_accentuation=False,
    )

    assert int(rows[1]['duration']) > 160


def test_phase2_inserts_one_mini_pause_at_eligible_word_boundary() -> None:
    rows = build_phone_rows('qat pa')

    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 0,
                    'durations': {
                        'cvc_reference': 350,
                        'pauses': {
                            'mini': {
                                'min': 50,
                                'max': 80,
                            },
                        },
                    },
                },
            }
        },
        allow_accentuation=False,
    )

    mini_pause_rows = [row for row in rows if row['category'] == 'S' and row['text'] == MINI_PAUSE_TEXT]
    assert len(mini_pause_rows) == 1
    assert mini_pause_rows[0]['label'] == MINI_PAUSE_LABEL
    assert mini_pause_rows[0]['type'] == MINI_PAUSE_TYPE
    assert mini_pause_rows[0]['realization'] == MINI_PAUSE_REALIZATION
    assert mini_pause_rows[0]['duration'] == '0064'
    assert mini_pause_rows[0]['drift'] == '+000'
    assert reconstruct_tilde_from_phone_rows(rows) == 'qat pa\n'


def test_phase2_does_not_insert_mini_pause_before_punctuation_owned_pause() -> None:
    rows = build_phone_rows('qat, pa')

    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 0,
                    'durations': {
                        'cvc_reference': 306,
                        'pauses': {
                            'mini': {
                                'min': 50,
                                'max': 80,
                            },
                        },
                    },
                },
            }
        },
        allow_accentuation=False,
    )

    assert all(row['text'] != MINI_PAUSE_TEXT for row in rows if row['category'] == 'S')


def test_phase2_long_pause_resets_running_drift_to_zero() -> None:
    config = {
        'process': {
            'timing_model': {
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
    assert report['unit_drift']['current'] == 0
    assert report['unit_drift']['label'] == 'On the beat'


def test_phase2_extensible_reports_drift_summary_and_extensions() -> None:
    rows = build_phone_rows('bā~')

    report = realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 0,
                },
            }
        },
        allow_accentuation=True,
    )

    assert set(report['unit_drift']) == {'max', 'mean', 'stddev', 'current', 'label'}
    assert report['unit_drift']['max'] > 0
    assert report['unit_drift_extension_count'] > 0
    assert report['max_unit_drift_extension'] > 0


def test_phase2_reports_probability_oriented_extension_rates() -> None:
    rows = build_phone_rows('bā~')

    report = realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 0,
                },
            }
        },
        allow_accentuation=True,
    )

    assert report['syllable_count'] == 1
    assert report['pause_count'] == 1
    assert report['mini_pause_count'] == 0
    assert report['total_unit_count'] == 2
    assert report['unit_drift_extension_rate'] == pytest.approx(1.0)


def test_phase2_reports_drift_tolerance_effect_over_non_accented_long_vowels() -> None:
    rows = build_phone_rows('qā')

    report = realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 0,
                    'durations': {
                        'cvc_reference': 400,
                    },
                },
            }
        },
        allow_accentuation=False,
    )

    assert report['non_accented_long_vowel_count'] == 1
    assert report['left_as_is_non_accented_long_vowel_count'] == 0
    assert report['drift_tolerance_effect'] == pytest.approx(0.0)
    assert report['adjusted_non_accented_long_vowel_count'] == 1
    assert report['shortened_non_accented_long_vowel_count'] == 0
    assert report['lengthened_non_accented_long_vowel_count'] == 1


def test_phase2_explicit_tolerance_19_keeps_small_fricative_long_vowel_drift_as_is() -> None:
    zero_rows = build_phone_rows('šā')
    zero_report = realize_phone_rows(
        zero_rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 0,
                    'durations': {
                        'cvc_reference': 260,
                    },
                },
            }
        },
        allow_accentuation=False,
    )
    tolerant_rows = build_phone_rows('šā')
    tolerant_report = realize_phone_rows(
        tolerant_rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 19,
                    'durations': {
                        'cvc_reference': 260,
                    },
                },
            }
        },
        allow_accentuation=False,
    )

    assert zero_report['non_accented_long_vowel_count'] == 1
    assert zero_report['adjusted_non_accented_long_vowel_count'] == 1
    assert zero_report['left_as_is_non_accented_long_vowel_count'] == 0
    assert zero_report['drift_tolerance_effect'] == pytest.approx(0.0)

    assert tolerant_report['non_accented_long_vowel_count'] == 1
    assert tolerant_report['adjusted_non_accented_long_vowel_count'] == 0
    assert tolerant_report['left_as_is_non_accented_long_vowel_count'] == 1
    assert tolerant_report['drift_tolerance_effect'] == pytest.approx(1.0)
    assert [row['duration'] for row in zero_rows] != [row['duration'] for row in tolerant_rows]


def test_phase2_reports_mini_pause_probability_over_structural_eligibility() -> None:
    rows = build_phone_rows('qat pa')

    report = realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 0,
                    'durations': {
                        'cvc_reference': 350,
                        'pauses': {
                            'mini': {
                                'min': 50,
                                'max': 80,
                            },
                        },
                    },
                },
            }
        },
        allow_accentuation=False,
    )

    assert report['syllable_count'] == 2
    assert report['pause_count'] == 1
    assert report['mini_pause_count'] == 1
    assert report['total_unit_count'] == 4
    assert report['eligible_mini_pause_count'] == 1
    assert report['inserted_mini_pause_count'] == 1
    assert report['mini_pause_insertion_rate'] == pytest.approx(1.0)


def test_phase2_reports_pause_residual_frequency_over_non_mini_pauses() -> None:
    rows = build_phone_rows('qat,')

    report = realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
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
        },
        allow_accentuation=False,
    )

    assert report['pause_count'] == 2
    assert report['pause_with_residual_drift_count'] == 1
    assert report['pause_with_residual_drift_rate'] == pytest.approx(0.5)


def test_phase2_default_policy_keeps_runtime_extensible_behavior() -> None:
    rows = build_phone_rows('bā~')

    report = realize_phone_rows(
        rows,
        None,
        allow_accentuation=True,
    )

    assert report['unit_drift']['current'] == 0
    assert report['unit_drift']['label'] == 'On the beat'


def test_shared_verification_uses_extensible_canonical_drift_default() -> None:
    defaults = build_default_phonetize_verification_config()

    assert ACCENTUATION_DISTRIBUTION_CHOICES == ('100_0', '95_05', '90_10', '85_15', '80_20', '75_25', '70_30')
    assert defaults['process']['timing_model']['accentuation_distribution_policy'] == '80_20'
    assert 'drift_policy' not in defaults['process']['timing_model']
    assert 'short_pause_policy' not in defaults['process']['timing_model']
    assert defaults['process']['timing_model']['drift_tolerance'] == 19
    durations = defaults['process']['timing_model']['durations']
    assert durations['segmental_floor'] == 20
    assert durations['consonants']['closure']['perception_limits']['gemination_max'] == 260
    assert durations['consonants']['fricative']['geminate'] == 210
    assert durations['consonants']['fricative']['perception_limits']['geminate_min'] == 163
    assert durations['consonants']['fricative']['perception_limits']['gemination_max'] == 290
    assert durations['consonants']['sonorant']['perception_limits']['gemination_max'] == 275
    assert durations['vowels']['perception_limits']['elongation_max'] == 280


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


def test_shared_verification_rejects_gemination_max_above_segmental_ceiling() -> None:
    result = verify_phonetize_config(
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'segmental_ceiling': 200,
                        'consonants': {
                            'closure': {
                                'perception_limits': {
                                    'gemination_max': 220,
                                }
                            }
                        },
                    }
                }
            }
        }
    )

    assert result.status == 'failure'
    assert any('gemination_max <= phonetize.process.timing_model.durations.segmental_ceiling' in issue.relation for issue in result.failures)


def test_shared_verification_rejects_segmental_floor_above_vowel_and_consonant_minima() -> None:
    result = verify_phonetize_config(
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'segmental_floor': 120,
                    }
                }
            }
        }
    )

    assert result.status == 'failure'
    assert any('segmental_floor' in issue.path for issue in result.failures)


def _first_syllable_analysis(sample: str) -> dict[str, object]:
    """Helper for Path-indexed tests."""
    rows = build_phone_rows(sample)
    units = _partition_phone_units(rows)
    first = next(unit for unit in units if unit['kind'] == 'syllable')
    return _analyze_syllable(rows, first['indices'])


def test_path_1_1_normalization_keeps_in_range_value() -> None:
    """Path 1.1"""
    assert _normalize_drift_to_nearest_branch(120.0, 306.0) == 120.0


def test_path_1_2_normalization_wraps_positive_overflow() -> None:
    """Path 1.2"""
    assert _normalize_drift_to_nearest_branch(200.0, 306.0) == -106.0


def test_path_1_3_normalization_wraps_negative_overflow() -> None:
    """Path 1.3"""
    assert _normalize_drift_to_nearest_branch(-200.0, 306.0) == 106.0


def test_path_1_3b_normalization_keeps_exact_thresholds_unchanged() -> None:
    """Path 1.3b"""
    threshold = _round_half_up(0.5 * 306.0)
    assert _normalize_drift_to_nearest_branch(float(threshold), 306.0) == float(threshold)
    assert _normalize_drift_to_nearest_branch(float(-threshold), 306.0) == float(-threshold)


def test_path_1_4_normalization_can_be_disabled() -> None:
    """Path 1.4"""
    assert _normalize_drift_to_nearest_branch(250.0, 306.0) == -56.0


def test_path_1_5_normalization_rotates_exactly_one_branch_when_enabled() -> None:
    """Path 1.5"""
    assert _normalize_drift_to_nearest_branch(-250.0, 306.0) == 56.0


def test_path_1_5b_normalization_wraps_minus_303_to_plus_3_for_306_reference() -> None:
    """Path 1.5b"""
    assert _normalize_drift_to_nearest_branch(-303.0, 306.0) == 3.0


def test_path_1_6_fold_is_deferred_until_prosodic_unit_final_boundary() -> None:
    """Path 1.6"""
    rows = build_phone_rows('qā&bā')
    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'cvc_reference': 600,
                        'vowels': {'perception_limits': {'very_long_min': 190, 'elongation_max': 240}},
                    }
                }
            }
        },
        allow_accentuation=False,
    )

    vowel_rows = [row for row in rows if row['category'] == 'V']
    assert len(vowel_rows) >= 2
    assert vowel_rows[0]['boundary'] == 'L'
    assert vowel_rows[0]['duration'] == '0189'
    assert vowel_rows[0]['drift'] == '-322'
    assert vowel_rows[1]['boundary'] == 'F'
    assert vowel_rows[1]['duration'] == '0189'
    assert vowel_rows[1]['drift'] == '-044'


def test_path_2_tolerance_gate_skips_long_vowel_correction() -> None:
    """Path 2"""
    rows = build_phone_rows('qā')
    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 500,
                    'durations': {'cvc_reference': 306},
                }
            }
        },
        allow_accentuation=False,
    )
    assert rows[1]['duration'] == '0160'


def test_path_3_1_long_vowel_correction_with_legal_room() -> None:
    """Path 3.1"""
    rows = build_phone_rows('qā')
    realize_phone_rows(rows, {'process': {'timing_model': {'durations': {'cvc_reference': 400}}}}, allow_accentuation=False)
    assert int(rows[1]['duration']) > 160


def test_path_3_1b_non_accentual_long_vowel_cleanup_targets_zero_when_legal_room_exists() -> None:
    """Path 3.1b"""
    rows = build_phone_rows('qā')
    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'cvc_reference': 310,
                    }
                }
            }
        },
        allow_accentuation=False,
    )

    assert rows[1]['duration'] == '0221'
    assert rows[1]['drift'] == '+000'


def test_path_3_2_long_vowel_correction_without_legal_room() -> None:
    """Path 3.2"""
    rows = build_phone_rows('qā')
    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'cvc_reference': 500,
                        'vowels': {'perception_limits': {'elongation_max': 160}},
                    }
                }
            }
        },
        allow_accentuation=False,
    )
    assert rows[1]['duration'] == '0160'


def test_path_3_3_short_vowel_stays_fixed() -> None:
    """Path 3.3"""
    rows = build_phone_rows('qat')
    realize_phone_rows(rows, {'process': {'timing_model': {'durations': {'cvc_reference': 400}}}}, allow_accentuation=False)
    assert rows[1]['duration'] == '0110'


def test_path_3_3b_accentuation_inactive_does_not_apply_increment() -> None:
    """Path 3.3b"""
    plain_rows = build_phone_rows('bā')
    inactive_rows = build_phone_rows('bā~')
    active_rows = build_phone_rows('bā~')

    realize_phone_rows(plain_rows, allow_accentuation=False)
    realize_phone_rows(inactive_rows, allow_accentuation=False)
    realize_phone_rows(active_rows, allow_accentuation=True)

    assert [row['duration'] for row in inactive_rows] == [row['duration'] for row in plain_rows]
    assert int(active_rows[0]['duration']) >= int(inactive_rows[0]['duration'])
    assert int(active_rows[1]['duration']) >= int(inactive_rows[1]['duration'])


def test_path_3_4_non_accentual_long_vowel_stops_before_very_long_band_and_keeps_residual_drift() -> None:
    """Path 3.4"""
    rows = build_phone_rows('qā')
    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'cvc_reference': 500,
                        'vowels': {'perception_limits': {'very_long_min': 190, 'max': 240}},
                    }
                }
            }
        },
        allow_accentuation=False,
    )

    assert rows[1]['duration'] == '0189'
    assert rows[1]['drift'] == '+028'


def test_path_3_5_unit_final_fold_happens_after_syllable_completion_for_current_reference() -> None:
    """Path 3.5"""
    rows = build_phone_rows('qā')
    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'cvc_reference': 600,
                        'vowels': {'perception_limits': {'very_long_min': 190, 'max': 240}},
                    },
                }
            }
        },
        allow_accentuation=False,
    )

    assert rows[1]['duration'] == '0189'
    # In the original stream, CR-080 folds against the half-beat basis rather than the
    # full cvc_reference, so the residual now lands near the half-beat checkpoint.
    assert rows[1]['drift'] == '-022'


def test_path_4_1_accent_route_c_colon_v() -> None:
    """Path 4.1"""
    analysis = _first_syllable_analysis('b~a')
    assert analysis['accent_shape'] == 'C:V'
    assert _primary_accent_index(analysis) == analysis['onset_indices'][0]
    assert _adjacent_accent_index(analysis) == analysis['nucleus_index']


def test_path_4_2_accent_route_cvv_colon() -> None:
    """Path 4.2"""
    analysis = _first_syllable_analysis('bā~')
    assert analysis['accent_shape'] == 'CVV:'
    assert _primary_accent_index(analysis) == analysis['nucleus_index']
    assert _adjacent_accent_index(analysis) == analysis['onset_indices'][0]


def test_path_4_3_accent_route_cvc_colon() -> None:
    """Path 4.3"""
    analysis = _first_syllable_analysis('bat~')
    assert analysis['accent_shape'] == 'CVC:'
    assert _primary_accent_index(analysis) == analysis['coda_indices'][0]
    assert _adjacent_accent_index(analysis) == analysis['nucleus_index']


def test_path_4_4_accent_route_cvv_colon_c() -> None:
    """Path 4.4"""
    analysis = _first_syllable_analysis('bāt~')
    assert analysis['accent_shape'] == 'CVV:C'
    assert _primary_accent_index(analysis) == analysis['nucleus_index']
    assert _adjacent_accent_index(analysis) == analysis['coda_indices'][0]


def test_path_5_1_policy_100_0_primary_first() -> None:
    """Path 5.1"""
    rows = build_phone_rows('bā~')
    realize_phone_rows(rows, {'process': {'timing_model': {'accentuation_distribution_policy': '100_0'}}}, allow_accentuation=True)
    assert int(rows[1]['duration']) >= 160


def test_path_5_2_policy_80_20_split() -> None:
    """Path 5.2"""
    rows = build_phone_rows('bā~')
    realize_phone_rows(rows, {'process': {'timing_model': {'accentuation_distribution_policy': '80_20'}}}, allow_accentuation=True)
    assert int(rows[0]['duration']) > 89


def test_path_5_3_policy_70_30_split() -> None:
    """Path 5.3"""
    rows = build_phone_rows('bā~')
    realize_phone_rows(rows, {'process': {'timing_model': {'accentuation_distribution_policy': '70_30'}}}, allow_accentuation=True)
    assert int(rows[0]['duration']) > 89


def test_path_5_4_accent_increment_uses_full_half_foot_even_with_entry_drift() -> None:
    """Path 5.4"""
    rows = build_phone_rows('bā~')
    analysis = _first_syllable_analysis('bā~')
    durations = {
        analysis['onset_indices'][0]: 89.0,
        analysis['nucleus_index']: 160.0,
    }
    config = {
        'process': {
            'accentuation_distribution_policy': '100_0',
        },
        'timing_model': {
            'durations': {
                'segmental_ceiling': 310,
                'segmental_floor': 10,
                'cvc_reference': 300,
                'consonants': {
                    'closure': {'perception_limits': {'geminate_min': 130, 'gemination_max': 220}},
                    'fricative': {'perception_limits': {'geminate_min': 150, 'gemination_max': 250}},
                    'sonorant': {'perception_limits': {'geminate_min': 135, 'gemination_max': 250}},
                },
                'vowels': {
                    'short': 110,
                    'long': 160,
                    'perception_limits': {
                        'long_min': 153,
                        'very_long_min': 233,
                        'elongation_max': 400,
                    },
                },
            },
        },
    }

    applied = _apply_accent_increment(
        rows,
        analysis,
        durations,
        config,
        40.0,
        None,
    )

    assert applied == 150.0


def test_path_5_4b_preserved_ratio_caps_total_increment_under_legality_limits() -> None:
    """Path 5.4b"""
    rows = build_phone_rows('bā~')
    analysis = _first_syllable_analysis('bā~')
    durations = {
        analysis['onset_indices'][0]: 89.0,
        analysis['nucleus_index']: 160.0,
    }
    config = {
        'process': {
            'accentuation_distribution_policy': '80_20',
        },
        'timing_model': {
            'durations': {
                'segmental_ceiling': 310,
                'segmental_floor': 10,
                'cvc_reference': 300,
                'consonants': {
                    'closure': {'perception_limits': {'geminate_min': 120, 'gemination_max': 260}},
                    'fricative': {'perception_limits': {'geminate_min': 163, 'gemination_max': 290}},
                    'sonorant': {'perception_limits': {'geminate_min': 148, 'gemination_max': 275}},
                },
                'vowels': {
                    'short': 110,
                    'long': 160,
                    'perception_limits': {
                        'long_min': 153,
                        'very_long_min': 233,
                        'elongation_max': 220,
                    },
                },
            },
        },
    }

    applied = _apply_accent_increment(
        rows,
        analysis,
        durations,
        config,
        40.0,
        None,
    )

    assert applied == 75.0
    assert durations[analysis['nucleus_index']] == 220.0
    assert durations[analysis['onset_indices'][0]] == 104.0


def test_path_5_5_consonant_class_mapping_covers_accent_legality_inventory() -> None:
    """Path 5.5"""
    closure_row = next(row for row in build_phone_rows('ba') if row['text'] == 'b')
    fricative_row = next(row for row in build_phone_rows('ša') if row['text'] == 'š')
    sonorant_row = next(row for row in build_phone_rows('la') if row['text'] == 'l')
    hiatus_row = next(row for row in build_phone_rows('a˙a') if row['text'] == '˙')
    transition_row = next(row for row in build_phone_rows('a¨a') if row['text'] == '¨')

    assert _consonant_timing_key(closure_row) == 'closure'
    assert _consonant_timing_key(fricative_row) == 'fricative'
    assert _consonant_timing_key(sonorant_row) == 'sonorant'
    assert _consonant_timing_key(hiatus_row) == 'closure'
    assert _consonant_timing_key(transition_row) == 'sonorant'


def test_path_6_1_accentuation_precedes_long_vowel_cleanup_on_cvv() -> None:
    """Path 6.1"""
    rows = build_phone_rows('bā~')
    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'vowels': {'perception_limits': {'elongation_max': 170}},
                    }
                }
            }
        },
        allow_accentuation=True,
    )
    assert int(rows[0]['duration']) > 89
    assert rows[1]['duration'] == '0170'


def test_path_6_1b_accented_long_vowel_cleanup_uses_elongation_max_without_tolerance_gate() -> None:
    """Path 6.1b"""
    rows = build_phone_rows('bā~')
    report = realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'drift_tolerance': 500,
                    'durations': {
                        'consonants': {
                            'closure': {
                                'perception_limits': {
                                    'geminate_min': 95,
                                }
                            }
                        },
                        'vowels': {
                            'perception_limits': {
                                'very_long_min': 200,
                                'elongation_max': 240,
                            }
                        },
                    }
                }
            }
        },
        allow_accentuation=True,
    )

    assert rows[1]['duration'] == '0240'
    assert report['non_accented_long_vowel_count'] == 0


def test_path_6_2_full_saturation_keeps_residual_drift() -> None:
    """Path 6.2"""
    rows = build_phone_rows('bā~')
    report = realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'consonants': {
                            'closure': {
                                'perception_limits': {
                                    'gemination_max': 108,
                                }
                            }
                        },
                        'vowels': {'perception_limits': {'elongation_max': 160}},
                    }
                }
            }
        },
        allow_accentuation=True,
    )
    # Accent increment is fully constrained here; any remaining mismatch can be
    # discharged by later pauses in the stream.
    assert rows[0]['duration'] == '0089'
    assert rows[1]['duration'] == '0160'


def test_path_7_1_same_consonant_chain_ceiling_is_enforced() -> None:
    """Path 7.1"""
    rows = build_phone_rows('at~·ta')
    realize_phone_rows(
        rows,
        {'process': {'timing_model': {'durations': {'consonants': {'closure': {'perception_limits': {'gemination_max': 210}}}}}}},
        allow_accentuation=True,
    )
    t_rows = [row for row in rows if row['text'] == 't' and row['category'] == 'C']
    assert len(t_rows) >= 2
    assert int(t_rows[0]['duration']) + int(t_rows[1]['duration']) <= 210


def test_path_7_3_adjacent_short_vowel_spill_stops_below_long_min() -> None:
    """Path 7.3"""
    rows = build_phone_rows('nim~·ma')

    realize_phone_rows(rows, allow_accentuation=True)

    vowel_row = next(row for row in rows if row['text'] == 'i' and row['category'] == 'V')
    assert vowel_row['length'] == 'S'
    assert vowel_row['duration'] == '0131'


def test_path_7_2_adjacent_consonant_stays_singleton() -> None:
    """Path 7.2"""
    rows = build_phone_rows('bā~')
    realize_phone_rows(rows, allow_accentuation=True)
    onset = rows[0]
    assert int(onset['duration']) <= 179


def test_path_8_1_mini_pause_inserted_when_eligible() -> None:
    """Path 8.1"""
    rows = build_phone_rows('qat pa')
    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'cvc_reference': 350,
                        'pauses': {'mini': {'min': 50, 'max': 80}},
                    }
                }
            }
        },
        allow_accentuation=False,
    )
    assert any(row['category'] == 'S' and row['text'] == MINI_PAUSE_TEXT for row in rows)
    mini_row = next(row for row in rows if row['category'] == 'S' and row['text'] == MINI_PAUSE_TEXT)
    assert mini_row['label'] == MINI_PAUSE_LABEL
    assert mini_row['type'] == MINI_PAUSE_TYPE
    assert mini_row['realization'] == MINI_PAUSE_REALIZATION


def test_path_8_2_mini_pause_not_inserted_when_not_eligible() -> None:
    """Path 8.2"""
    rows = build_phone_rows('qat, pa')
    realize_phone_rows(rows, {'process': {'timing_model': {'durations': {'cvc_reference': 306}}}}, allow_accentuation=False)
    assert all(row['text'] != MINI_PAUSE_TEXT for row in rows if row['category'] == 'S')


def test_path_8_3_positive_drift_mini_pause_targets_next_sync_point() -> None:
    """Path 8.3"""
    rows = build_phone_rows('ša pa')
    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'cvc_reference': 300,
                        'pauses': {'mini': {'min': 220, 'max': 230}},
                    }
                }
            }
        },
        allow_accentuation=False,
    )

    mini_pause_rows = [row for row in rows if row['category'] == 'S' and row['text'] == MINI_PAUSE_TEXT]
    assert mini_pause_rows == []


def test_path_8_4_negative_drift_outside_mini_band_does_not_clamp_partial_pause() -> None:
    """Path 8.4"""
    rows = build_phone_rows('qat pa')
    realize_phone_rows(
        rows,
        {
            'process': {
                'timing_model': {
                    'durations': {
                        'cvc_reference': 500,
                        'pauses': {'mini': {'min': 100, 'max': 200}},
                    }
                }
            }
        },
        allow_accentuation=False,
    )

    assert all(row['text'] != MINI_PAUSE_TEXT for row in rows if row['category'] == 'S')


def test_path_9_1_short_pause_uses_nearest_discharge_in_band() -> None:
    """Path 9.1"""
    rows = build_phone_rows('qat,')
    realize_phone_rows(rows, {'process': {'timing_model': {'durations': {'cvc_reference': 200, 'pauses': {'short': {'min': 600, 'max': 600}}}}}}, allow_accentuation=False)
    short_pause = next(row for row in rows if row['category'] == 'S' and row['length'] == 'S')
    assert short_pause['duration'] == '0600'


def test_path_9_2_long_pause_uses_nearest_discharge_in_band() -> None:
    """Path 9.2"""
    rows = build_phone_rows('qat\n')
    realize_phone_rows(rows, allow_accentuation=False)
    long_pause = next(row for row in rows if row['category'] == 'S' and row['length'] == 'L')
    assert long_pause['duration'] == '1514'


def test_path_9_3_pause_clamps_and_carries_residual() -> None:
    """Path 9.3"""
    rows = build_phone_rows('qat,')
    realize_phone_rows(rows, {'process': {'timing_model': {'durations': {'cvc_reference': 200, 'pauses': {'short': {'min': 600, 'max': 600}}}}}}, allow_accentuation=False)
    short_pause = next(row for row in rows if row['category'] == 'S' and row['length'] == 'S')
    assert short_pause['drift'] != '+000'


def test_path_10_1_non_final_rows_keep_previous_drift_token() -> None:
    """Path 10.1"""
    rows = build_phone_rows('qat pa')
    realize_phone_rows(rows, allow_accentuation=False)
    assert rows[0]['drift'] == '+000'
    assert rows[1]['drift'] == '+000'


def test_path_10_2_unit_final_row_updates_drift_token() -> None:
    """Path 10.2"""
    rows = build_phone_rows('qat pa')
    realize_phone_rows(rows, allow_accentuation=False)
    assert rows[2]['drift'] != '+000'


def test_path_11_round_half_up_behavior() -> None:
    """Path 11"""
    assert _round_half_up(2.5) == 3
    assert _round_half_up(152.5) == 153


def test_phase2_first_construct_demo_line_preserves_half_foot_checkpoint_invariant() -> None:
    from pathlib import Path

    from akkapros.lib.frontmatter import split_frontmatter
    from akkapros.lib.phonetize import build_phone_streams, realize_phone_rows
    from akkapros.lib.prosody import AccentStyle, ProsodyEngine, parse_syl_line, postprocess_restore_diphthongs
    from akkapros.lib.syllabify import syllabify_text

    repo_root = Path(__file__).resolve().parents[1]
    proc_path = repo_root / 'data' / 'lexlinks' / 'construct_prep' / 'erra_construct_proc.txt'
    _frontmatter, body = split_frontmatter(proc_path.read_text(encoding='utf-8'))
    syllabified = syllabify_text(body, preserve_lines=True)
    engine = ProsodyEngine(style=AccentStyle.LOB)
    accentuated_lines = []
    for line in syllabified.splitlines():
        if not line.strip():
            accentuated_lines.append('')
            continue
        accentuated_lines.append(engine.accentuation_line(parse_syl_line(line)))
    tilde_lines = postprocess_restore_diphthongs(accentuated_lines)
    first_line = next(line for line in tilde_lines if line.strip()) + '\n'

    _original_rows, accentuated_rows = build_phone_streams(first_line)
    realize_phone_rows(accentuated_rows, allow_accentuation=True)

    total = 0
    failures = []
    for index, row in enumerate(accentuated_rows, start=1):
        total += int(row['duration'])
        if not _is_chrono_checkpoint_row(row):
            continue
        drift = int(row['drift'])
        numerator = 2 * (total - drift)
        if numerator % 300 != 0:
            failures.append((index, row['label'], row['duration'], row['drift'], total, numerator))

    assert not failures


def test_debug_chrono_raises_fatally_on_checkpoint_mismatch() -> None:
    assert lib_constants.DEBUG_CHRONO is False

    rows = build_phone_rows('qat')
    realize_phone_rows(rows, allow_accentuation=False)

    rows[2]['drift'] = '-013'

    with pytest.raises(ValueError, match='DEBUG_CHRONO checkpoint mismatch'):
        monkeypatch = pytest.MonkeyPatch()
        try:
            monkeypatch.setattr(lib_constants, 'DEBUG_CHRONO', True)
            _validate_chrono_checkpoints(rows, 306)
        finally:
            monkeypatch.undo()


def test_normal_mode_does_not_trigger_debug_chrono_checkpoint_guard() -> None:
    assert lib_constants.DEBUG_CHRONO is False

    rows = build_phone_rows('qat')
    realize_phone_rows(rows, allow_accentuation=False)

    rows[2]['drift'] = '-013'

    _validate_chrono_checkpoints(rows, 306)