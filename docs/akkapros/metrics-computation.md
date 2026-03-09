# Metrics Computation

This document explains every metric reported by `akkapros` metrics output: what each metric designates, how it is computed, and which unit it uses.

Implementation scope:
- `src/akkapros/lib/metrics.py`
- `src/akkapros/cli/metricser.py`
- `src/akkapros/cli/fullreparer.py` (metrics stage)

## 1. Input And Notation

Metrics uses repaired text in `*_tilde.txt` format.

Main symbols in input:
- `.` and `-`: syllable separators
- `+`: linker between words (no pause)
- `~`: repair/accent marker

Main symbols in output formulas:
- `N_x`: count of item `x`
- `mu`: mora unit
- `mean(x)`: arithmetic mean
- `sd(x)`: standard deviation

## 2. Mora Rules Used By Metrics

Base duration model:
- short vowel (`a e i u`) = `1 mu`
- long/circumflex vowel (`a- e- i- u-` macron/circumflex) = `2 mu`
- repaired extra-long vowel = `3 mu`
- coda consonant contributes consonantal weight in interval computation

These mora assignments are the basis for syllable weight, interval distances, and all derived timing estimates.

## 3. Metric-By-Metric Reference

### 3.1 Total Syllables

What it designates:
- Number of syllables in the analyzed text.

How computed:
- Tokenize syllables from repaired stream and count all syllable nuclei.

Unit:
- `syllables`

### 3.2 Syllable Type Counts (`CV`, `CVC`, `CVV`, ...)

What it designates:
- Structural distribution of syllables.

How computed:
- Each syllable is classified by consonant/vowel pattern.
- Repaired patterns are reported separately (examples: `CVC:`, `CVV:`, `C:V`, `ʔ:V`).

Unit:
- Count: `syllables`
- Share: `%`

### 3.3 Mean Morae Per Syllable

What it designates:
- Mean syllable weight across all syllables.

How computed:
- For each syllable `s`, compute `morae(s)`.
- `mean_morae_per_syllable = mean(morae(s))`.

Unit:
- `mora/syllable`

### 3.4 SD Morae Per Syllable

What it designates:
- Dispersion of syllable weight around the mean.

How computed:
- `sd_morae_per_syllable = sd(morae(s))`.

Unit:
- `mora/syllable`

### 3.5 Total Words

What it designates:
- Number of lexical words after parsing word boundaries.

How computed:
- Count word tokens in analyzed text.

Unit:
- `words`

### 3.6 Mean Syllables Per Word

What it designates:
- Mean word length in syllables.

How computed:
- For each word `w`, let `syll_count(w)` be its syllable count.
- `mean_syllables_per_word = mean(syll_count(w))`.

Unit:
- `syllable/word`

### 3.7 SD Syllables Per Word

What it designates:
- Variability of word length in syllables.

How computed:
- `sd_syllables_per_word = sd(syll_count(w))`.

Unit:
- `syllable/word`

### 3.8 Mean Morae Per Word

What it designates:
- Mean moraic load per word.

How computed:
- For each word `w`, compute `morae(w)`.
- `mean_morae_per_word = mean(morae(w))`.

Unit:
- `mora/word`

### 3.9 SD Morae Per Word

What it designates:
- Dispersion of moraic load across words.

How computed:
- `sd_morae_per_word = sd(morae(w))`.

Unit:
- `mora/word`

### 3.10 Merged Words

What it designates:
- Number of words that participate in merged prosodic units.

How computed:
- Count words inside units linked by merge markers from repair stage.

Unit:
- `words`

### 3.11 Merged Units

What it designates:
- Number of multi-word prosodic units produced by merging.

How computed:
- Count each merged group as one unit.

Unit:
- `units`

### 3.12 Mean Merged Unit Size

What it designates:
- Mean number of words per merged unit.

How computed:
- `mean_merged_unit_size = merged_words / merged_units` (if `merged_units > 0`).

Unit:
- `words`

### 3.13 Repair Rate

What it designates:
- Fraction of syllables modified by repair operations.

How computed:
- `repair_rate = repaired_syllables / total_syllables * 100`.

Unit:
- `%`

### 3.14 %V (Two Values)

What it designates:
- Proportion of vocalic duration proxy in the moraic stream.

How computed:
- Articulate (no pauses): `percent_v_articulate = vowel_morae / total_morae * 100`.
- Normal speech (including pauses): `percent_v_speech = percent_v_articulate / (1 + pause_ratio/100)`.

Rationale:
- Acoustic %V from real speech includes pause time in the denominator.
- To compare moraic text metrics with speech metrics, pause ratio expands total moraic time by `x(1 + pause_ratio/100)`.

Implementation note:
- `metricser.py` and `fullreparer.py` table/CSV outputs expose both values as separate fields.

Unit:
- `%`

### 3.15 DeltaC

What it designates:
- Absolute variability of consonant-to-consonant interval length.

How computed:
- Build sequence of consonant intervals measured in mora distance.
- `DeltaC = sd(consonant_intervals)`.

Unit:
- `mora`

### 3.16 MeanC

What it designates:
- Mean consonant interval length.

How computed:
- `MeanC = mean(consonant_intervals)`.

Unit:
- `mora`

### 3.17 VarcoC

What it designates:
- Tempo-normalized variability of consonant intervals.

How computed:
- `VarcoC = 100 * DeltaC / MeanC`.

Unit:
- `%`

### 3.17.1 How `consonant_intervals` Is Computed (Detailed)

What this sequence designates:
- `consonant_intervals` is the ordered list of vowel-mora distances attached to each consonant position in the preprocessed stream.
- This list is the direct input for `DeltaC` and `MeanC`.

Step-by-step algorithm in `metrics.py`:
1. Preprocess text (`preprocess_text`) and insert word boundaries (`$`) only at punctuation boundaries.
2. Keep connected speech across spaces and `+` linkers: they do not create `$`.
3. Remove boundary/separator symbols (`$`, `.`, `-`, `+`) and keep only phonetic segments.
4. Build two parallel arrays with `extract_segments(...)`:
- `consonants`: every consonant encountered in order.
- `vowels_after[i]`: contiguous vowel/length-marker string immediately following consonant `consonants[i]`.
5. Convert each `vowels_after[i]` to mora distance with `vowel_length(...)`:
- short vowel = `1`
- long/circumflex vowel = `2`
- extra-long repaired vowel = `3`
- explicit length marker `:` contributes `+1`
6. Build `consonant_intervals` with `compute_consonant_distances(...)`:
- for each consonant except last: append `vowel_length(vowels_after[i])`
- append trailing value for last consonant as well

Important consequences:
- Number of intervals equals number of consonants (not consonant-pairs).
- Consonant clusters create `0` intervals where no vowel follows a consonant.
- Final consonants can contribute terminal `0`.
- Spaces and `+` linkers do not break interval continuity.
- `$` markers come from punctuation boundaries only, and are removed before interval distance is computed.

Core interpretation rule:
- If two consonants are separated by a vowel, the interval distance is the vowel mora count: `1`, `2`, or `3` (short, long, repaired extra-long).
- If two consonants are adjacent in a cluster, interval distance is `0`.

Gemination clarification:
- In `s-t`, distance `s -> t` is `0` if no vowel material appears between them.
- In plain doubled writing `s-s` (two consonant tokens), distance between the two `s` values is computed the same way as any adjacent consonant pair.
- In repaired `s:t` (length marker attached to first `s`), consonant count is not incremented by introducing a new consonant token.
- `s:t` is interpreted as consonant `s` followed by vowel/length material `:` before the next consonant (for example `t`), so distance `s -> t = 1`.

Worked examples:

Example A: simple open syllables
- Input idea: `ba na`
- After preprocessing (conceptually): `bana`
- Segments: consonants = `[b, n]`, vowels_after = `[a, a]`
- Distances: `[1, 1]`
- Result: `MeanC = 1.0`, `DeltaC = 0.0`

Example B: long vowel affects one interval
- Input idea: `ba na` with first vowel long (`ba-`)
- Segments: consonants = `[b, n]`, vowels_after = `[a-, a]`
- Distances: `[2, 1]`
- Effect: interval variability increases because one consonant carries a longer vowel interval.

Example B2: punctuation inserts boundary but not distance
- Input idea: `ba, na`
- After preprocessing (conceptually): `ba$na`
- `$` is removed before interval extraction, so distance logic remains vowel-based (`[1, 1]`).

Example C: initial vowel word and terminal consonant
- Input idea: `ab`
- Processing adds initial glottal for vowel-initial words.
- Segments: consonants = `[GLOTTAL, b]`, vowels_after = `[a, ""]`
- Distances: `[1, 0]`
- Interpretation: last consonant has no following vowel material, so terminal interval is `0`.

Example D: consonant cluster produces zero interval
- Input idea: `abdu`
- Segments: consonants = `[GLOTTAL, b, d]`, vowels_after = `[a, "", u]`
- Distances: `[1, 0, 1]`
- Interpretation: `b` is followed directly by consonant `d`, so its vowel interval is zero.

Example E: repaired length marker contributes mora
- Input idea with repaired consonant length marker after vowel sequence
- If `vowels_after[i]` is `a:` then `vowel_length("a:") = 1 + 1 = 2`
- This increases the corresponding interval even when no extra vowel letter appears.

Example F: cluster vs repaired gemination (`s-t` vs `s:t`)
- `s-t`: no vowel/length between `s` and `t` -> distance `0`.
- `s:t`: `:` contributes `1` mora between `s` and `t` -> distance `1`.
- Consonant tokens remain the same base sequence (`s`, `t`); the change is in interval weight, not extra consonant count.

### 3.18 Speech Rate (`SPS`)

What it designates:
- Predicted syllables per second under chosen `wpm` and `pause_ratio`.

How computed:
- `SPS_speech = (WPM / 60) * mean_syllables_per_word`

Unit:
- `syllable/s`

### 3.19 Articulation Rate (`SPS` Without Pauses)

What it designates:
- Predicted articulation-only rate (excluding pause time share).

How computed:
- `SPS_articulation = SPS_speech / (1 - pause_ratio/100)`

Unit:
- `syllable/s`

### 3.20 Mean Syllable Duration

What it designates:
- Mean time assigned to one articulated syllable.

How computed:
- `mean_syllable_duration = 1 / SPS_articulation`

Unit:
- `s/syllable`

### 3.21 Mora Duration

What it designates:
- Mean time assigned to one mora in the model.

How computed:
- `mora_dur = mean_syllable_duration / mean_morae_per_syllable`

Unit:
- `s/mora`

### 3.22 Word Duration

What it designates:
- Mean time per word at selected `WPM`.

How computed:
- `word_dur = 60 / WPM`

Unit:
- `s/word`

### 3.23 Short Pause Punctuation Per Syllable

What it designates:
- Density of short-pause punctuation events relative to syllable count.

How computed:
- Count punctuation in `SHORT_PAUSE_PUNCTUATION_CHARS`.
- `short_pause_per_syll = N_short_pause / total_syllables`

Unit:
- `pause/syllable`

### 3.24 Long Pause Punctuation Per Syllable

What it designates:
- Density of long-pause punctuation events relative to syllable count.

How computed:
- Count punctuation in `LONG_PAUSE_PUNCTUATION_CHARS`.
- Include newline boundaries when enabled.
- Include final EOF boundary when enabled and final character is word-final.
- `long_pause_per_syll = N_long_pause / total_syllables`

Unit:
- `pause/syllable`

### 3.25 Total Punctuation Pauses Per Syllable

What it designates:
- Combined punctuation pause density.

How computed:
- `total_pause_per_syll = short_pause_per_syll + long_pause_per_syll`

Unit:
- `pause/syllable`

### 3.26 Total Boundaries

What it designates:
- Number of detected boundary positions in text stream.

How computed:
- Count boundaries from parser boundary scan.

Unit:
- `boundaries`

### 3.27 Pauseable Boundaries

What it designates:
- Number of boundaries eligible for punctuation pause treatment.

How computed:
- Subset count of total boundaries that satisfy pauseability conditions.

Unit:
- `boundaries`

### 3.28 Total Pause Time Per Syllable

What it designates:
- Pause-time budget allocated per syllable from configured `pause_ratio`.

How computed:
- Derived from speech/articulation timing model and pause ratio.

Unit:
- `s/syllable`

### 3.29 Short Pause Punctuation Duration

What it designates:
- Duration assigned to one short-pause event.

How computed:
- `W_short = 1.0` (fixed)
- `W_long = long_punct_weight` (parameter)
- `units = short_pause_per_syll * W_short + long_pause_per_syll * W_long`
- `unit_dur = total_pause_time_per_syll / units`
- `short_pause_dur = unit_dur * W_short`

Unit:
- `s/pause`

### 3.30 Long Pause Punctuation Duration

What it designates:
- Duration assigned to one long-pause event.

How computed:
- `long_pause_dur = unit_dur * W_long`

Unit:
- `s/pause`

### 3.31 Short Pause Duration In Mean-Syllable Units

What it designates:
- Relative size of a short pause compared to one mean syllable.

How computed:
- `short_ratio = short_pause_dur / mean_syllable_duration`

Unit:
- `mean syllable duration` (dimensionless ratio)

### 3.32 Long Pause Duration In Mean-Syllable Units

What it designates:
- Relative size of a long pause compared to one mean syllable.

How computed:
- `long_ratio = long_pause_dur / mean_syllable_duration`

Unit:
- `mean syllable duration` (dimensionless ratio)

### 3.33 Pause Time Share By Class

What it designates:
- How total pause budget is split between short and long classes.

How computed:
- `short_share = (short_pause_per_syll * short_pause_dur) / total_pause_time_per_syll * 100`
- `long_share = (long_pause_per_syll * long_pause_dur) / total_pause_time_per_syll * 100`

Unit:
- `% of pause time`

## 4. Pause Classification Rules

Rules used by implementation:
- Spaces are not pauses.
- `+` linkers are not pauses.
- Short and long punctuation classes are constant sets defined in `metrics.py`.
- Short class weight is always fixed: `SHORT_PAUSE_PUNCT_WEIGHT = 1.0`.
- Long class weight is configurable with `--long-punct-weight`.
- EOF is treated as line-end long pause when enabled.

Exact punctuation classes:
- Short pause punctuation characters: `,`, `:`, `;`, `|`, `…`
- Short pause multi-character patterns: `...`, `…`
- Long pause punctuation characters: `.`, `?`, `!`
- Newline can trigger long pause when `LONG_PAUSE_INCLUDES_NEWLINE = True`.
- Final EOF can trigger long pause when `LONG_PAUSE_INCLUDES_FINAL_EOF = True`.

## 5. Precision Policy

Internal computation:
- Full floating-point precision.

Display:
- Time values are printed at millisecond-scale precision.
- Ratios and percentages use fixed display precision.

Audit rule:
- Displayed pause/syllable ratios are computed from displayed rounded values so manual checks match the visible table.

## 6. Run Configuration In Output

Each report includes effective parameters (run context), including:
- input path
- `wpm`
- `pause_ratio`
- `long_punct_weight`
- extra phonetic inventory overrides

This makes each metrics file self-describing and reproducible.

## 7. CLI Parameters Used For Metrics

`metricser.py`:
- `--wpm`
- `--pause-ratio`
- `--long-punct-weight`
- `--table`, `--json`, `--csv`
- `--extra-consonants`, `--extra-vowels`

`fullreparer.py` (metrics stage):
- `--metrics-wpm`
- `--metrics-pause-ratio`
- `--metrics-long-punct-weight`
- `--metrics-table`, `--metrics-json`, `--metrics-csv`

## 8. Versioning

If formulas, constants, or pause classification rules change in `metrics.py`, update this document in the same commit.
