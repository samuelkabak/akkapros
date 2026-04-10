# Full Prosmaker CLI (`fullprosmaker.py`)

`fullprosmaker.py` runs the complete Akkadian processing pipeline in one
command.

Implementation:
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/lib/syllabify.py`
- `src/akkapros/lib/prosody.py`
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/lib/metrics.py`
- `src/akkapros/lib/print.py`

## Pipeline Stages

| Stage | Input -> Output | Description |
|-------|-----------------|-------------|
| 1. Syllabify | `*_proc.txt` -> `*_syl.txt` | Adds syllable boundaries |
| 2. Prosody | `*_syl.txt` -> `*_tilde.txt` | Applies accentuation |
| 3. Phonetize | `*_tilde.txt` -> `*_ophone.txt`, `*_phone.txt`, `*_ombrola.pho`, `*_mbrola.pho` | Builds finalized phone-row and raw `.pho` artifacts |
| 4. Metrics | `_ophone.txt` + `_phone.txt` -> table/json | Computes interval and structural metrics |
| 5. Print | `*_tilde.txt` -> accent outputs | Generates user-facing text outputs |

## Core Outputs

Always written:

- `<prefix>_syl.txt`
- `<prefix>_tilde.txt`
- `<prefix>_ophone.txt`
- `<prefix>_phone.txt`
- `<prefix>_ombrola.pho`
- `<prefix>_mbrola.pho`

Optional metrics outputs:

- `<prefix>_metrics.txt` with `--metrics-table` or by default when no metrics
  format flag is set
- `<prefix>_metrics.json` with `--metrics-json`

Optional print outputs:

- `<prefix>_accent_acute.txt`
- `<prefix>_accent_bold.md`
- `<prefix>_accent_ipa.txt`
- `<prefix>_accent_xar.txt`
- `<prefix>_xar.txt`

## Syntax

```bash
python src/akkapros/cli/fullprosmaker.py <input_proc.txt> [options]
```

## Key Options

Shared I/O:

- `-p, --prefix <name>`
- `--outdir <dir>`
- `--title <string>`

Prosody:

- `--prosody-style {lob,sob}`
- `--mora-mode {bi,mono}`
- `--prosody-relax-last`

Phonetizer timing/config passthrough:

- `--phonetize-accentuation-distribution-policy {100_0,85_15,70_30}`
- `--phonetize-short-pause-policy {strict,best_effort}`
- `--phonetize-drift-policy {strict,extensible}`
- `--phonetize-drift-tolerance <int>`
- `-t, --option KEY=VALUE`

Metrics output selection:

- `--metrics-table`
- `--metrics-json`

Print output selection:

- `--print-acute`
- `--print-bold`
- `--print-ipa`
- `--print-ipa-proto-semitic {preserve,replace}`
- `--print-circ-hiatus`
- `--print-xar`
- `--print-merger`

The full pipeline no longer exposes `--explicit-link-count` for metrics.
Explicit-link counts are derived from the generated phone-row structure.

## Examples

Minimal full run:

```bash
python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
  -p erra \
  --outdir outputs
```

JSON metrics output:

```bash
python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
  -p erra \
  --outdir outputs \
  --metrics-json
```

Mono-mode comparison run:

```bash
python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
  -p erra-mono \
  --outdir outputs \
  --mora-mode mono \
  --metrics-table
```

Run with punctuation extensions:

```bash
python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
  -p erra \
  --outdir outputs \
  --extra-short-punct-chars "·" \
  --extra-long-punct-chars "※" \
  --extra-short-punct-pattern "^\\s*[·]+\\s*$" \
  --extra-long-punct-pattern "^\\s*[※]+\\s*$"
```

## Stage Behavior Notes

Execution order is fixed:

1. syllabify
2. prosody
3. phonetize
4. metrics
5. print

Metrics now consumes the generated `_ophone.txt` and `_phone.txt` artifacts.
`_tilde.txt` remains the prosody pivot for printer output and upstream
reconstruction, but it is no longer the active metrics input.

Prosody-stage front matter no longer carries explicit-link counts for metrics.
The metrics stage derives those counts from phone-row structure.

## Related Commands

For isolated stage work:

- `atfparser.py`
- `syllabifier.py`
- `prosmaker.py`
- `phonetizer.py`
- `metricalc.py`
- `printer.py`

For production runs, use `fullprosmaker.py` so the stage contracts stay aligned
across the full pipeline.

Front matter for prosody and downstream outputs preserves
`metadata.options.mora_mode` so artifact consumers can distinguish `bi` from
`mono` runs.

Escaped chunks are preserved through the full pipeline using CR-005 syntax:

- `{{text}}`
- `{tag{text}}` where `tag` matches `[0-9a-z_]{1,16}`

Internal tags begin with `_` and are reserved for pipeline-internal handling conventions.

Regex semantics for punctuation patterns are standard Python regex: `^` anchors start, `$` anchors end, and a literal dollar requires `\\$`. The diphthong separator `¨` is treated as a plain character.

Boundary pseudo-tokens are also available in punctuation patterns: `[:bol:]` (beginning of line), `[:eol:]` (end of line). EOF is normalized internally to end-of-line semantics.

When lines are preserved (default, without `--syl-merge-lines`), newline boundaries are preserved in syllabifier output for punctuation, preserve blocks, and number/currency suites.

---

## 🔗 Related Commands

For isolated stage debugging, use the single-stage CLIs:

| Stage | Command |
|-------|---------|
| ATF extraction | `atfparser.py` |
| Syllabification | `syllabifier.py` |
| Prosody realization | `prosmaker.py` |
| Metrics | `metricalc.py` |
| Formatting | `printer.py` |

For **production runs**, use `fullprosmaker.py` to ensure all stages run with consistent options and outputs.

---

## ✅ Summary

`fullprosmaker.py` is the primary entry point for end-to-end Akkadian prosodic analysis. It coordinates all pipeline stages, manages shared options, and produces a complete set of outputs—from syllabified text through metrics and publication-ready formatting—in a single, reproducible command.