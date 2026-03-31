# Akkadian Prosody Realization Algorithm (LOB/SOB)

## Purpose

This document describes the algorithm currently implemented in
`src/akkapros/lib/prosody.py`. It is written as a readable specification of
what the engine actually does, not as a loose conceptual overview.

The algorithm has four moving parts that must be kept separate:

- structural grouping of words into a prosodic unit
- the mora-mode gate (`bi` or `mono`)
- accent-site selection (`LOB` or `SOB`)
- last-resort repair when no legal internal candidate exists

---

## Symbols and Data Model

### Input (`*_syl.txt`)

| Symbol | Meaning |
|--------|---------|
| `·` | syllable separator |
| `-` | preserved internal boundary |
| `¦` | word end |
| `+` | explicit user-supplied prosodic link |
| `⟦...⟧` / escaped chunks | non-lexical material passed through unchanged |

### Output (`*_tilde.txt`)

| Symbol | Meaning |
|--------|---------|
| `~` | one added mora on the chosen target |
| `+` | prosodic merger / linked unit |
| space | ordinary boundary between independent units |

### Syllable Types and Morae

| Type | Shape | Morae |
|------|-------|-------|
| Light | `CV`, `V` | 1 |
| Heavy | `CVC`, `VC`, `CVV`, `VV` | 2 |
| Superheavy | `CVVC`, `VVC` | 3 |

### Legal Operations

The engine always adds exactly one mora.

| Operation | Legal on | Effect |
|-----------|----------|--------|
| `lengthen_vowel` | `CVV`, `VV`, `CVVC`, `VVC` | insert `~` after the long vowel |
| `geminate_coda` | `CVC`, `VC`, non-final in active unit | append `~` to the syllable |
| `last_resort_accentuation` | any unresolved syllable | geminate onset or glottal onset |

---

## Control Parameters

### Mora Mode

`bi`
: Accentuation is attempted only if the current prosodic unit has odd mora count.

`mono`
: Accentuation may be attempted regardless of current mora parity. `mono` does
not use forward merge as a repair strategy.

### Accent Style

`LOB`
: final superheavy > rightmost non-final heavy > final heavy

`SOB`
: rightmost non-final heavy > final heavy

Mora mode decides **whether** an attempt is made. Accent style decides
**where** the attempt is made.

---

## Structured English Specification

### Main Procedure

For each input line:

1. Parse the line into a sequence of words, explicit `+` markers, and escaped chunks.
2. Scan left to right.
3. If the current token is escaped material, emit it unchanged.
4. If the current token starts an explicit `+` chain, resolve that explicit group.
5. Else if the current token is a function word, resolve the function-word group.
6. Else resolve it as an ordinary lexical word.
7. Restore diphthong spellings after the whole line is processed.

---

## Pseudocode

```text
ACCENTUATION_LINE(tokens):
    result := []
    i := 0

    while i < len(tokens):
        token := tokens[i]

        if token is '+' marker:
            i := i + 1
            continue

        if token is escaped chunk:
            append escaped chunk text to result
            i := i + 1
            continue

        if token begins an explicit '+' chain:
            i := RESOLVE_EXPLICIT_GROUP(tokens, i, result)
            continue

        if token is a function word:
            i := RESOLVE_FUNCTION_GROUP(tokens, i, result)
            continue

        i := RESOLVE_CONTENT_WORD(tokens, i, result)

    return ASSEMBLE_LINE(result, tokens)
```

---

## Ordinary Content Word Resolution

```text
RESOLVE_CONTENT_WORD(tokens, i, result):
    word := tokens[i]

    if CAN_EMIT_WITHOUT_ACCENTUATION(word):
        emit word unchanged
        return i + 1

    accentuation := BEST_ACCENTUATION(word, style)
    if accentuation exists:
        apply accentuation
        emit word
        return i + 1

    if mora_mode = mono:
        apply last resort to the final syllable of word
        emit word
        return i + 1

    return RESOLVE_BY_FORWARD_MERGE(tokens, i, result)
```

### Meaning

- In `bi`, an odd standalone word tries internal accentuation first, then may merge forward.
- In `mono`, a standalone word never merges forward. It either accentuates internally or goes directly to last resort.

---

## Forward Merge (`bi` only)

```text
RESOLVE_BY_FORWARD_MERGE(tokens, i, result):
    merged := [tokens[i]]
    j := i + 1

    while j is a following word and not punctuation/escaped chunk:
        append tokens[j] to merged
        unit := MERGED_UNIT(merged)

        if CAN_EMIT_WITHOUT_ACCENTUATION(unit):
            emit merged with '+'
            return j + 1

        accentuation := BEST_ACCENTUATION(unit, style)
        if accentuation exists:
            apply accentuation
            emit merged with '+'
            return j + 1

        j := j + 1

    apply last resort to the final syllable of the original word
    emit original word
    return i + 1
```

This branch exists only because `bi` requires the active unit to resolve under
bimoraic well-formedness.

---

## Explicit `+` Group Resolution

An explicit `+` chain is a user-supplied prosodic unit. The engine must not
ignore it or split it apart.

### Strict Mode (`only_last = True`)

All linked words before the final linked word are locked from accentuation.
Only the tail domain may receive the internal accent.

### Relaxed Mode (`only_last = False`)

Accentuation may propagate leftward inside the explicit chain. The rightmost
legal site in the whole explicit group is chosen.

### Pseudocode

```text
RESOLVE_EXPLICIT_GROUP(tokens, i, result):
    group := maximal explicit '+' chain starting at i
    unit := MERGED_UNIT(group, locked_prefix_words = explicit_tail_start)

    if CAN_EMIT_WITHOUT_ACCENTUATION(unit):
        emit group with '+'
        return index after the group

    accentuation := BEST_EXPLICIT_GROUP_ACCENTUATION(unit, style, only_last)
    if accentuation exists:
        apply accentuation
        emit group with '+'
        return index after the group

    if mora_mode = mono:
        apply last resort to first syllable of the last word in the explicit group
        emit group with '+'
        return index after the group

    extend the explicit group rightward word by word until punctuation/end:
        if enlarged unit becomes emit-ready in bi mode:
            emit enlarged unit with '+'
            return index after enlarged unit

        if enlarged unit gains a legal accentuation candidate:
            apply accentuation
            emit enlarged unit with '+'
            return index after enlarged unit

    apply last resort to first syllable of the last word in the final enlarged group
    emit final enlarged group with '+'
    return index after the final enlarged group
```

### Important Invariant

Mora mode never overrides explicit-link locking. Pre-tail linked words stay
ineligible for accentuation in both `bi` and `mono`.

---

## Function-Word Group Resolution

Function words are never accented as independent units.

### Forward Attachment

If one or more consecutive function words are followed by a content word, the
whole sequence becomes a grouped unit whose content host is the final word.

```text
RESOLVE_FUNCTION_GROUP(tokens, i, result):
    group := consecutive function words starting at i

    if next token is a content word:
        append that content word to group
        unit := MERGED_UNIT(group, locked_prefix_words = len(group) - 1)

        if not CAN_EMIT_WITHOUT_ACCENTUATION(unit):
            accentuation := BEST_ACCENTUATION(unit, style)
            if accentuation exists:
                apply accentuation to the content-host side
            else:
                apply last resort to first syllable of the content host

        emit group with '+'
        return index after the content host

    if function words are stranded before punctuation/end:
        merge backward with the nearest previous content host
        rollback any previous local accentuation on that host if needed
        rebuild and emit the larger grouped unit

    otherwise:
        emit the function sequence as grouped material
```

### Consequence

The grouped unit is resolved under the active mora mode, but the accent target
remains on the content-host side. The function-word prefix is structurally
locked.

---

## Candidate Selection

### `BEST_ACCENTUATION(word_or_unit, style)`

1. Build the list of legal candidates in priority order.
2. Return the first candidate.
3. If no candidate exists, return `None`.

### Candidate Rules

For a single word:

- `LOB`
  1. final superheavy
  2. rightmost non-final heavy
  3. final heavy

- `SOB`
  1. rightmost non-final heavy
  2. final heavy

For merged units:

- skip locked pre-linker syllables when explicit-link locking applies
- treat non-final heavy positions before a word boundary as eligible for coda gemination
- allow final heavy vowel lengthening according to style priority

---

## Helper Predicate

```text
CAN_EMIT_WITHOUT_ACCENTUATION(unit):
    return (mora_mode = bi) AND (unit should not attempt accentuation)
```

Equivalent reading:

- `bi`: even unit => emit unchanged
- `mono`: never use evenness as a completion shortcut

---

## Diphthong Restoration

The prosody engine operates on the syllabified representation where adjacent
vowels have already been split for unambiguous parsing.

After line-level accentuation is finished, the engine restores diphthongal
spellings while preserving any `~` added by prosody realization.

Example:

```text
u.ʾā~  ->  uā~
```

---

## Escaped Material and Punctuation

- Escaped chunks pass through unchanged.
- They delimit where forward merge may stop.
- In explicit groups and function-word groups, punctuation/end-of-line is a
  hard stop for any rightward growth.

---

## Compact Mathematical Summary

Let $U$ be the structurally determined prosodic unit.

In `bi`:

$$
	ext{if } \mu(U) \equiv 0 \pmod 2, \text{ emit } U \text{ unchanged}
$$

$$
	ext{else try internal accentuation; if it fails, allow forward merge; if still unresolved, use last resort}
$$

In `mono`:

$$
	ext{ignore parity of } U
$$

$$
	ext{try internal accentuation on } U; \text{ if it fails, use last resort directly}
$$

The style parameter then selects the target syllable according to `LOB` or
`SOB`, subject to structural locks from explicit links and function-word
grouping.

**Input (`*_syl.txt`):**

    gi.mir¦dad.mē¦

**Possible output (`*_tilde.txt`, model-dependent target):**

    gi.mir+dad~.mē

**Interpretation:**

- First word cannot resolve independently
- Unit merges forward
- Prosody realization target selected by hierarchy
- One mora added at the selected syllable (`~`)

---

## Worked Example: *Erra and Išum* (lines 21-22)

### Source lines (transliteration)

    engidudu bēlu muttallik mūši muttarrû rubê
    ša eṭla u ardata ina šulmi ittanarrû unammaru kīma ūmi

### Translation

    O Engidudu, lord who wanders in the night, who guides the princes,
    Who leads safely lad and girl, illuminating them like the light of day!

### Command used

    python src/akkapros/cli/fullprosmaker.py outputs/demo_proc.txt \
      -p demo \
      --outdir outputs \
      --print-acute --print-bold --print-ipa

### Prosody-realized pivot (`*_tilde.txt`)

    en~·gi·du·du bē~·lu mut·tal·lik mū~·ši mut·tar·rû ru·bê~
    ša+eṭ·la u+a·rda·ta i·na+šul·mi it·ta·nar~·rû u·nam~·ma·ru kī~·ma ū~·mi

### `--print-acute` output (`*_accent_acute.txt`)

    en´gidudu bē´lu muttallik mū´ši muttarrû rubê´
    ša‿eṭla u‿ardata ina‿šulmi ittanar´rû unam´maru kī´ma ū´mi

### `--print-bold` output (`*_accent_bold.md`)

    **en**gidudu **bē**lu muttallik **mū**ši muttarrû ru**bê**
    ša‿eṭla u‿ardata ina‿šulmi itta**nar**rû u**nam**maru **kī**ma **ū**mi

### `--print-ipa` output (`*_accent_ipa.txt`)

    ˈʔenː.gi.du.du.ˈbeːː.lu.mut.tal.lik.ˈmuːː.ʃi.mut.tar.ruː.ru.ˈbeːː ⟨linebreak⟩ ‖
    ʃa.ʔetˤ.la.ʔu.ʔar.da.ta.ʔina.ʃul.mi.ʔit.ta.ˈnarː.ruː.ʔu.ˈnamː.ma.ru.ˈkiːː.ma.ˈʔuːː.mi ⟨linebreak⟩ ‖

### IPA mode selection

IPA mode is controlled with `--print-ipa-proto-semitic {preserve,replace}`:

| Mode | Description | Mapping |
|------|-------------|---------|
| `preserve` | Old Akkadian distinctions | `ḥ → ħ`, `ḫ → χ`, `ʿ → ʕ`, `ʾ → ʔ` |
| `replace` | Old Babylonian merger | `ḥ → χ`, `ḫ → χ`, `ʿ → ʔ`, `ʾ → ʔ` |

### IPA output conventions

- Spaces and linkers (`+`/`‿`) do not add pauses
- Punctuation emits tags plus a prosodic marker:
  - Weak punctuation: `|`
  - Strong punctuation (including line break): `‖`
- If a line already ends in strong punctuation, line-break deduplication prevents duplicate strong markers

### Note on vowel coloring in IPA

The IPA renderer applies context-sensitive vowel coloring **post-emphatic only** (after `q`, `ṣ`, `ṭ`). As a result:

| Default vowel | After emphatic |
|---------------|----------------|
| `a` | `ɑ` |
| `i` | `ɨ` |
| `u` | `ʊ` |
| `e` | `ɛ` |

Vowels before emphatics remain plain.

---

## Implementation Note

Current behavior corresponds to `src/akkapros/lib/prosody.py` and CLI orchestration in `fullprosmaker.py`.