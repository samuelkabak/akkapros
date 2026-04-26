from __future__ import annotations

import tempfile
from pathlib import Path

from akkapros.lib.print import (
    ACUTE_MARK,
    convert_line,
    convert_text_with_ipa_xar,
    process_file,
    _render_phone_rows,
)
from akkapros.lib.utils import (
    format_selftest_label,
    get_logger_with_fallback,
    log_selftest_result,
    log_selftest_summary,
)
from akkapros.lib.phonetize import (
    realize_phone_streams,
    serialize_phone_rows,
)
from akkapros.lib.frontmatter import (
    read_text_file,
)


def run_tests() -> bool:
    """Lightweight self-tests for conversion rules."""
    logger = get_logger_with_fallback(__name__)
    category = 'Printer'
    tests = [
        ("nû~", "acute", "nû´"),
        ("nû~", "bold", "**nû**"),
        ("nû~k", "acute", "nû´k"),
        ("nû~k", "bold", "**nûk**"),
        ("šar~·ri", "acute", "šar´ri"),
        ("šar~·ri", "bold", "**šar**ri"),
        ("k~a·pin", "acute", "k´apin"),
        ("k~a·pin", "bold", "**ka**pin"),
        ("k~a", "acute", "k´a"),
        ("k~a", "bold", "**ka**"),
        ("~a·pil", "acute", "´apil"),
        ("~a·pil", "bold", "**a**pil"),
        ("~a", "acute", "´a"),
        ("~a", "bold", "**a**"),
        ("nû~", "ipa", "ˈnuːː"),
        ("nû~k", "ipa", "ˈnuːːk"),
        ("šar~·ri", "ipa", "ˈʃarː.ri"),
        ("k~a·pin", "ipa", "ˈkːa.pin"),
        ("~a·pil", "ipa", "ˈʔːa.pil"),
        ("k~a", "ipa", "ˈkːa"),
        ("~a", "ipa", "ˈʔːa"),
        ("gi·mir+dad~·mē", "acute", "gimir dad´mē"),
        ("gi·mir+dad~·mē", "bold", "gimir **dad**mē"),
        ("gi·mir+dad~·mē", "ipa", "gi.mir.ˈdadː.meː"),
        ("gi·mir+dad~·mē⟦ : ⟧šar", "acute", "gimir dad´mē : šar"),
        ("gi·mir+dad~·mē⟦ : ⟧šar", "ipa", "gi.mir.ˈdadː.meː ⟨colon⟩ | ʃar"),
        ("qa", "xar", "ꝗà"),
        ("qi", "xar", "ꝗì"),
        ("qu", "xar", "ꝗù"),
        ("qe", "xar", "ꝗè"),
        ("ṭa", "xar", "ꞓà"),
        ("ṣa", "xar", "ɉà"),
        ("ša", "xar", "x̌a"),
        ("ḥa", "xar", "'a"),
        ("baḥk", "xar", "ba'k"),
        ("ya", "xar", "ja"),
        ("ʿa", "xar", "'a"),
        ("qā~", "xar", "ꝗàa´"),
        ("šar~", "xar", "x̌ar´"),
        ("q~a", "xar", "ꝗ´à"),
        ("ʾa ʿa", "xar", "'a 'a"),
        ("ʾa", "xar", "'a"),
        ("uʾa", "xar", "u'a"),
        ("kūʾa", "xar", "kuu'a"),
        ("baʾk", "xar", "ba'k"),
        ("abʿd", "xar", "ab'd"),
        ("ʾka", "xar", "'ka"),
        ("bakʾ", "xar", "bak'"),
        ("bākʾ", "xar", "baak'"),
        ("biʾd", "xar", "bi'd"),
        ("buʾd", "xar", "bu'd"),
        ("beʾd", "xar", "be'd"),
        ("takʾ", "xar", "tak'"),
        ("tikʾ", "xar", "tik'"),
        ("tukʾ", "xar", "tuk'"),
        ("tekʾ", "xar", "tek'"),
        ("tīkʾ", "xar", "tiik'"),
        ("bā", "xar", "baa"),
        ("bī", "xar", "bii"),
        ("bū", "xar", "buu"),
        ("bē", "xar", "bee"),
        ("bâ", "xar", "beâ"),
        ("bî", "xar", "beî"),
        ("bû", "xar", "biû"),
        ("bê", "xar", "baê"),
        ("qā", "xar", "ꝗàa"),
        ("qī", "xar", "ꝗìi"),
        ("qū", "xar", "ꝗùu"),
        ("qē", "xar", "ꝗèe"),
        ("qâ", "xar", "ꝗèâ"),
        ("qî", "xar", "ꝗèî"),
        ("qû", "xar", "ꝗìû"),
        ("qê", "xar", "ꝗàê"),
        ("aq", "xar", "aꝗ"),
        ("taq", "xar", "taꝗ"),
        ("qat", "xar", "ꝗàt"),
        ("qa", "ipa", "qɑ"),
        ("aq", "ipa", "aq"),
        ("taq", "ipa", "taq"),
        ("qat", "ipa", "qɑt"),
        ("iṭ", "ipa", "itˤ"),
        ("ṭi", "ipa", "tˤɨ"),
        ("qi", "ipa", "qɨ"),
        ("qu", "ipa", "qʊ"),
        ("qe", "ipa", "qɛ"),
        ("ṭe", "ipa", "tˤɛ"),
        ("iṣ", "ipa", "isˤ"),
        ("a", "ipa", "a"),
        ("i", "ipa", "i"),
        ("u", "ipa", "u"),
        ("e", "ipa", "e"),
        ("ā", "ipa", "aː"),
        ("ī", "ipa", "iː"),
        ("ū", "ipa", "uː"),
        ("ē", "ipa", "eː"),
        ("â", "ipa", "aː"),
        ("î", "ipa", "iː"),
        ("û", "ipa", "uː"),
        ("ê", "ipa", "eː"),
        ("ā~", "ipa", "ˈʔaːː"),
        ("ī~", "ipa", "ˈʔiːː"),
        ("ū~", "ipa", "ˈʔuːː"),
        ("ē~", "ipa", "ˈʔeːː"),
        ("â~", "ipa", "ˈʔaːː"),
        ("î~", "ipa", "ˈʔiːː"),
        ("û~", "ipa", "ˈʔuːː"),
        ("ê~", "ipa", "ˈʔeːː"),
        ("qa~", "ipa", "ˈqɑː"),
        ("qi~", "ipa", "ˈqɨː"),
        ("qu~", "ipa", "ˈqʊː"),
        ("qe~", "ipa", "ˈqɛː"),
        ("qā~", "ipa", "ˈqɑːː"),
        ("qī~", "ipa", "ˈqɨːː"),
        ("qū~", "ipa", "ˈqʊːː"),
        ("qē~", "ipa", "ˈqɛːː"),
        ("qâ~", "ipa", "ˈqɑːː"),
        ("qî~", "ipa", "ˈqɨːː"),
        ("qû~", "ipa", "ˈqʊːː"),
        ("qê~", "ipa", "ˈqɛːː"),
        ("ʾa", "ipa", "ʔa"),
        ("ʿa", "ipa", "ʔa"),
        ("ʾi", "ipa", "ʔi"),
        ("ʿu", "ipa", "ʔu"),
        ("ʿē", "ipa", "ʔeː"),
        ("ʾ~a", "ipa", "ˈʔːa"),
        ("ʿ~a", "ipa", "ˈʔːa"),
        ("a+ē", "ipa", "a.eː"),
        ("a-ē", "ipa", "a-eː"),
        ("ḫa", "ipa", "χa"),
        ("ḥa", "ipa", "ʔa"),
        ("baḥk", "ipa", "baʔk"),
        ("ʿa+ʾi", "ipa", "ʔa.ʔi"),
        ("ʾa-ʿi", "ipa", "ʔa-ʔi"),
        (
            "ana+se·bet·ti qar·rā~d lā+ša·nān — nan~·di·qā kak·kī·kun",
            "ipa",
            "ana.se.bet.ti.qɑr.ˈraːːd.laː.ʃa.naːn ⟨emdash⟩ | ˈnanː.di.qɑː.kak.kiː.kun",
        ),
        (
            "ṣal·mā~t qaq·qa·di ana+šu·mut·ti — šum·qu·tu bū~l šak·kan",
            "ipa",
            "sˤɑl.ˈmaːːt.qɑq.qɑ.di.ana.ʃu.mut.ti ⟨emdash⟩ | ʃum.qʊ.tu.ˈbuːːl.ʃak.kan",
        ),
        ("ba", "ipa", "ba"),
        ("bā", "ipa", "baː"),
        ("baq", "ipa", "baq"),
        ("qab", "ipa", "qɑb"),
        ("qaq", "ipa", "qɑq"),
        ("qā", "ipa", "qɑː"),
        ("ṭeṭ", "ipa", "tˤɛtˤ"),
        ("q~a", "ipa", "ˈqːɑ"),
        ("q~a", "acute", "q´a"),
        ("q~a", "bold", "**qa**"),
        ("~aq", "acute", "´aq"),
        ("~aq", "bold", "**aq**"),
        ("~aq", "ipa", "ˈʔːaq"),
        ("qaq·qa·di", "ipa", "qɑq.qɑ.di"),
        ("ṣal·mā~t", "ipa", "sˤɑl.ˈmaːːt"),
        ("ḫaṭ~·ṭi", "ipa", "ˈχatˤː.tˤɨ"),
        ("qā·tā~·šu", "ipa", "qɑː.ˈtaːː.ʃu"),
        ("a·na+ē·kal·lim", "ipa", "a.na.eː.kal.lim"),
        ("bēl-ē·riš", "ipa", "beːl-eː.riʃ"),
        ("šar gi·mir", "ipa", "ʃar.gi.mir"),
        ("šar, gi·mir", "ipa", "ʃar ⟨comma⟩ | gi.mir"),
        ("šar. gi·mir", "ipa", "ʃar ⟨period⟩ ‖ gi.mir"),
        ("šar\n", "ipa", "ʃar ⟨linebreak⟩ ‖\n"),
        ("šar.\n", "ipa", "ʃar ⟨period⟩ ‖\n"),
        ("šar? gi·mir", "ipa", "ʃar ⟨question⟩ ‖ gi.mir"),
        ("šar! gi·mir", "ipa", "ʃar ⟨exclamation⟩ ‖ gi.mir"),
        ("šar: gi·mir", "ipa", "ʃar ⟨colon⟩ | gi.mir"),
        ("šar; gi·mir", "ipa", "ʃar ⟨semicolon⟩ | gi.mir"),
        ("šar—gi·mir", "ipa", "ʃar ⟨emdash⟩ | gi.mir"),
        ("šar–gi·mir", "ipa", "ʃar ⟨endash⟩ | gi.mir"),
        ("“šar,” gi·mir", "ipa", "⟨opening-dblquote⟩ | ʃar ⟨comma⟩ ⟨closing-dblquote⟩ | gi.mir"),
        ("(šar) {{gi·mir}}", "ipa", "⟨opening-parenthese⟩ | ʃar ⟨closing-parenthese⟩ | ⟨escape:{{gi·mir}}⟩"),
        ("§ 42%", "ipa", "⟨section⟩ ⟨number⟩ ⟨percent⟩ |"),
        ("šar... gi·mir", "ipa", "ʃar ⟨ellipsis⟩ | gi.mir"),
        ("šar… gi·mir", "ipa", "ʃar ⟨ellipsis⟩ | gi.mir"),
        ("123 gi·mir", "ipa", "⟨number⟩ | gi.mir"),
        ("$€£", "ipa", "⟨dollar⟩ ⟨euro⟩ ⟨pound⟩ |"),
        ("er~·ra", "acute", "er´ra"),
        ("er~·ra", "bold", "**er**ra"),
        ("ti·¨ā~m·tu", "bold", "ti**ām**tu"),
        ("nā~š", "bold", "**nāš**"),
        ("ša+ana+na·šê", "acute", "ša ana našê"),
        ("ī·ris·sū~-ma", "bold", "īris**sū**-ma"),
        ("šar {{https://ex.am/ple+uri}} gi·mir+dad~·mē", "bold", "šar {{https://ex.am/ple+uri}} gimir **dad**mē"),
        ("šar {url{https://ex.am/ple+uri}} gi·mir", "ipa", "ʃar ⟨escape:{url{https://ex.am/ple+uri}}⟩ gi.mir"),
        ("šar {_mdf{---}} gi·mir", "ipa", "ʃar ⟨escape:{_mdf{---}}⟩ gi.mir"),
        ("šar{{x}}gi·mir", "ipa", "ʃar ⟨escape:{{x}}⟩ gi.mir"),
        ("šar, 123 gi·mir+dad~·mē", "acute", "šar, 123 gimir dad´mē"),
    ]

    ipa_mode_cases = [
        ("ḥa", "ʔa", "ħa"),
        ("ḫa", "χa", "χa"),
        ("ʿa", "ʔa", "ʕa"),
        ("ʾa", "ʔa", "ʔa"),
        ("ʾ~a", "ˈʔːa", "ˈʔːa"),
        ("ʿa+ʾi", "ʔa.ʔi", "ʕa.ʔi"),
    ]
    circ_hiatus_cases = [
        ("qû", "qʊ.ʊ"),
        ("bû", "bu.u"),
        ("qâ", "qɑ.ɑ"),
        ("qû~", "ˈqʊ.ʊː"),
    ]
    total = len(tests) + 10 + (len(ipa_mode_cases) * 2) + 2 + len(circ_hiatus_cases) + 1
    passed = 0
    case_index = 0

    def report(ok: bool, label: str, details: list[str] | None = None) -> None:
        nonlocal passed, case_index
        case_index += 1
        case_label = format_selftest_label(case_index, total, label)
        if ok:
            passed += 1
        log_selftest_result(logger, ok, category, case_label, details=details)

    for inp, mode, expected in tests:
        got = convert_line(inp, mode)
        if got == expected:
            report(True, f'{mode} {inp}')
        else:
            report(
                False,
                f'{mode} {inp}',
                details=[
                    f'input={inp!r}',
                    f'mode={mode}',
                    f'expected={expected!r}',
                    f'got={got!r}',
                ],
            )

    text_in = "šar {{https://ex.am/ple+uri}} gi·mir+dad~·mē\n~a·pil\n"
    expected_acute = "šar {{https://ex.am/ple+uri}} gimir dad´mē\n´apil\n"
    expected_bold = "šar {{https://ex.am/ple+uri}} gimir **dad**mē\\\n**a**pil\n"
    expected_ipa = "ʃar ⟨escape:{{https://ex.am/ple+uri}}⟩ gi.mir.ˈdadː.meː ⟨linebreak⟩ ‖\nˈʔːa.pil ⟨linebreak⟩ ‖\n"
    expected_xar = "x̌ar {{https://ex.am/ple+uri}} gimir dad´mee\n´apil\n"
    got_acute, got_bold, got_ipa, got_xar = convert_text_with_ipa_xar(text_in)
    if got_acute == expected_acute:
        report(True, 'Convert text acute')
    else:
        report(
            False,
            'Convert text acute',
            details=[
                f'input={text_in!r}',
                f'expected={expected_acute!r}',
                f'got={got_acute!r}',
            ],
        )

    if got_bold == expected_bold:
        report(True, 'Convert text bold')
    else:
        report(
            False,
            'Convert text bold',
            details=[
                f'input={text_in!r}',
                f'expected={expected_bold!r}',
                f'got={got_bold!r}',
            ],
        )

    if got_ipa == expected_ipa:
        report(True, 'Convert text ipa')
    else:
        report(
            False,
            'Convert text ipa',
            details=[
                f'input={text_in!r}',
                f'expected={expected_ipa!r}',
                f'got={got_ipa!r}',
            ],
        )

    if got_xar == expected_xar:
        report(True, 'Convert text xar')
    else:
        report(
            False,
            'Convert text xar',
            details=[
                f'input={text_in!r}',
                f'expected={expected_xar!r}',
                f'got={got_xar!r}',
            ],
        )

    merger_cases = [
        ('gi·mir+dad~·mē', 'acute', 'gimir‿dad´mē'),
        ('gi·mir+dad~·mē', 'bold', 'gimir‿**dad**mē'),
        ('gi·mir+dad~·mē', 'xar', 'gimir‿dad´mee'),
    ]
    for inp, mode, expected in merger_cases:
        got = convert_line(inp, mode, print_merger=True)
        if got == expected:
            report(True, f'{mode} print-merger {inp}')
        else:
            report(
                False,
                f'{mode} print-merger {inp}',
                details=[
                    f'input={inp!r}',
                    f'mode={mode}',
                    f'expected={expected!r}',
                    f'got={got!r}',
                ],
            )

    forbidden_ipa = {'ħ', 'ʕ'}
    ipa_inventory_ok = True
    for inp, mode, _ in tests:
        if mode != 'ipa':
            continue
        ipa_out = convert_line(inp, 'ipa')
        bad = sorted(ch for ch in forbidden_ipa if ch in ipa_out)
        if bad:
            ipa_inventory_ok = False
            report(
                False,
                'Ipa inventory',
                details=[
                    f'input={inp!r}',
                    f'got={ipa_out!r}',
                    f'forbidden={"".join(bad)!r}',
                ],
            )

    if ipa_inventory_ok:
        report(True, 'Ipa inventory')

    text_inventory_ok = not any(ch in got_ipa for ch in forbidden_ipa)
    if text_inventory_ok:
        report(True, 'Convert text ipa inventory')
    else:
        report(
            False,
            'Convert text ipa inventory',
            details=[
                f'input={text_in!r}',
                f'got={got_ipa!r}',
            ],
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        phone_path = Path(tmpdir) / "sample_phone.txt"
        ophone_path = Path(tmpdir) / "sample_ophone.txt"
        out_acute = Path(tmpdir) / "sample_accent_acute.txt"
        out_bold = Path(tmpdir) / "nested" / "sample_accent_bold.md"
        out_ipa = Path(tmpdir) / "sample_accent_ipa.txt"
        out_xar = Path(tmpdir) / "sample_accent_xar.txt"
        out_xar_plain = Path(tmpdir) / "sample_xar.txt"
        (ophone_rows, _), (phone_rows, _) = realize_phone_streams("k~a·pin + ~a·pil")
        phone_path.write_text(serialize_phone_rows(phone_rows), encoding='utf-8')
        ophone_path.write_text(serialize_phone_rows(ophone_rows), encoding='utf-8')

        expected_acute = _render_phone_rows(phone_rows, mode='acute')
        expected_ipa = _render_phone_rows(phone_rows, mode='ipa')
        expected_xar = _render_phone_rows(phone_rows, mode='xar')
        expected_xar_plain = _render_phone_rows(ophone_rows, mode='xar').replace(ACUTE_MARK, '')

        process_file(
            input_file=str(phone_path),
            output_acute_file=str(out_acute),
            output_bold_file=str(out_bold),
            ophone_file=str(ophone_path),
            output_ipa_file=str(out_ipa),
            output_xar_file=str(out_xar),
            output_xar_plain_file=str(out_xar_plain),
            write_acute=True,
            write_bold=False,
            write_ipa=True,
            write_xar=True,
        )

        acute_frontmatter, acute_body = read_text_file(out_acute)
        ipa_frontmatter, ipa_body = read_text_file(out_ipa)
        xar_frontmatter, xar_body = read_text_file(out_xar)
        xar_plain_frontmatter, xar_plain_body = read_text_file(out_xar_plain)

        file_ok = (
            out_acute.exists()
            and acute_frontmatter is not None
            and acute_frontmatter.get('file', {}).get('format') == 'acute'
            and acute_body == expected_acute
            and out_ipa.exists()
            and ipa_frontmatter is not None
            and ipa_frontmatter.get('file', {}).get('format') == 'ipa'
            and ipa_body == expected_ipa
            and out_xar.exists()
            and xar_frontmatter is not None
            and xar_frontmatter.get('file', {}).get('format') == 'xar'
            and xar_body == expected_xar
            and out_xar_plain.exists()
            and xar_plain_frontmatter is not None
            and xar_plain_frontmatter.get('file', {}).get('format') == 'xar'
            and xar_plain_body == expected_xar_plain
            and not out_bold.exists()
        )
        if file_ok:
            report(True, 'Process file selective write')
        else:
            report(
                False,
                'Process file selective write',
                details=[
                    f'acute_exists={out_acute.exists()}',
                    f'acute_text={out_acute.read_text(encoding="utf-8") if out_acute.exists() else ""!r}',
                    f'ipa_exists={out_ipa.exists()}',
                    f'ipa_text={out_ipa.read_text(encoding="utf-8") if out_ipa.exists() else ""!r}',
                    f'xar_exists={out_xar.exists()}',
                    f'xar_text={out_xar.read_text(encoding="utf-8") if out_xar.exists() else ""!r}',
                    f'xar_plain_exists={out_xar_plain.exists()}',
                    f'xar_plain_text={out_xar_plain.read_text(encoding="utf-8") if out_xar_plain.exists() else ""!r}',
                    f'bold_exists={out_bold.exists()}',
                ],
            )

    for inp, exp_ob, exp_strict in ipa_mode_cases:
        got_ob = convert_line(inp, 'ipa', ipa_mode='ipa-ob')
        if got_ob == exp_ob:
            report(True, f'Ipa ob {inp}')
        else:
            report(
                False,
                f'Ipa ob {inp}',
                details=[
                    f'input={inp!r}',
                    f'expected={exp_ob!r}',
                    f'got={got_ob!r}',
                ],
            )

        got_strict = convert_line(inp, 'ipa', ipa_mode='ipa-strict')
        if got_strict == exp_strict:
            report(True, f'Ipa strict {inp}')
        else:
            report(
                False,
                f'Ipa strict {inp}',
                details=[
                    f'input={inp!r}',
                    f'expected={exp_strict!r}',
                    f'got={got_strict!r}',
                ],
            )

    _, _, got_ipa_ob, _ = convert_text_with_ipa_xar("ʾa ʿa\n", ipa_mode='ipa-ob')
    if got_ipa_ob == "ʔa.ʔa ⟨linebreak⟩ ‖\n":
        report(True, 'Convert text ipa mode ob')
    else:
        report(
            False,
            'Convert text ipa mode ob',
            details=[
                f'expected={"ʔa.ʔa ⟨linebreak⟩ ‖\\n"!r}',
                f'got={got_ipa_ob!r}',
            ],
        )

    _, _, got_ipa_strict, _ = convert_text_with_ipa_xar("ʾa ʿa\n", ipa_mode='ipa-strict')
    if got_ipa_strict == "ʔa.ʕa ⟨linebreak⟩ ‖\n":
        report(True, 'Convert text ipa mode strict')
    else:
        report(
            False,
            'Convert text ipa mode strict',
            details=[
                f'expected={"ʔa.ʕa ⟨linebreak⟩ ‖\\n"!r}',
                f'got={got_ipa_strict!r}',
            ],
        )

    for inp, expected in circ_hiatus_cases:
        got = convert_line(inp, 'ipa', circ_hiatus=True)
        if got == expected:
            report(True, f'Ipa circ hiatus {inp}')
        else:
            report(
                False,
                f'Ipa circ hiatus {inp}',
                details=[
                    f'input={inp!r}',
                    f'expected={expected!r}',
                    f'got={got!r}',
                ],
            )

    # Ensure default remains unchanged when circ-hiatus is disabled.
    if convert_line("qû", 'ipa') == "qʊː":
        report(True, 'Ipa circ hiatus default off')
    else:
        report(
            False,
            'Ipa circ hiatus default off',
            details=[
                'expected="qʊː"',
                f'got={convert_line("qû", "ipa")!r}',
            ],
        )

    log_selftest_summary(logger, category, passed, total)
    return passed == total
