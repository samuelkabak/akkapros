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

# ---- Akkadian text-detection constants -----------------------------------
# Distinctively Akkadian characters (rare in other writing systems).
AKKADIAN_DISTINCTIVE: frozenset = frozenset('ṭṣšḥḫʿʾ')

# Characters whose presence makes Akkadian identification impossible.
NON_AKKADIAN_CHARS: frozenset = frozenset('ofxvjc')

# Common Akkadian enclitics (without the prosodic hyphen).
# Used for word-suffix detection when scoring likelihood of Akkadian text.
# Source: Huehnergard (2011) §17–19; von Soden (1969) §§47–50.
AKKADIAN_ENCLITICS: frozenset = frozenset({
    'ma', 'mi',                             # coordinative / quotative
    'šu', 'šū', 'šī', 'šunu', 'šina',      # 3rd-person object / possessive
    'ya', 'ia',                             # 1st-person singular possessive
    'ni',                                   # subjunctive suffix
    'ku', 'ki', 'kunu', 'kina',             # 2nd-person possessive
    'nu',                                   # 1st-person plural suffix
})

# Canonical Akkadian function-word list: prepositions, conjunctions, pronouns.
# Shared by prosody realization (ADR-009) and text-detection scoring.
# Canonical source: Huehnergard (2011); see also ADR-009.
FUNCTION_WORDS: frozenset = frozenset({
    'ana', 'ina', 'ištu', 'itti', 'eli',    # prepositions
    'ul', 'ula', 'lā',                       # negations
    'ša',                                    # relative / genitive particle
    'u', 'ū', 'lū',                          # conjunctions / assertive
    'anāku', 'nīnu', 'atta', 'atti', 'attunu', 'attina',   # pronouns
    'šū', 'šī', 'šunu', 'šina',             # 3rd-person independent pronouns
})
