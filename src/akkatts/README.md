# akkatts (experimental)

`akkatts` is an experimental package for TTS/acoustic exploration outside the core `akkapros` pipeline.

## Current tool: IPA -> phonetizer TSV

CLI:

```bash
python src/akkatts/cli/ipa2phon.py outputs/erra2_accent_ipa.txt -o outputs/erra2_phon.tsv
```

Output columns:

- `kind`: `syllable` or `control`
- `line_no`, `token_no`, `syllable_no`
- `source`: original IPA chunk
- `stress`: 1/0 for `ˈ`
- `onset_mora`, `vowel_mora`, `coda_mora`, `total_mora`
- `control`: for punctuation/pause tags (`⟨pause⟩`, `(.)`, `(..)`, `⟨...⟩`)

Mora defaults (configurable via CLI flags):

- onset unstressed: `0.2`
- onset stressed: `1.0`
- vowel short/long/extra-long: `1/2/3`
- coda single/geminate: `1/2`

This is a first-pass intermediate format meant to feed a downstream phonetizer/voice system.
