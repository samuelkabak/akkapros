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
  the active phone/ophone metrics contract

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

This page records one fixed sample configuration. It is not a statement of all
current package defaults outside this worked verification example.

### Policy settings

- `geminate_policy = corrective`
- `accentuation_distribution_policy = 80_20`
- `drift_tolerance = 12`

Note: `short_pause_policy` and `drift_policy` are no longer part of the public
config surface; behavior for both is now fixed internally.

### Speech-level settings

The phonetizer still owns speech-model settings upstream, but the metrics stage
now reports `WPM` and `Pause ratio` from realized phone-row durations rather
than from copied metrics-side defaults.

### Core duration anchors

- `segmental_ceiling = 310`
- `segmental_floor = 10`
- `cvc_reference = 300`

### Consonant timings

Closure class:

- `closure.onset = 89`
- `closure.coda = 87`
- `closure.coda_final = 87`
- `closure.geminate = 175`
- `closure.special_realization.hiatus = 35`
- `closure.perception_limits.geminate_min = 145`
- `closure.perception_limits.gemination_max = 260`

Fricative class:

- `fricative.onset = 115`
- `fricative.coda = 112`
- `fricative.coda_final = 112`
- `fricative.geminate = 210`
- `fricative.perception_limits.geminate_min = 163`
- `fricative.perception_limits.gemination_max = 290`

Sonorant class:

- `sonorant.onset = 105`
- `sonorant.coda = 100`
- `sonorant.coda_final = 100`
- `sonorant.geminate = 190`
- `sonorant.special_realization.vowel_transition = 25`
- `sonorant.perception_limits.geminate_min = 148`
- `sonorant.perception_limits.gemination_max = 275`

### Vowel timings

- `vowels.short = 110`
- `vowels.short_final = 110`
- `vowels.long = 160`
- `vowels.long_final = 160`
- `vowels.very_long = 260`
- `vowels.perception_limits.short_min = 60`
- `vowels.perception_limits.long_min = 153`
- `vowels.perception_limits.very_long_min = 233`
- `vowels.perception_limits.elongation_max = 280`

### Pause bands

Short pause band:

- `pauses.short.min = 520`
- `pauses.short.max = 680`

Long pause band:

- `pauses.long.min = 1100`
- `pauses.long.max = 1780`

### Drift summary carried by the phonetizer

For this sample under the current approved defaults, the phonetizer reports:

- original stream: `Unit drift max = 150.0 ms`, `Unit drift mean = 32.4167 ms`, `Unit drift stddev = 49.3203 ms`
- accentuated stream: `Unit drift max = 189.0 ms`, `Unit drift mean = 28.1739 ms`, `Unit drift stddev = 63.0787 ms`

Under the active contract, metricalc surfaces these drift values from the
phone/ophone metadata rather than recomputing them from interval arithmetic.

## Metric Formulas

The active formulas are the interval formulas used by the current metrics
pipeline.

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

- `V = [110, 110, 110, 110, 110, 110, 110, 110, 153, 185, 110, 110, 185, 110, 110, 110, 153, 110, 232, 110]`
- `C = [115, 115, 115, 201, 105, 100, 35, 105, 105, 89, 115, 89, 189, 217, 35, 105, 35, 105, 35, 175, 115]`
- `P = [150, 199, 533, 1460]`

Accentuated stream (`_phone.txt`):

- `V = [110, 110, 127, 110, 110, 110, 110, 110, 169, 185, 110, 110, 185, 110, 110, 110, 269, 110, 280, 110]`
- `C = [115, 115, 115, 297, 105, 135, 105, 105, 92, 115, 89, 189, 217, 35, 105, 35, 126, 35, 231, 115]`
- `P = [150, 600, 1519]`

## Manual Computation

Applying the public formulas above to those interval lists yields the following
results for the current approved timing profile.

Original stream:

- `|V| = 20`, `|C| = 21`, `|P| = 4`
- `sum(V) = 2558 ms`, `sum(C) = 2300 ms`, `sum(P) = 2342 ms`, `Total = 7200 ms`
- `%C = 31.944444444444443`
- `%V = 35.52777777777778`
- `meanC = 109.52380952380952 ms`
- `meanV = 127.9 ms`
- `ΔC = 50.67320043800653 ms`
- `ΔV = 34.222653316188094 ms`
- `VarcoC = 46.26683518252771`
- `VarcoV = 26.75735208458803`
- `rPVI-C = 59.0`
- `nPVI-V = 21.698221153635842`
- `Unit drift max = 150.0 ms`, `Unit drift mean = 32.4167 ms`, `Unit drift stddev = 49.3203 ms`

Accentuated stream:

- `|V| = 20`, `|C| = 20`, `|P| = 3`
- `sum(V) = 2755 ms`, `sum(C) = 2476 ms`, `sum(P) = 2269 ms`, `Total = 7500 ms`
- `%C = 33.013333333333335`
- `%V = 36.733333333333334`
- `meanC = 123.8 ms`
- `meanV = 137.75 ms`
- `ΔC = 64.1237865382262 ms`
- `ΔV = 51.86508941474988 ms`
- `VarcoC = 51.796273455756214`
- `VarcoV = 37.651607560616974`
- `rPVI-C = 75.78947368421052`
- `nPVI-V = 30.249305872660635`
- `Unit drift max = 189.0 ms`, `Unit drift mean = 28.1739 ms`, `Unit drift stddev = 63.0787 ms`

## Raw Program Response

The block below is the current program response for the same sample.

```text
Acoustic metrics (original):
  %C: 31.94%
  %V: 35.53%
  meanC: 109.52 ms
  meanV: 127.90 ms
  ΔC: 50.67 ms
  ΔV: 34.22 ms
  VarcoC: 46.27
  VarcoV: 26.76
  rPVI-C: 59.00
  nPVI-V: 21.70
  Unit drift max: 150.00 ms
  Unit drift mean: 32.42 ms
  Unit drift stddev: 49.32 ms

Acoustic metrics (accentuated):
  %C: 33.01%
  %V: 36.73%
  meanC: 123.80 ms
  meanV: 137.75 ms
  ΔC: 64.12 ms
  ΔV: 51.87 ms
  VarcoC: 51.80
  VarcoV: 37.65
  rPVI-C: 75.79
  nPVI-V: 30.25
  Unit drift max: 189.00 ms
  Unit drift mean: 28.17 ms
  Unit drift stddev: 63.08 ms
```

## Equality Check

The manual computation and the program response are equal for every published
indicator in this sample.

Original stream:

| Indicator | Manual result | Program result |
| --- | ---: | ---: |
| %C | 31.944444444444443 | 31.944444444444443 |
| %V | 35.52777777777778 | 35.52777777777778 |
| meanC | 109.52380952380952 | 109.52380952380952 |
| meanV | 127.9 | 127.9 |
| ΔC | 50.67320043800653 | 50.67320043800653 |
| ΔV | 34.222653316188094 | 34.222653316188094 |
| VarcoC | 46.26683518252771 | 46.26683518252771 |
| VarcoV | 26.75735208458803 | 26.75735208458803 |
| rPVI-C | 59.0 | 59.0 |
| nPVI-V | 21.698221153635842 | 21.698221153635842 |
| Unit drift max | 150.0 | 150.0 |
| Unit drift mean | 32.4167 | 32.4167 |
| Unit drift stddev | 49.3203 | 49.3203 |

Accentuated stream:

| Indicator | Manual result | Program result |
| --- | ---: | ---: |
| %C | 33.013333333333335 | 33.013333333333335 |
| %V | 36.733333333333334 | 36.733333333333334 |
| meanC | 123.8 | 123.8 |
| meanV | 137.75 | 137.75 |
| ΔC | 64.1237865382262 | 64.1237865382262 |
| ΔV | 51.86508941474988 | 51.86508941474988 |
| VarcoC | 51.796273455756214 | 51.796273455756214 |
| VarcoV | 37.651607560616974 | 37.651607560616974 |
| rPVI-C | 75.78947368421052 | 75.78947368421052 |
| nPVI-V | 30.249305872660635 | 30.249305872660635 |
| Unit drift max | 189.0 | 189.0 |
| Unit drift mean | 28.1739 | 28.1739 |
| Unit drift stddev | 63.0787 | 63.0787 |
