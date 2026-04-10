# Metrics Computation

The active metrics model is interval-based and phone-driven.

Implementation scope:
- `src/akkapros/lib/metrics.py`
- `src/akkapros/cli/metricalc.py`
- `src/akkapros/cli/fullprosmaker.py`

## Inputs

Metricalc consumes paired phonetizer artifacts:

- original stream: `<prefix>_ophone.txt`
- accentuated stream: `<prefix>_phone.txt`

MBROLA `.pho` files are not metrics inputs.

## Interval Normalization

Each phone row is mapped to one of three interval classes:

- `V` for rows with `category=V`
- `C` for rows with `category=C`
- `P` for rows with `category=S`

Hiatus rows and vowel-transition rows remain consonantal because they are
serialized as consonant-category rows.

After normalization, metricalc merges adjacent rows of the same class and sums
their durations.

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

## Structural Statistics

The metrics output still includes the broader structural inventory, derived from
the paired phone artifacts:

- syllable totals and syllable-type ratios
- word and mora statistics
- merge statistics
- accentuation statistics
- prominence statistics

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
