# Metrics Computation

The active metrics model is interval-based and phone-driven. Metricalc reads the
paired phonetizer artifacts, converts their realized row durations into rhythm
intervals, and reports both rhythmic and structural summaries.

Implementation scope:
- `src/akkapros/lib/metrics.py`
- `src/akkapros/cli/metricalc.py`
- `src/akkapros/cli/fullprosmaker.py`

## What the Metrics Stage Measures

The metrics stage answers two related questions.

First, it asks how time is distributed across vocalic, consonantal, and pause
intervals in the paired original and accentuated streams.

Second, it keeps the wider structural inventory needed for research reporting:
counts of syllables, morae, merges, accentuation, prominence, pauses, and drift.

Because the metrics stage now reads the phonetizer's realized phone rows, the
reported values describe the toolkit's actual phonetic timing model rather than
an approximation reconstructed from `_tilde.txt`.

## Inputs

Metricalc consumes paired phonetizer artifacts:

- original stream: `<prefix>_ophone.txt`
- accentuated stream: `<prefix>_phone.txt`

MBROLA `.pho` files are not metrics inputs, and `_tilde.txt` is no longer the
active metrics input contract.

## Interval Normalization

Each phone row is mapped to one of three interval classes:

- `V` for rows with `category=V`
- `C` for rows with `category=C`
- `P` for rows with `category=S`

Hiatus rows and vowel-transition rows remain consonantal because the phonetizer
serializes them as consonant-category rows.

After normalization, metricalc merges adjacent rows of the same class and sums
their durations. The goal is not to count letters or phones one by one, but to
measure stretches of vocalic time, consonantal time, and pause time.

Example:

```python
[("V", 100), ("C", 120), ("P", 100), ("C", 45), ("V", 245)]
```

## Rhythm Formulas

Let `V` be the vocalic interval durations, `C` the consonantal interval
durations, and `P` the pause durations. Let
`Total = sum(V) + sum(C) + sum(P)`.

Active metrics:

- `%V = (sum(V) / Total) * 100`
- `%C = (sum(C) / Total) * 100`
- `meanV = arithmetic_mean(V)`
- `meanC = arithmetic_mean(C)`
- `ΔV = population_standard_deviation(V)`
- `ΔC = population_standard_deviation(C)`
- `VarcoV = (ΔV / meanV) * 100`
- `VarcoC = (ΔC / meanC) * 100`
- `rPVI-C = mean(abs(C[k] - C[k+1]))`
- `nPVI-V = 100 * mean(abs((V[k] - V[k+1]) / ((V[k] + V[k+1]) / 2)))`

Pause treatment:

- pauses remain in the denominator for `%V` and `%C`
- pauses are excluded from `mean`, `Δ`, `Varco`, and PVI metrics

Fallback rules:

- no intervals for a class -> that class reports `0`
- fewer than two intervals -> `Δ` and the PVI metric report `0`

## What the Main Metrics Mean

`%V` and `%C`
: These describe how much of the total elapsed time is occupied by vocalic and
	consonantal intervals. Because pauses stay in the denominator, neither metric
	alone exhausts 100 percent unless pause time is zero.

`meanV` and `meanC`
: These describe the average size of vocalic and consonantal intervals in
	milliseconds. They are useful as baseline size measures before variability is
	considered.

`ΔV` and `ΔC`
: These describe raw variability inside the vocalic and consonantal interval
	classes. Higher values mean intervals differ more strongly in absolute size.

`VarcoV` and `VarcoC`
: These normalize variability against average interval size. They are useful
	when comparing texts or streams with different average interval durations.

`rPVI-C`
: This measures how strongly adjacent consonantal intervals fluctuate from one
	to the next in absolute terms.

`nPVI-V`
: This measures how strongly adjacent vocalic intervals fluctuate from one to
	the next after normalization by local average size.

## Interpretation Limits

These metrics are descriptive summaries of the realized phone-row timing model.
They do not by themselves prove a complete historical phonology, and they do
not replace philological judgment.

In particular:

- they describe the current encoded realization, not recorded ancient speech
- they are sensitive to the phonetizer's duration model and pause handling
- they are best interpreted comparatively across streams, texts, or parameter
	settings rather than as isolated numbers without context

The most informative comparison in normal use is the paired one already exposed
by the toolkit: original `_ophone.txt` versus accentuated `_phone.txt`.

## Structural Statistics

The metrics output still includes the broader structural inventory, derived from
the paired phone artifacts:

- syllable totals and syllable-type ratios
- word and mora statistics
- merge statistics
- accentuation statistics
- prominence statistics
- pause and speech-rate summaries

Prominence statistics are derived from phone structure:

- `function_word_count` is computed from the reconstructed lexical stream
- `explicit_word_link_count` is computed from `boundary=X` rows

## Drift Reporting

Metricalc consumes the phonetizer drift summary directly from front matter:

- `metadata.data.phonetize.drift.max`
- `metadata.data.phonetize.drift.mean`
- `metadata.data.phonetize.drift.stddev`

Those values are reported for both original and accentuated streams in table
and JSON outputs.

## Reading the Outputs

`<prefix>_metrics.txt`
: Human-readable report for inspection, review, and publication drafting.

`<prefix>_metrics.json`
: Structured report for comparisons, scripting, or downstream visualization.

In both formats, the most important first comparison is usually this one:

- original stream: what the deaccented phone realization looks like
- accentuated stream: what changes once the prosody-driven realization is added
