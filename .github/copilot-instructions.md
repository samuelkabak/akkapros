# Copilot Instructions for Akkadian Prosody Toolkit (akkapros)

## Project Overview

**akkapros** is a computational toolkit for reconstructing Babylonian accentuation from ATF (Akkadian Text Format) files. It solves a fundamental Assyriology problem: traditional grammars describe *where* stress *could* fall (based on syllable weight) but provide no mechanism for *how* stress was realized in connected speech.

### The Problem

When European scholars recite Akkadian, the language sounds rhythmless. Arabic-speaking teachers sound better—closer to something that could be real. This auditory intuition (not abstract theory) motivated the investigation: *the academic stress model provides no mechanism for phrasal timing*.

### The Core Discovery

Acoustic analysis of the Erra and Ishum corpus reveals that Akkadian patterns with **stress-timed languages** (VarcoC = 72.5), similar to English and German. This requires a mechanism for variable timing between fixed stress peaks. Yet the academic model assigns fixed stress positions based solely on syllable weight—giving no way to create the variable timing that stress-timed languages need.

The toolkit implements this via a **bimoraic repair model** that adds exactly 1 mora to selected syllables through gemination or vowel lengthening, organizing speech around bimoraic units (even mora counts, multiple of 2). This produces testable predictions about ancient Babylonian pronunciation.

## eBL ATF Parsing Strategy (`atf_parser.py`)

### Purpose: Phonetic Text Extraction, Not Scholarly Parsing

**Critical distinction**: The parser is designed for extracting clean phonetic material for prosody analysis, *not* for helping scholars parse cuneiform. This means:

- **Strip all markup** that doesn't affect pronunciation
- **Preserve line breaks** (which encode phrasing)
- **Discard structural metadata** (tablet numbers, column markers, etc.)
- **Output: loudly readable text** suitable for direct phonetic processing

### What Gets Extracted

| Element | Treatment | Reason |
|---------|-----------|--------|
| `%%n` lines | **Keep as primary Akkadian** | Contains linguistic content |
| Content in `( )` | Keep content only | Parentheses are editorial markup |
| Content in `[ ]` | Keep content only | Brackets mark restorations; content is part of text |
| Content in `< >` | Keep content only | Angle brackets mark deletions; content is original |
| `{ }` braces | **Remove entirely** | Mark non-Akkadian (Sumerian, glosses) |
| `\| \|` double pipes | Preserve | Mark major structural breaks/alternative readings |
| `.` single vertical bar | Convert to space | Editorial separator between words |
| `-` hyphens | Preserve | Cuneiform sign boundaries may encode morphology |
| `#tr.en:` lines | Store separately | English translations for reference only |
| `HuzNA1 i 1.` etc. | **Ignore completely** | Publication/archive metadata irrelevant to phonetics |
| `x` broken signs | Replace with `...` | Unknown syllables represented as ellipsis |
| `? ! * °` uncertainty marks | Remove | Uncertainty marks don't affect pronunciation |
| Numerals `0-9` | Preserve | May be part of text (Akkadian numbers) |

### Why This Cleanup Strategy

**For phonetics, you need:**
- Consecutive syllables without editorial noise
- Morpheme boundaries (preserved via hyphens)
- Alternative readings (preserved via `||`)
- Known line breaks (phrasing structure)

**For phonetics, you DON'T need:**
- Tablet/column coordinates (HuzNA1, etc.)
- Certainty qualifications (?, *)
- Markup delimiters themselves (`{`, `[`, etc.)
- Structural metadata

### Output Files

| File | Content | Use |
|------|---------|-----|
| `*_proc.txt` | Clean Akkadian with line breaks preserved | **Main input to syllabifier** |
| `*_orig.txt` | Original `%%n` lines with all markup | Reference/comparison |
| `*_trans.txt` | English translations only | Context during analysis |

### Example Processing

**Input (raw eBL ATF):**
```
&X000001 = L I.5 Erra and Išum SB I
#tr.en: King of all settlements ...

1. %n šar (|) gimir (|) dadmē | bānû
#tr.en: The king of all settlements, Banu
HuzNA1 i 1. [LU]GAL gi-mir da-ad₂-me ba-nu#-u#
```

**Output (`*_proc.txt`):**
```
šar gimir dadmē bānû
```

**Why this form?**
- `(|)` removed: editorial separator
- `[LU]` removed: cuneiform logogram substitution
- `#` removed: uncertainty marker
- Line break preserved: phrases remain distinct
- `-` preserved: sign boundaries
- Single `|` becomes space: word boundary

### Implementation Notes

- **One line per line**: Preserve original line structure (encodes phrasing/verse structure)
- **No added newlines within a line**: Cuneiform may wrap; logical lines are single units
- **Empty lines preserved**: Represent significant breaks in the source
- **Spaces normalized**: Multiple spaces → single space
- **No leading/trailing whitespace**: Each line trimmed

## Architecture: The Processing Pipeline

```
ATF Input → Parse → Syllabify → Repair → Metrics → Format Output
```

Each stage is a standalone module in `src/akkapros/cli/` with well-defined I/O:
- **atf_parser.py** (v1.0.0): Extracts clean Akkadian text from eBL ATF markup, preserving line breaks (which encode phrasing)
- **syllabify.py** (v1.2.0): Syllabifies following Huehnergard (2011) rules; marks word boundaries with `¦`; **inserts glottal stops between adjacent vowels** (diphthong expansion for unambiguous syllabification)
- **repair.py** (v1.0.0): Applies moraic repair to achieve bimoraic units; uses one of three accent models (LOB, SOB, AOB)
- **metrics.py** (v2.0.0): Computes acoustic metrics (%V = vowel percentage, ΔC = consonant distance, VarcoC = coefficient of variation of consonant durations)
- **format.py** (v1.0.0): Generates IPA, Markdown, LaTeX outputs (and optionally restores diphthongs)

**Why this pipeline?** Each stage preserves critical information in the intermediate format. For example, the `*_syl.txt` format with pipes and dots allows downstream stages to re-serialize prosodic units (merges) without losing underlying syllable structure. Each stage is independently testable before becoming a building block for the next.

**Data Flow**: Each stage reads the **exact output** of the previous stage. No information is lost. Intermediate files are both human-readable (for debugging) and machine-parseable.

## Phonological Background: Why Repairs Are Legal

Before understanding repair rules, understand what's already in Akkadian's phonology:

- **Gemination as native process**: N-assimilation (_indin_ → _iddin_), T-infix assimilation (_iṣtabat_ → _iṣṣabat_). Geminated consonants are phonologically distinct.
- **Vowel syncope**: Unstressed short vowels delete under conditions (_napištum_ → _napšātum_), but syncope is blocked if it creates illegal tri-consonantal clusters.
- **Anaptyxis**: When syncope would create illegal clusters, vowels are inserted. This shows the language actively repairs syllable structure.
- **Geers' Law**: Two emphatics cannot co-occur in a root; one dissimilates. Evidence of articulatory ease prioritizing production.

**Key insight**: The toolkit's repair operations (gemination, vowel lengthening) are not invented—they're already present in Akkadian phonology. We're systematizing their use for a different purpose (rhythm), but they're grounded in native phonological processes.

## Why Specific Repairs Are Legal & Illegal

### Legal Operations

| Operation | Why Legal | Where Attested |
|-----------|----------|-----------------|
| **Vowel lengthening** (CVV, CVVC) | Already present in morphology (short vs. long vowel contrast); operations within existing system | Comparative Semitic (root internal variations) |
| **Coda gemination** (CVC, VC non-final) | Attested via morphological processes; phonologically systematic | N-assimilation: _in_ + verb → geminated consonant |

### Illegal Operations (Why Never Performed)

| Operation | Why Illegal | Evidence |
|-----------|----------|----------|
| **Lengthen short vowels** (CV → CVV) | Would neutralize phonemic vowel length contrast (CV vs. CVV); creates homophony | Akkadian clearly distinguishes lexical short vs. long |
| **Geminate final consonants** (CVC# → CVC:#) | Word-final geminates unattested in Akkadian phonotactics | Consonant clusters prohibited at word boundaries |
| **Geminate onset consonants** (CV → C:V) | Onset consonants are not available for gemination without resyllabification | Gemination affects coda position only |

**Design principle**: Repairs use only operations available in the language and follow syllable structure constraints. No invented phonetics.

### The Bimoraic Target

Akkadian organizes rhythm around **bimoraic units** (even mora counts). In connected speech, words or merged groups must achieve even total morae. This explains:
- **Why repair is needed**: Odd-mora words can't form stress-timed rhythm alone
- **Why merging occurs**: Words combine prosodically until reaching even counts
- **Why timing is variable**: Between fixed stress peaks, weak syllables absorb timing variation

### Three Accent Models & Their Philosophy

All three models derive from the **academic stress hierarchy** (rightmost heavy syllable, defaulting to first) but differ in how they handle special cases:

| Model | Priority 1 | Priority 2 | Priority 3 | Rationale |
|-------|-----------|-----------|-----------|-----------|
| **LOB** (Literary) | Final superheavy (CVVC/VVC + circumflex) | Rightmost non-final heavy | Final heavy | Streck (2022): Literary Old Babylonian attests special treatment of circumflex vowel finals. Respects this evidence. |
| **SOB** (Standard) | Rightmost non-final heavy | Final heavy | (none) | Huehnergard (2011): Standard rule across most OB texts; avoids word-final repairs when possible. |
| **AOB** (Academic) | Final superheavy | Rightmost non-final heavy | First syllable | Traditional description: defaults to first syllable if no heavy exists (onset gemination as last resort). |

**Why the hierarchy includes "Priority 2 or 3"**: When no syllable meets Priority 1 criteria, the model falls back. This ensures all words find a repair target. Some words (e.g., all-light CV sequences) require the fallback.

**All three share**: Same repair operations, same legal/illegal definitions, same merge/unmerge logic. They differ *only* in which syllable gets selected for repair within a word or merged unit.

### Repair Operations (in priority order)

| Operation | Applies To | Effect | Notation | Phonetic |
|-----------|-----------|--------|----------|----------|
| **Lengthen vowel** | CVV, VV, CVVC, VVC | Long vowel → extra-long | `~` after vowel | `rā` → `rà` |
| **Coda gemination** | CVC, VC (non-final) | Coda consonant geminated | `~` at end | `dad` → `daː d` |
| **Onset gemination** | CV (last resort only) | Consonant geminated | `C~V` | `ka` → `kːa` |
| **Glottal gemination** | V (last resort only) | Glottal stop geminated | `~V` | `a` → `ʔːa` |

**Why this hierarchy?** Vowel lengthening is phonetically most natural and least disruptive. Coda gemination is attested in closed syllables. Onset gemination is only used when no legal repair exists (rare, <1% in real texts). Final consonant gemination is **never done** (unattested in Akkadian).

## Critical Phonetic Conventions

**Never hardcode phonetic character sets.** All are module-level constants loaded at import:

```python
# Akkadian core inventory (in every CLI module):
AKKADIAN_VOWELS = set('āēīūâêîûaeiu')  # Short, long, circumflex vowels
AKKADIAN_CONSONANTS = set('bdgkpṭqṣszšlmnrḥḫʿʾwyt')
SHORT = set('aeiu')
LONG = set('āēīūâêîû')
EXTRA_LONG = set('àìùè')  # For repaired text with tilde markers
```

**Consonant gemination**: Marked with `:` (e.g., `mas:ta` = geminatedalveolar-stop). This is critical in **metrics.py** calculations.

## Text Format Conventions

### Special Markers

| Marker | Module | Meaning | Example |
|--------|--------|---------|---------|
| `\|` | syllabify | Temporary word ending (replaced by ¦) | `ku.u\|` |
| `¦` | repair, metrics | Final word ending marker | `ku.u¦` |
| `.` | all | Syllable separator | `ta.bu.tum` |
| `~` | repair, metrics | Tilde marker for repaired/accented syllables | `TA.bu.tum` → `tà.bu.tum` |
| `-` | syllabify | **Prosodic boundary** (construct state, clitics, compounds) | `bīt-šarrim` |
| `[...]` | syllabify | Non-Akkadian text (preserves internal whitespace) | `[Sum: lugal]` |
| `_` | repair | **Merged words** (no prosodic pause, shared stress unit) | `gi.mir_dad~.mē` |
| `$` | metrics | Word boundary in pause calculations | `sa$li$iš` |

### Entry/Exit Formats (Per Stage)

- **ATF → Parse** (`atf_parser.py`): Raw eBL format (`%%n`, `#tr.en:`) → Clean ASCII Akkadian text (`*_proc.txt`)
- **Parse → Syllabify** (`syllabify.py`): Single-line text → Syllabified with word markers (`*_syl.txt`)
- **Syllabify → Repair** (`repair.py`): Syllabified with pipes and dots → Tilde-marked pivot format (`*_tilde.txt`)
- **Repair → Metrics** (`metrics.py`): Tilde format → JSON metrics (`*_metrics.json`)
- **Metrics → Format** (`format.py`): Tilde format → IPA/Markdown/LaTeX (`*_ipa.txt`, `*_md.txt`, `*_tex.tex`)

### The Pivot Format (`*_tilde.txt`)

This is the master format. All downstream processing derives from it:
- **Space** = normal word boundary (words are prosodically independent)
- **Underscore `_`** = merged words (no pause, single stress unit, morae counted across the merge)
- **Tilde `~`** = repair marker on the syllable where stress lands
- **Syllable boundaries** = dots (`.`) and hyphens (`-`) preserved from input

Example: `šar gi.mir_dad~.mē bā.nû kib.rā~.ti`
- `šar` = standalone word
- `gi.mir_dad~.mē` = merged unit (gimir is odd mora, merges with dadmē; stress falls on dad)
- `bā.nû` = standalone word
- `kib.rā~.ti` = standalone word (stress on rā)

## Key Development Patterns

### 1. Function Words and Merge Logic

Function words (prepositions, conjunctions, particles, pronouns) **cannot be stressed independently**. When encountered, they must merge with adjacent content words:

```python
FUNCTION_WORDS = {
    'ana', 'ina', 'ištu', 'itti', 'eli',  # Prepositions
    'ul', 'ula', 'lā',                    # Negations
    'ša', 'u', 'ū', 'lū',                 # Conjunctions
    'anāku', 'nīnu', 'atta', ...          # Pronouns
}
```

**Merge algorithm** (in `repair.py`):
1. **Forward merge**: Combine odd-mora word with next word(s) until bimoraic or repair succeeds
2. **Backward merge**: If forward fails at punctuation, merge with previous word
3. **Last resort**: If all merges fail, apply onset gemination on first syllable

Example: `u ana šarri` → all function words merge: `u_ana_šar.ri`

### 2. Hyphen as Prosodic Marker

The hyphen (`-`) in input text **explicitly joins words into a single stress unit**:
- **Construct state**: `bīt-šarrim` (noun in construct + genitive)
- **Enclitics**: `ī.ris.sū-ma` (verb + particle)
- **Compounds**: `amēlu-ša-īšum` (fused lexical items)

The hyphen is preserved in output and treated identically to dots as syllable boundaries. This allows users to mark constructions that should form a single prosodic unit based on their linguistic knowledge, rather than attempting automatic syntactic analysis.

### 3. Diphthong Processing

Akkadian texts may preserve diphthongs (vowel sequences in hiatus, e.g., `ua`, `iā`). Since the repair algorithm operates on clear syllable boundaries, diphthongs undergo **two-phase processing**:

**Phase 1: Expansion** (`syllabify.py`):
- Insert glottal stop between vowels: `ua` → `u.ʾa`
- This creates two clear CV syllables without changing mora counts

**Phase 2: Restoration** (`repair.py --restore-diphthongs`):
- After repair, convert back: `u.ʾā~` → `uā~`
- Preserves repair markers and total mora counts
- First vowel in diphthong always short (Akkadian constraint)

Usage: `python repair.py text_syl.txt --restore-diphthongs -o output`

### 4. Phonetic Inventory Extensibility

All CLI modules support foreign character injection via command-line arguments:

```python
# syllabify.py example
parser.add_argument('--extra-vowels', help='Additional vowel characters')
FOREIGN_VOWELS = set(args.extra_vowels) if args.extra_vowels else set()
ALL_VOWELS = AKKADIAN_VOWELS | FOREIGN_VOWELS | EXTRA_VOWELS | EXTRA_LONG
```

When extending for non-Akkadian text, update ALL_AKKADIAN accordingly.

### 5. Accent Models

**repair.py** implements three accent models via `AccentStyle` enum:

- **LOB** (Literary Old Babylonian): Prioritizes final superheavy syllables (circumflex-bearing). Use for poetic texts.
- **SOB** (Standard Old Babylonian): Prioritizes rightmost non-final heavy syllables. Use for most texts.
- **AOB** (Academic Old Babylonian): Matches traditional grammatical descriptions; uses first syllable as fallback.

Always specify which model is being tested/applied. All three share identical repair operations; they differ only in stress placement selection.

### 6. Consonant Distance Metrics

**metrics.py** calculates ΔC based on consonant type and position:

```python
# Simplified conceptually
CONSONANT_DISTANCES = {
    'obstruents': {'+voice': 0, '-voice': 1},
    'sonority': distance_based_on_manner,
    'uvular': special_weight_for_ḫ, 'ḥ'
}
```

When debugging metric calculations, verify consonant classification first.

## Testing & Development Workflow

### High-Risk Functions Requiring Extensive Testing

**Do NOT rewrite these functions without comprehensive test coverage monitoring:**

#### `tokenize_line()` and `syllabify_text()` in `syllabify.py`

These functions took **days to debug** and handle complex edge cases:

| Challenge | Example | Why It's Hard |
|-----------|---------|---------------|
| **Hyphen vs dash distinction** | `ḫendur-sanga` (hyphen, attached) vs `ḫendur - sanga` (dash, spaced) | Requires context-aware char inspection |
| **Whitespace normalization** | Multiple spaces, tabs, newlines all treated differently | Must preserve line breaks (phrasing) but normalize word separation |
| **Punctuation preservation** | Numbers, commas, ellipsis, em-dashes must all wrap in brackets | Cannot assume punct = single char |
| **Hyphen split across lines** | Hyphenated word broken at line end must be merged with warning | Requires lookahead to next line |
| **Diphthong expansion** | Insert glottal stop between adjacent vowels for unambiguous syllabification | Adds complexity to vowel detection |
| **Bracket handling** | `[foreign text]` must preserve ALL internal whitespace but not affect word parsing | State machine needed |

#### The Test Suite

The `run_tests()` function in `syllabify.py` contains **~40 comprehensive test cases** covering:

- All syllable types (CV, CVC, CVV, CVVC, VC, V, VV, VVC)
- Multi-syllable combinations
- Hyphen preservation vs merging
- Dash vs hyphen distinction
- Whitespace variations (spaces, tabs, newlines, double newlines)
- Numbers and non-Akkadian text
- Punctuation (commas, periods, em-dashes, ellipsis)
- Diphthongs
- Real complex lines

**Even with these tests, edge cases may not be fully covered.**

### How to Extend These Functions Safely

1. **Add a test case FIRST** for your new scenario
2. **Verify it fails** with current code
3. **Make minimal change** to the function
4. **Verify ALL existing tests still pass** before committing
5. **Run with `--test` flag** to validate: `python syllabify.py --test`

### When to Rewrite vs Extend

| Scenario | Recommendation |
|----------|-----------------|
| **Bug in specific case** | Add test, fix in-place, verify all tests pass |
| **Add new character class** | Update phonetic sets, test with `--extra-vowels` / `--extra-consonants` |
| **Change syllabification rules** | This is core logic—add tests first, proceed with extreme caution |
| **Refactor for clarity** | DO NOT do this without full test coverage and careful monitoring |

### Environment Setup (PowerShell)

```powershell
# Activate environment (Windows)
.\sandbox\activate_project.ps1

# Install dependencies for development
.\sandbox\venv_pip_install_dev.ps1
```

### Running Tests

```bash
# Run syllabifier tests
python syllabify.py --test

# Run repair tests
python repair.py --test

# Run all pytest tests
pytest sandbox/test_*.py -v

# Test patterns: sandbox/test_*.py files test individual modules
# conftest.py contains shared test utilities
```

### Directory Navigation

- **Source code**: `src/akkapros/cli/` (CLI entrypoints) and `src/akkapros/lib/` (future API layer)
- **Data samples**: `data/samples/` (e.g., `erra-and-ishum-SB.atf`)
- **Tests**: `sandbox/` (pytest convention, not standard `tests/`)
- **Intermediate outputs**: `outputs/` (processed text files)

## Common Editing Scenarios

### Adding a New Repair Algorithm Variant

1. Extend `AccentStyle` enum in **repair.py**
2. Add logic in `repair_phrase()` that checks `accent_style`
3. Update the priority hierarchy for syllable selection
4. Test against known Akkadian phrases (likely in sandbox tests)
5. Keep function word exclusion consistent

### Extending Phonetic Coverage

1. Update module-level phonetic sets (VOWELS, CONSONANTS)
2. Check if **syllabify.py** needs syllabification rules for new characters
3. If diphthongs are involved, verify **syllabify.py** inserts glottal stops correctly
4. Add IPA mappings in **format.py** if outputting IPA
5. Test with foreign text pattern: `word [foreign.text] word`

### Debugging Syllable Boundaries

1. Check word ending marker (`¦`) at output of **syllabify.py**
2. Verify syllable separation (`.`) in intermediate outputs
3. Trace hyphen (`-`) vs dash handling: attached = syllable separator, spaced = punctuation
4. Confirm non-Akkadian text in `[brackets]` is preserved as-is
5. If diphthongs present, verify glottal stops inserted between vowels

### Debugging Merge Logic

1. Identify which word triggered merge (odd morae after internal repair)
2. Check `Word.morae` property vs `Word.repaired_morae`
3. Trace merge direction: forward (default) or backward (at punctuation)
4. Verify function word handling: must merge with content words
5. Check final output has all even-morae groups

### ⚠️ WARNING: Modifying High-Risk Parser Functions

**Do NOT rewrite `tokenize_line()` or `syllabify_text()` without extensive testing.**

These functions took days to debug and handle dozens of edge cases (hyphen vs dash, whitespace normalization, bracket preservation, diphthong expansion, etc.).

**If you must modify them:**

1. **Write a test case FIRST** that captures your scenario
2. **Verify the test fails** with current code
3. **Make the minimal change** necessary
4. **Run the full test suite**: `python syllabify.py --test`
5. **Verify ALL tests pass** before committing
6. **Monitor edge cases** after deployment

The test suite covers ~40 cases but may not be exhaustive. Each change is a risk.

## Stress-Timed vs. Other Rhythmic Types

### Why Akkadian Must Be Stress-Timed

The core insight: **Acoustic metrics applied to the corpus reveal VarcoC = 72.5**, which classifies Akkadian with stress-timed languages.

### Comparison with Major Language Types

#### Stress-Timed Languages (English, German, Dutch)

| Metric | English Range | Akkadian (Original) | Akkadian (Repaired) | Interpretation |
|--------|---------------|-------------------|-------------------|-----------------|
| VarcoC | 70–80 | 72.5 | 86.6 (initially high, but post-repair analysis shows convergence) | Akkadian's VarcoC approaches stress-timed range, particularly after repairs |
| Information Rate | ~39 bits/sec | ~39 bits/sec | ~39 bits/sec | All languages transmit at same rate; differences are in speech rate |

#### Syllable-Timed Languages (French, Spanish, Italian)

- VarcoC: 50–55
- **Akkadian at 72.5 is significantly higher, ruling out this classification**

#### Mora-Timed Languages (Japanese)

- VarcoC: ~37
- ΔC (consonant distance): extremely low
- **Akkadian at 72.5 is much higher, clearly not mora-timed**

### Why This Classification Matters

Stress-timed languages require a mechanism for **variable timing between fixed stress peaks**. Unlike syllable-timed languages (where syllables are isochronous) or mora-timed languages (where morae are isochronous), stress-timed languages must absorb timing variability somewhere. The Akkadian prosody toolkit fills this gap: the repair algorithm creates the necessary timing variability by modifying syllable structure, while keeping lexical stress positions fixed.

## Metrics (`metrics.py`): Quantifying Rhythmic Structure

### Purpose & Approach

**metrics.py** computes acoustic and statistical metrics from the `.tilde` pivot format (not audio). Unlike audio-based analysis that works from speech signals directly, it makes explicit assumptions about how orthographic length markers correspond to durational differences. This enables analysis of ancient texts without recorded speech.

**Key Design**: The module processes text in three stages:
1. **Original structure** (no `~` markers) - baseline syllable structure
2. **Repaired structure** (`~` markers included) - effect of repairs on syllables
3. **Comparison** - quantify what the algorithm changed

### Input Format: The `.tilde` Pivot

```
šar gi.mir_dad~.mē bā.nû kib.rā~.ti ...
```

- **Syllable boundaries**: `.` or `-` (preserved from input)
- **Word boundaries**: space (normal) or `_` (merged, no pause)
- **Repair markers**: `~` indicates mora was added

### Core Metrics

#### %V (Vowel Percentage)

**Formula**: `(vowel_morae / total_morae) × 100`

**Computation**: Count morae in vowels vs. consonants across all syllables
- Short vowels (a,i,u,e) = 1μ
- Long vowels (ā,ī,ū,ē,â,î,û,ê) = 2μ  
- Extra-long vowels (à,ì,ù,è, from repairs) = 3μ
- Coda consonants = 1μ

**Interpretation**: Higher %V = more time on vowels. Akkadian's high %V (~74-80%) reflects its CV-heavy syllable structure. As repairs add consonant morae, %V decreases.

#### ΔC (Consonant Distance Std Dev)

**Computation**:
1. Extract all consonants in reading order
2. For each consonant pair, count morae between them (vowels + length markers)
3. Calculate standard deviation of distances

**Interpretation**: 
- Low ΔC (30-55) = syllable-timed (regular consonant spacing)
- High ΔC (70-85) = stress-timed (variable spacing)

Akkadian's ΔC increases with repairs (roughly +15%), indicating variable consonant spacing like English.

#### MeanC (Mean Consonant Interval)

**Formula**: `mean(consonant_distances)`

**Interpretation**: Average morae between consonants. Increases with repairs as vowels lengthen.

#### VarcoC (Rate-Normalized Variability)

**Formula**: `(ΔC / MeanC) × 100`

**Critical metric**: Independent of speech tempo; the most robust classifier of rhythmic type

- Stress-timed languages: VarcoC ≈ 70–85
- Syllable-timed: VarcoC ≈ 50–55
- Mora-timed: VarcoC ≈ 35–40

**Akkadian shows VarcoC ≈ 67.7 (original) → 69.6 (repaired)**, confirming stress-timed rhythm.

### Syllable Classification

Every syllable is classified by type. The classification changes between original and repaired versions:

**Original types**: CV (1μ), CVC (2μ), CVV (2μ), CVVC (3μ), VC (2μ), V (1μ), VV (2μ), VVC (3μ)

**Repaired types** (when modified):
- C:V = onset gemination (2μ)
- CVC: = coda gemination (3μ)
- CVV: = vowel lengthening (3μ)
- CVV:C = superheavy lengthening (4μ)

### Speech Rate Estimation

The module estimates plausible speech rates using cross-linguistic calibration:

**Parameters**:
- Default WPM: 165 (midpoint across English 150-180, Romance 180-220, Japanese 130-160)
- Pause ratio: 35% (typical natural speech 30-40%)

**Derived metrics**:
- Syllables per second (articulation rate): ~5.81 SPS for Akkadian
- Mora duration: ~70 ms (within human perceptual range)
- Word duration: 364 ms (60 / 165 WPM)

**Rationale**: All languages transmit information at ~39 bits/second. Speech rate variability across languages reflects information density differences, not rhythmic differences.

### Repair Statistics Tracked

For each line and the whole text:

| Statistic | Meaning |
|-----------|---------|
| Total syllables | Unchanged by repairs |
| Repaired syllables | Count of syllables modified |
| Repair rate (%) | Percentage modified (typical: ~19% for Erra) |
| Repair type breakdown | Distribution of: vowel lengthening, coda gemination, etc. |

### Output Format

The module produces JSON and human-readable text containing:
- Before/after comparison for all metrics
- Syllable type distributions
- Repair statistics
- Bootstrap confidence intervals (95% CI) for VarcoC
- Comparison with language typologies

## Repair Rate & Emergent Behavior

### The 19.1% Repair Rate is Not Designed

The observed repair rate (19.1% of syllables modified in Erra and Ishum) is **emergent from constraint interaction**, not a design parameter:

1. **Syllable type distribution** - 57.6% of syllables are 1-mora (CV, V), which cannot be repaired internally
2. **Word boundaries** - Words are processed independently; even-mora targets are computed per-word
3. **Repair rules** - Legal/illegal definitions prevent certain repairs (no final gemination, no onset gemination except last resort)
4. **Hierarchy** - Priority 1 > Priority 2 > Priority 3 selects specific syllables
5. **Merge/unmerge logic** - Words combine only when necessary, then unmerge after repair

**Result**: Different syllable distributions or different rules would yield different rates. The fact that 19.1% falls in a cross-linguistically plausible range (15-20% for stress-timed prominence) suggests the hypothesis is reasonable, but this is not proof.

### Cross-Linguistic Plausibility

Stress-timed languages typically realize 15-20% of syllables as phonetically prominent (through lengthening, intensification, or other means). The repair rate corresponds to the proportion of syllables that must be phonetically modified to achieve isochrony. This alignment supports the model's face validity.

## What This Model Does & Doesn't Claim

### What the Model DOES Claim

1. Akkadian exhibits the acoustic signature of stress-timing (VarcoC = 72.5)
2. The academic model identifies a plausible candidate set (where stress *could* go)
3. Some mechanism must connect eligibility to realization in connected speech
4. The repair hypothesis is one working model that fills this gap
5. It produces specific, testable predictions about repair patterns
6. It accounts for the observed data
7. The repair rate emerges from constraint interaction, not arbitrary design

### What the Model Does NOT Claim

- **Not that this is the only possible hypothesis** - Other models might work equally well
- **Not that 19.1% is the "true" historical repair rate** - Different texts may differ; this is one corpus
- **Not that speech rate can be reliably reconstructed** - Estimates are speculative, calibrated to cross-linguistic ranges
- **Not that the CVVC treatment is historically correct** - Two plausible hypotheses (lengthen or shorten) both yield stress-timed results
- **Not that the repaired text represents actual Akkadian speech** - It represents one possible realization consistent with acoustic constraints

### The Core Contribution

The model shows that a **rhythmically coherent output** can be generated from a rhythmless input using operations that are:
- Phonetically plausible (attested in Akkadian)
- Philologically grounded (based on academic stress rules)
- Algorithmically systematic (deterministic, reproducible)

**Distinction**: The academic model describes *writing* and *meter*. Our model describes *speech*.

## Research Development & Validation

### Iterative Development Process

The repair algorithm was not derived deductively but developed through extensive trial and error:

1. **Initial hypothesis** (even compression of short vowels) - Failed; produced out-of-range VarcoC
2. **Problem diagnosis** - Arbitrary compression ignores syllable structure and stress
3. **Arabic insight** - CVC as rhythmic unit in Levantine; inspired bimoraic hypothesis
4. **Symmetry principle** - Lengthen instead of compress; preserves lexical contrasts
5. **Phonological grounding** - Check that all operations are attested in Akkadian
6. **Systematization** - Define legal/illegal repairs with linguistic justification
7. **Hierarchy refinement** - Base priority on academic stress rules, Literary OB evidence
8. **Implementation** - Build algorithm, test on small sample, validate before full corpus

### Validation Against Small Sample

Before full corpus application, the algorithm was tested on a 4-line, 27-word sample (hand-analyzed for correctness) with **100% accuracy**. This gave confidence in the implementation before scaling.

### Sensitivity Analysis

Two competing hypotheses for CVVC treatment were tested:

- **Hypothesis A** (lengthen): CVVC → CVV:C preserves lexical length
- **Hypothesis B** (shorten): CVVC → CVC follows later historical development

**Result**: Both yield stress-timed VarcoC (difference < 0.1, within 95% CI ±2.8). The choice doesn't affect rhythmic classification, validating robustness.

### Transparency & Reproducibility

- All code is provided for inspection and replication
- Decision points are documented with linguistic justification
- None of the algorithm parameters are arbitrary; all are motivated by Akkadian phonology or acoustic theory

## Version & Documentation Style

- Each module declares `__version__`, `__author__`, `__license__`, `__project__`, `__repo__`
- Docstrings include version number and format examples
- Enum-driven configuration (e.g., `AccentStyle`, `TestResult`) for type safety
- Data classes for structured outputs (e.g., `TestCase` in atf_parser.py)

## External Dependencies

- **Runtime**: None (pure Python)
- **Development**: pytest, black, flake8, sox (audio processing for future speech synthesis)
- **External tools**: DiaMoE-TTS (called as subprocess, not imported)

---

**Last Updated**: 2026-02-25 | **Project Version**: 1.0.0
