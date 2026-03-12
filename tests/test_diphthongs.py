import unittest
from typing import List

from akkapros.lib.constants import DIPH_SEPARATOR, SYL_SEPARATOR
from akkapros.lib.repair import postprocess_restore_diphthongs


def restore(lines: List[str]) -> List[str]:
    """Proxy helper to keep test call-sites concise."""
    return postprocess_restore_diphthongs(lines)


class TestDiphthongsPatterns(unittest.TestCase):
    """Test DIPH_SEPARATOR-based diphthong restoration output."""
    
    def setUp(self):
        self.maxDiff = None
    
    def test_identical_short_vowels(self):
        """Test identical short vowels become circumflex."""
        test_cases = [
            ([f"a{SYL_SEPARATOR}{DIPH_SEPARATOR}a"], ["â"]),
            ([f"i{SYL_SEPARATOR}{DIPH_SEPARATOR}i"], ["î"]),
            ([f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}u"], ["û"]),
            ([f"e{SYL_SEPARATOR}{DIPH_SEPARATOR}e"], ["ê"]),
            ([f"ka{SYL_SEPARATOR}{DIPH_SEPARATOR}a"], ["kâ"]),
            ([f"ta{SYL_SEPARATOR}{DIPH_SEPARATOR}a ki"], ["tâ ki"]),
        ]
        for input_lines, expected in test_cases:
            with self.subTest(input=input_lines[0]):
                result = restore(input_lines)
                self.assertEqual(result, expected)
    
    def test_u_patterns_short_first(self):
        """Test u patterns with short first vowel."""
        test_cases = [
            ([f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}a"], ["ua"]),
            ([f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}ā"], ["uā"]),
            ([f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}â"], ["uâ"]),
            ([f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~"], ["uā~"]),
            ([f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}â~"], ["uâ~"]),
        ]
        for input_lines, expected in test_cases:
            with self.subTest(input=input_lines[0]):
                result = restore(input_lines)
                self.assertEqual(result, expected)
    
    def test_u_patterns_long_first(self):
        """Test u patterns with long first vowel."""
        test_cases = [
            ([f"ū{SYL_SEPARATOR}{DIPH_SEPARATOR}a"], ["uā"]),
            ([f"ū{SYL_SEPARATOR}{DIPH_SEPARATOR}ā"], ["uā~"]),
            ([f"ū{SYL_SEPARATOR}{DIPH_SEPARATOR}â"], ["uâ~"]),
            ([f"ū{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~"], ["uā"]),
            ([f"ū{SYL_SEPARATOR}{DIPH_SEPARATOR}â~"], ["uâ"]),
        ]
        for input_lines, expected in test_cases:
            with self.subTest(input=input_lines[0]):
                result = restore(input_lines)
                self.assertEqual(result, expected)
    
    def test_a_i_patterns(self):
        """Test a + i combinations."""
        test_cases = [
            ([f"a{SYL_SEPARATOR}{DIPH_SEPARATOR}i"], ["ai"]),
            ([f"a{SYL_SEPARATOR}{DIPH_SEPARATOR}ī"], ["aī"]),
            ([f"a{SYL_SEPARATOR}{DIPH_SEPARATOR}î"], ["aî"]),
            ([f"a{SYL_SEPARATOR}{DIPH_SEPARATOR}ī~"], ["aī~"]),
            ([f"a{SYL_SEPARATOR}{DIPH_SEPARATOR}î~"], ["aî~"]),
            ([f"ā{SYL_SEPARATOR}{DIPH_SEPARATOR}i"], ["aī"]),
            ([f"ā{SYL_SEPARATOR}{DIPH_SEPARATOR}ī"], ["aī~"]),
            ([f"ā{SYL_SEPARATOR}{DIPH_SEPARATOR}î"], ["aî~"]),
            ([f"ā{SYL_SEPARATOR}{DIPH_SEPARATOR}ī~"], ["aī"]),
            ([f"ā{SYL_SEPARATOR}{DIPH_SEPARATOR}î~"], ["aî"]),
        ]
        for input_lines, expected in test_cases:
            with self.subTest(input=input_lines[0]):
                result = restore(input_lines)
                self.assertEqual(result, expected)

    def test_residual_separator_removed(self):
        """Residual standalone DIPH_SEPARATOR is stripped from output."""
        result = restore([f"ba{DIPH_SEPARATOR}ru"])
        self.assertEqual(result, ["baru"])


if __name__ == '__main__':
    unittest.main()