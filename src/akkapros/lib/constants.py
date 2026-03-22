"""
Shared constants for Akkadian Prosody Toolkit library modules.
"""

# ---- Phonetic inventory ---------------------------------------------------
AKKADIAN_VOWELS = set('āēīūâêîûaeiu')
AKKADIAN_CONSONANTS = set('bdgkpṭqṣszšlmnrḥḫʿʾwyt')

SHORT_VOWELS = set('aeiu')
LONG_VOWELS = set('āēīūâêîû')
CIRCUMFLEX_VOWELS = set('âêîû')

# Symbols
GLOTTAL = 'ʾ'
SYL_WORD_ENDING = '¦'
SYL_SEPARATOR = '·'
HYPHEN = '-'
WORD_LINKER = '+'
OPEN_ESCAPE = '⟦'
CLOSE_ESCAPE = '⟧'

OPEN_PRESERVE_CHAR = '{'
CLOSE_PRESERVE_CHAR = '}'
TAG_PRESERVE_RE = r'[0-9a-z_]{1,16}'
OPEN_PRESERVE_RE = OPEN_PRESERVE_CHAR + TAG_PRESERVE_RE + OPEN_PRESERVE_CHAR
CLOSE_PRESERVE_RE = CLOSE_PRESERVE_CHAR + CLOSE_PRESERVE_CHAR

OPEN_PRESERVE = OPEN_PRESERVE_CHAR + OPEN_PRESERVE_CHAR
CLOSE_PRESERVE = CLOSE_PRESERVE_CHAR + CLOSE_PRESERVE_CHAR

DIPH_SEPARATOR = '¨'

# Treat diphthongs as consonant clusters for syllabification.
AKKADIAN_CONSONANTS.add(DIPH_SEPARATOR)

# Backward compatibility alias (deprecated name)
TIL_WORD_LINKER = WORD_LINKER

# ---- Punctuation pause classes -------------------------------------------
SHORT_PAUSE_PUNCTUATION_CHARS = {
    ',', ';', ':', '—', '–',
    '(', ')', '«', '»', '“', '”', '‘', '’', '"', "'",
    '/', '\\', '&', '†', '‡', '|'
}

SHORT_PAUSE_PUNCTUATION_PATTERNS = (
    r'\s\.\.\.(?=\s|[:eol:]|$)',
    r'\s…(?=\s|[:eol:]|$)',
)

LONG_PAUSE_PUNCTUATION_CHARS = {
    '.', '?', '!', '[', ']', '{', '}', '<', '>', '-', '*', '+', '#'
}

LONG_PAUSE_PUNCTUATION_PATTERNS = (
    r'^(?:[:bol:])?\.\.\.',
    r'^(?:[:bol:])?…',
)

LONG_PAUSE_INCLUDES_NEWLINE = True
LONG_PAUSE_INCLUDES_FINAL_EOF = True

# ---- Regex boundary pseudo-tokens ----------------------------------------
REGEX_TOKEN_BOL = '[:bol:]'
REGEX_TOKEN_EOL = '[:eol:]'
# Internal compatibility alias; user docs expose only [:bol:] and [:eol:].
REGEX_TOKEN_EOF = '[:eof:]'

# Sentinels used internally to materialize line/file boundaries for regex.
REGEX_SENTINEL_SOL = '<<BOL>>'
REGEX_SENTINEL_EOL = '<<EOL>>'

# ---- Numeric / currency punctuation suites -------------------------------
NUMBER_REGEX = r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?"
NUMBER_WITH_GROUPS_REGEX = r"-?(?:0|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]+)?"
CURRENCY_SYMBOLS = "$€£¥₽₹₩₪₫₺₴"
DEFAULT_NUMBER_PATTERN = rf"(?:{NUMBER_WITH_GROUPS_REGEX}|{NUMBER_REGEX})"
