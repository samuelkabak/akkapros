"""
Shared constants for Akkadian Prosody Toolkit library modules.
"""

# ---- Phonetic inventory ---------------------------------------------------
AKKADIAN_VOWELS = set('\u0101\u0113\u012b\u016b\u00e2\u00ea\u00ee\u00fbaeiu')
AKKADIAN_CONSONANTS = set('bdgkp\u1e6dq\u1e63sz\u0161lmnr\u1e25\u1e2b\u02bf\u02bewyt')

SHORT_VOWELS = set('aeiu')
LONG_VOWELS = set('\u0101\u0113\u012b\u016b\u00e2\u00ea\u00ee\u00fb')
CIRCUMFLEX_VOWELS = set('\u00e2\u00ea\u00ee\u00fb')

# Symbols
GLOTTAL = '\u02be'
SYL_WORD_ENDING = '\u00a6'
SYL_SEPARATOR = '\u00b7'
HYPHEN = '-'
WORD_LINKER = '+'
OPEN_ESCAPE = '\u27e6'
CLOSE_ESCAPE = '\u27e7'

OPEN_PRESERVE_CHAR = '{'
CLOSE_PRESERVE_CHAR = '}'
TAG_PRESERVE_RE = r'[0-9a-z_]{1,16}'
OPEN_PRESERVE_RE = OPEN_PRESERVE_CHAR + TAG_PRESERVE_RE + OPEN_PRESERVE_CHAR
CLOSE_PRESERVE_RE = CLOSE_PRESERVE_CHAR + CLOSE_PRESERVE_CHAR

OPEN_PRESERVE = OPEN_PRESERVE_CHAR + OPEN_PRESERVE_CHAR
CLOSE_PRESERVE = CLOSE_PRESERVE_CHAR + CLOSE_PRESERVE_CHAR

DIPH_SEPARATOR = '\u00a8'

# Treat diphthongs as consonant clusters for syllabification.
AKKADIAN_CONSONANTS.add(DIPH_SEPARATOR)

# Backward compatibility alias (deprecated name)
TIL_WORD_LINKER = WORD_LINKER

# ---- Punctuation pause classes -------------------------------------------
SHORT_PAUSE_PUNCTUATION_CHARS = {
    ',', ';', ':',
    '(', ')', '\u00ab', '\u00bb', '\u201c', '\u201d', '\u2018', '\u2019', '"', "'",
    '/', '\\', '&', '\u2020', '\u2021', '|'
}

SHORT_PAUSE_PUNCTUATION_PATTERNS = (
    r'(?:[:bol:]|^|[ \t]+)\.\.\.(?:[ \t]+|[:eol:]|$)',
    r'(?:[:bol:]|^|[ \t]+)\u2026(?:[ \t]+|[:eol:]|$)',
    r'(?:[:bol:]|^|[ \t]+)\u2014(?:[ \t]+|[:eol:]|$)',
    r'(?:[:bol:]|^|[ \t]+)\u2013(?:[ \t]+|[:eol:]|$)',
    r'(?:[:bol:]|^)#(?:[ \t]+|[:eol:]|$)',
)

LONG_PAUSE_PUNCTUATION_CHARS = {
    '.', '?', '!', '[', ']', '{', '}', '<', '>', '-', '*', '+'
}

LONG_PAUSE_PUNCTUATION_PATTERNS = (
    r'[:bol:]\s*[\-\*\+]\s+(?=.)',
)

LONG_PAUSE_INCLUDES_NEWLINE = True
LONG_PAUSE_INCLUDES_FINAL_EOF = True

# ---- Regex boundary pseudo-tokens ----------------------------------------
REGEX_TOKEN_BOL = '[:bol:]'
REGEX_TOKEN_EOL = '[:eol:]'
# Internal compatibility alias; user docs expose only [:bol:] and [:eol:].
REGEX_TOKEN_EOF = '[:eof:]'

# Sentinels used internally to materialize line/file boundaries for regex.
REGEX_SENTINEL_SOL = '\u0002'
REGEX_SENTINEL_EOL = '\u0003'

# ---- Numeric / currency punctuation suites -------------------------------
NUMBER_REGEX = r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?"
NUMBER_WITH_GROUPS_REGEX = r"-?(?:0|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]+)?"
CURRENCY_SYMBOLS = "$€£¥₽₹₩₪₫₺₴"
DEFAULT_NUMBER_PATTERN = rf"(?:{NUMBER_WITH_GROUPS_REGEX}|{NUMBER_REGEX})"
