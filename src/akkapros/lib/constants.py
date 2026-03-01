"""
Shared constants for Akkadian Prosody Toolkit library modules.

This module is intended as the central location for values that appear in
multiple places across the codebase, such as phonetic inventories,
regular expressions, default configuration values, etc.

At the moment it is an empty placeholder; constants can be added here when a
refactor reveals that they are truly shared.  Keeping this file separate
prevents circular imports when the constants are needed by both CLI tools and
library code.

Example use (future):
    from akkapros.lib.constants import AKKADIAN_VOWELS

"""

# Shared constants for phonetic inventory and other values used across
# multiple modules in the Akkadian Prosody Toolkit.

# ---- Phonetic inventory ---------------------------------------------------
# Core Akkadian vowel and consonant sets.  These are loaded by both the
# syllabification and metrics modules so they live here to avoid duplication.

AKKADIAN_VOWELS = set('āēīūâêîûaeiu')
AKKADIAN_CONSONANTS = set('bdgkpṭqṣszšlmnrḥḫʿʾwyt')

# Vowel length categories (short, long).  
# primarily by the metrics module, but defining it here keeps the inventory
# consistent.
SHORT_VOWELS = set('aeiu')
LONG_VOWELS = set('āēīūâêîû')
EXTRA_LONG_VOWELS = set('àìùè')

# Symbols
GLOTTAL = 'ʾ'          # glottal stop symbol (U+02BE)
SYL_WORD_ENDING = '¦'       # marker used by the syllabifier
SYL_SEPARATOR = '·'          # separator between syllables in the syllabifier output
OPEN_ESCAPE = '‹'
CLOSE_ESCAPE = '›'

OPEN_IGNORE = '['
CLOSE_IGNORE = ']'


TIL_WORD_LINKER = '+'


# Additional constants may be added here when shared across modules.
