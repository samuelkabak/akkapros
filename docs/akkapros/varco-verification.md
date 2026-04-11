# Varco Verification

This page is a worked verification example for the active metrics pipeline.
It does not describe the implementation in general terms. It does two concrete
things for one fixed Akkadian line:

1. computes every public indicator manually from the stated formulas, interval
  lists, and timing assumptions
2. places those manual results beside the raw program response and checks that
  the values are equal

## Sample

Input line:

```text
šazu šuḫgurim ina rebî : šākin tašmê ana ilī abbīšu
```

Pipeline assumptions used for this verification:

- syllabification preserves source line structure
- prosody style is `lob`
- prosody mora mode is `bi`
- explicit `+` propagation remains at the default `only-last` behavior
- metrics are computed from paired `_ophone.txt` and `_phone.txt` streams under
  the active phone/ophone contract from REQ-030

Observed current intermediate forms:

- Syllabified:

```text
ša·zu¦šuḫ·gu·rim¦˙i·na¦re·bî¦⟦ : ⟧šā·kin¦taš·mê¦˙a·na¦˙i·lī¦˙ab·bī·šu¦
```

- Prosody-realized (`_tilde`) form:

```text
ša·zu šuḫ~·gu·rim ˙i·na&re·bî~⟦ : ⟧šā·kin taš·mê ˙a·na&˙i·lī~ ˙ab·bī~·šu
```

## Timing Parameters

The following effective phonetizer timing parameters are the ones used for this
verification sample. They must be stated explicitly so the computation can be
reproduced without relying on hidden defaults.

### Policy settings

- `geminate_policy = corrective`
- `accentuation_distribution_policy = 85_15`
- `short_pause_policy = strict`
- `drift_policy = extensible`
- `drift_tolerance = 12`

### Speech-level settings

- `wpm = 193`
- `pause_ratio = 35`

`wpm` and `pause_ratio` affect speech-rate and pause reporting surfaces. The
interval metrics below are computed from emitted phone durations, but these
settings are still part of the effective runtime context used to produce those
durations.

### Core duration anchors

- `segmental_ceiling = 310`
- `cvc_reference = 305`

### Consonant timings

Closure class:

- `closure.onset = 108`
- `closure.coda = 103`
- `closure.geminate = 195`
- `closure.special_realization.hiatus = 18`
- `closure.perception_limits.geminate_min = 180`

Fricative class:

- `fricative.onset = 137`
- `fricative.coda = 142`
- `fricative.geminate = 279`
- `fricative.perception_limits.geminate_min = 152`

Sonorant class:

- `sonorant.onset = 89`
- `sonorant.coda = 70`
- `sonorant.geminate = 163`
- `sonorant.special_realization.vowel_transition = 11`
- `sonorant.perception_limits.geminate_min = 152`

### Vowel timings

- `vowels.short = 85`
- `vowels.long = 160`
- `vowels.very_long = 220`
- `vowels.perception_limits.short_min = 40`
- `vowels.perception_limits.long_min = 123`
- `vowels.perception_limits.very_long_min = 190`
- `vowels.perception_limits.max = 240`

### Pause bands

Short pause band:

- `pauses.short.min = 600`
- `pauses.short.max = 680`

Long pause band:

- `pauses.long.min = 1200`
- `pauses.long.max = 1780`

### Drift summary carried by the phonetizer

For this sample, the phonetizer reports:

- `Drift max = 65.0 ms`
- `Drift mean = -3.3182 ms`
- `Drift stddev = 18.3536 ms`

Under the active contract, metricalc surfaces these drift values from the
phone/ophone metadata rather than recomputing them from interval arithmetic.

## Metric Formulas

The active formulas are the interval formulas defined by REQ-030.

Let `V` be the list of vocalic interval durations, `C` the list of consonantal
interval durations, `P` the pause intervals, and `Total = sum(V) + sum(C) +
sum(P)`.

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

Pause intervals remain in the denominator for `%V` and `%C`, but are excluded
from `mean`, `Δ`, `Varco`, and PVI calculations.

## Interval Lists

Original stream (`_ophone.txt`):

- `V = [56, 44, 85, 54, 85, 54, 44, 44, 173, 185, 94, 94, 197, 68, 44, 44, 173, 94, 213, 68]`
- `C = [137, 137, 137, 250, 89, 88, 89, 89, 108, 137, 108, 178, 231, 18, 89, 18, 89, 18, 195, 137]`
- `P = [622, 1513]`

Accentuated stream (`_phone.txt`):

- `V = [56, 44, 108, 54, 85, 54, 44, 44, 240, 185, 94, 94, 197, 68, 44, 44, 240, 107, 240, 98]`
- `C = [137, 137, 137, 380, 89, 88, 89, 89, 180, 137, 108, 178, 231, 18, 89, 18, 162, 18, 267, 137]`
- `P = [635, 1537]`

## Manual Computation

The arithmetic below starts from the interval lists above. Those interval lists
are the durations emitted under the stated timing parameters. The computation of
the indicators then uses only the public formulas from REQ-030.

### Original Stream: Worked Derivation

Counts and totals:

- `|V| = 20`
- `|C| = 20`
- `|P| = 2`
- `sum(V) = 1913 ms`
- `sum(C) = 2342 ms`
- `sum(P) = 2135 ms`
- `Total = 1913 + 2342 + 2135 = 6390 ms`

Step-by-step indicator calculations:

- `%C = (sum(C) / Total) * 100 = (2342 / 6390) * 100 = 36.6510172143975`
- `%V = (sum(V) / Total) * 100 = (1913 / 6390) * 100 = 29.9374021909233`
- `meanC = sum(C) / |C| = 2342 / 20 = 117.10 ms`
- `meanV = sum(V) / |V| = 1913 / 20 = 95.65 ms`
- `ΔC = sqrt(sum((c_i - meanC)^2) / |C|)`
  with `sum((c_i - meanC)^2) = 76815.8`, so
  `ΔC = sqrt(76815.8 / 20) = 61.9741074965989 ms`
- `ΔV = sqrt(sum((v_i - meanV)^2) / |V|)`
  with `sum((v_i - meanV)^2) = 64136.55`, so
  `ΔV = sqrt(64136.55 / 20) = 56.6288574845017 ms`
- `VarcoC = (ΔC / meanC) * 100 = (61.9741074965989 / 117.10) * 100 = 52.9240883830905`
- `VarcoV = (ΔV / meanV) * 100 = (56.6288574845017 / 95.65) * 100 = 59.2042420120247`
- `rPVI-C = mean(abs(C[k] - C[k+1]))`
  with adjacent absolute differences
  `[0, 0, 113, 161, 1, 1, 0, 19, 29, 29, 70, 53, 213, 71, 71, 71, 71, 177, 58]`
  and total difference sum `1208`, so
  `rPVI-C = 1208 / 19 = 63.5789473684211`
- `nPVI-V = 100 * mean(abs((V[k] - V[k+1]) / ((V[k] + V[k+1]) / 2)))`
  with normalized adjacent terms
  `[0.24, 0.635658914729, 0.446043165468, 0.446043165468, 0.446043165468, 0.204081632653, 0.0, 1.188940092166, 0.067039106145, 0.652329749104, 0.0, 0.707903780069, 0.97358490566, 0.428571428571, 0.0, 1.188940092166, 0.591760299625, 0.775244299674, 1.032028469751]`
  whose sum is `10.024212266716772`, so
  `nPVI-V = 100 * (10.024212266716772 / 19) = 52.7590119300883`

Manual drift summary:

- drift history:
  `[12, 12, 3, 12, 3, 12, 12, 12, -12, 0, -12, -12, -12, -12, 12, 12, 12, -12, -12, -12, 12, 0]`
- `Drift max = max(abs(history)) = 12.0 ms`
- `Drift mean = sum(history) / 22 = 30 / 22 = 1.36363636363636 ms`
- `Drift stddev = sqrt(sum((d_i - mean)^2) / 22)`
  with `sum((d_i - mean)^2) = 2569.090909090909`, so
  `Drift stddev = sqrt(2569.090909090909 / 22) = 10.8063 ms`

### Accentuated Stream: Worked Derivation

Counts and totals:

- `|V| = 20`
- `|C| = 20`
- `|P| = 2`
- `sum(V) = 2140 ms`
- `sum(C) = 2689 ms`
- `sum(P) = 2172 ms`
- `Total = 2140 + 2689 + 2172 = 7001 ms`

Step-by-step indicator calculations:

- `%C = (sum(C) / Total) * 100 = (2689 / 7001) * 100 = 38.4087987430367`
- `%V = (sum(V) / Total) * 100 = (2140 / 7001) * 100 = 30.5670618483074`
- `meanC = sum(C) / |C| = 2689 / 20 = 134.45 ms`
- `meanV = sum(V) / |V| = 2140 / 20 = 107.00 ms`
- `ΔC = sqrt(sum((c_i - meanC)^2) / |C|)`
  with `sum((c_i - meanC)^2) = 143750.95`, so
  `ΔC = sqrt(143750.95 / 20) = 84.7794049283197 ms`
- `ΔV = sqrt(sum((v_i - meanV)^2) / |V|)`
  with `sum((v_i - meanV)^2) = 97740.0`, so
  `ΔV = sqrt(97740.0 / 20) = 69.9070811863863 ms`
- `VarcoC = (ΔC / meanC) * 100 = (84.7794049283197 / 134.45) * 100 = 63.0564558782594`
- `VarcoV = (ΔV / meanV) * 100 = (69.9070811863863 / 107.00) * 100 = 65.3337207349404`
- `rPVI-C = mean(abs(C[k] - C[k+1]))`
  with adjacent absolute differences
  `[0, 0, 243, 291, 1, 1, 0, 91, 43, 29, 70, 53, 213, 71, 71, 144, 144, 249, 130]`
  and total difference sum `1844`, so
  `rPVI-C = 1844 / 19 = 97.0526315789474`
- `nPVI-V = 100 * mean(abs((V[k] - V[k+1]) / ((V[k] + V[k+1]) / 2)))`
  with normalized adjacent terms
  `[0.24, 0.842105263158, 0.666666666667, 0.446043165468, 0.446043165468, 0.204081632653, 0.0, 1.380281690141, 0.258823529412, 0.652329749104, 0.0, 0.707903780069, 0.97358490566, 0.428571428571, 0.0, 1.380281690141, 0.766570605187, 0.766570605187, 0.840236686391]`
  whose sum is `11.00009456327598`, so
  `nPVI-V = 100 * (11.00009456327598 / 19) = 57.8952345435578`

Manual drift summary:

- drift history:
  `[12, 12, 3, 12, 3, 12, 12, 12, -25, 0, -12, -12, -12, -12, 12, 12, 12, -25, -12, -65, -12, 0]`
- `Drift max = max(abs(history)) = 65.0 ms`
- `Drift mean = sum(history) / 22 = -73 / 22 = -3.31818181818182 ms`
- `Drift stddev = sqrt(sum((d_i - mean)^2) / 22)`
  with `sum((d_i - mean)^2) = 7410.772727272727`, so
  `Drift stddev = sqrt(7410.772727272727 / 22) = 18.3536 ms`

## Raw Program Response

The block below is the program response for the same sample. It is given here
without further explanation so it can be compared directly against the manual
derivation above.

```text
Acoustic metrics (original):
  %C: 36.65%
  %V: 29.94%
  meanC: 117.10 ms
  meanV: 95.65 ms
  ΔC: 61.97 ms
  ΔV: 56.63 ms
  VarcoC: 52.92
  VarcoV: 59.20
  rPVI-C: 63.58
  nPVI-V: 52.76
  Drift max: 12.00 ms
  Drift mean: 1.36 ms
  Drift stddev: 10.81 ms

Acoustic metrics (accentuated):
  %C: 38.41%
  %V: 30.57%
  meanC: 134.45 ms
  meanV: 107.00 ms
  ΔC: 84.78 ms
  ΔV: 69.91 ms
  VarcoC: 63.06
  VarcoV: 65.33
  rPVI-C: 97.05
  nPVI-V: 57.90
  Drift max: 65.00 ms
  Drift mean: -3.32 ms
  Drift stddev: 18.35 ms
```

## Equality Check

The manual computation and the program response are equal for every published
indicator in this sample.

Original stream:

| Indicator | Manual result | Program result |
| --- | ---: | ---: |
| %C | 36.6510172143975 | 36.6510172143975 |
| %V | 29.9374021909233 | 29.9374021909233 |
| meanC | 117.10 | 117.10 |
| meanV | 95.65 | 95.65 |
| ΔC | 61.9741074965989 | 61.9741074965989 |
| ΔV | 56.6288574845017 | 56.6288574845017 |
| VarcoC | 52.9240883830905 | 52.9240883830905 |
| VarcoV | 59.2042420120247 | 59.2042420120247 |
| rPVI-C | 63.5789473684211 | 63.5789473684211 |
| nPVI-V | 52.7590119300883 | 52.7590119300883 |
| Drift max | 12.0 | 12.0 |
| Drift mean | 1.3636 | 1.3636 |
| Drift stddev | 10.8063 | 10.8063 |

Accentuated stream:

| Indicator | Manual result | Program result |
| --- | ---: | ---: |
| %C | 38.4087987430367 | 38.4087987430367 |
| %V | 30.5670618483074 | 30.5670618483074 |
| meanC | 134.45 | 134.45 |
| meanV | 107.00 | 107.00 |
| ΔC | 84.7794049283197 | 84.7794049283197 |
| ΔV | 69.9070811863863 | 69.9070811863863 |
| VarcoC | 63.0564558782594 | 63.0564558782594 |
| VarcoV | 65.3337207349404 | 65.3337207349404 |
| rPVI-C | 97.0526315789474 | 97.0526315789474 |
| nPVI-V | 57.8952345435578 | 57.8952345435578 |
| Drift max | 65.0 | 65.0 |
| Drift mean | -3.3182 | -3.3182 |
| Drift stddev | 18.3536 | 18.3536 |
