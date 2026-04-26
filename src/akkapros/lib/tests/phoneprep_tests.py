from __future__ import annotations

from akkapros.lib.phoneprep import (
    format_selftest_label,
    get_logger_with_fallback,
    is_vv_class_legal,
    log_selftest_result,
    log_selftest_summary,
    parse_symbol_list,
    validate_pattern1,
)


def run_tests() -> bool:
    cases = [
        ('Parse symbol list', lambda: parse_symbol_list('a, b c') == ['a', 'b', 'c'], None),
        ('Vv class plain/plain', lambda: is_vv_class_legal('a', 'ē'), None),
        ('Vv class mixed class', lambda: not is_vv_class_legal('a', 'ɑ'), None),
        ('Validate pattern1 sample', lambda: validate_pattern1(['a', 'm', 'n', 'a', 'm', 'n', 'a']), None),
    ]

    passed = 0
    total = len(cases)
    for index, (name, callback, details) in enumerate(cases, start=1):
        ok = bool(callback())
        if ok:
            passed += 1
        log_selftest_result(
            get_logger_with_fallback(__name__),
            ok,
            'Phoneprep',
            format_selftest_label(index, total, name),
            details=details,
        )

    log_selftest_summary(get_logger_with_fallback(__name__), 'Phoneprep', passed, total)
    return passed == total
