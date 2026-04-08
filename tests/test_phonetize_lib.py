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
    build_phone_rows,
    parse_phone_row,
    reconstruct_tilde_from_phone_rows,
    serialize_phone_row,
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
    ]
    line = serialize_phone_row(rows[0])
    assert line == 'SUD-C-F-S-O-N-F-SU-0000:ṣ'
    assert parse_phone_row(line) == rows[0]


def test_boundaries_preserve_internal_enclitic_and_unit_edges() -> None:
    rows = build_phone_rows('šit·ku·nat-ma')
    assert [row['boundary'] for row in rows if row['boundary'] != 'N'] == ['I', 'I', 'E', 'F']
    assert reconstruct_tilde_from_phone_rows(rows) == 'šit·ku·nat-ma'


def test_internal_and_explicit_merges_round_trip() -> None:
    sample = 'u+ana&šar~·ri'
    rows = build_phone_rows(sample)
    assert reconstruct_tilde_from_phone_rows(rows) == sample
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