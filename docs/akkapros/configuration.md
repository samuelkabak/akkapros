# Package-Wide Configuration

The package supports one shared YAML configuration file for the file-processing CLIs under `src/akkapros/cli/`. The config file is optional. If you do not pass `--conf FILE`, each CLI keeps its existing built-in defaults.

Override precedence is always:

1. Explicit CLI option
2. YAML config value
3. Built-in default

## Files

- `src/akkapros/config/default.yaml`: canonical full example with every supported key present
- `python -m akkapros.cli.confwriter`: create or incrementally update config files programmatically
- `docs/akkapros/confwriter.md`: detailed command reference for schema-driven config editing

## Structure

The top-level sections are:

- `common`: shared options such as `prefix`, `outdir`, and shared logging controls
- `atfparse`
- `syllabify`
- `prosody`
- `phonetize`
- `metrics`
- `print`

Shared output naming stays in `common`. The schema intentionally does not define stage-specific duplicates such as `metrics_prefix` or `print_prefix`.

`common.prefix` is required for runnable grouped configs. `confwriter` rejects writes that would leave it null, and prefix-dependent CLIs reject execution if no effective prefix is available from `--prefix` or `common.prefix`.

The `syllabify` section is also the only grouped-config owner for
`extra_vowels`, `extra_consonants`, and the four `extra_*punct*` settings.
Those values are written into front matter by syllabify, preserved downstream,
and consumed by metrics from the input file rather than re-declared under
`metrics`.

`fullprosmaker` is a pipeline runner. It reads `common` plus the relevant
shared stage sections: `syllabify`, `prosody`, `phonetize`, `metrics`, and `print`.
It does not have a duplicated YAML section of its own for those stage-owned
options.

The `phonetize` section owns the timing-model and phonetizer process controls.
That means grouped config no longer defines `metrics.wpm` or
`metrics.pause_ratio`. During the current transition, `metricalc` still computes
its outputs from `_tilde`, but it uses the phonetize transition defaults
internally (`wpm = 193`, `pause_ratio = 35`) rather than exposing separate
metrics-owned timing knobs.

## Example

```yaml
common:
  prefix: "demo"
  outdir: "outputs"

prosody:
  style: "lob"

phonetize:
  process:
    geminate_policy: "corrective"

metrics:
  json: true

print:
  ipa: true
```

With this file, you can run:

```bash
python -m akkapros.cli.fullprosmaker outputs/demo_proc.txt --conf run.yaml
```

The command will still accept explicit overrides, for example:

```bash
python -m akkapros.cli.fullprosmaker outputs/demo_proc.txt --conf run.yaml --prefix other
```

In that case, `--prefix other` overrides the `common.prefix` value from the config file while the remaining config-supplied values continue to apply.

## Confwriter

`confwriter` creates missing config files from the canonical schema and updates existing files incrementally. It now uses full YAML-path keys and a small schema-driven operation surface instead of one dedicated writer flag per config key.

Examples:

```bash
python -m akkapros.cli.confwriter --conf run.yaml --set common.prefix=demo
python -m akkapros.cli.confwriter --conf run.yaml --set common.outdir=outputs
python -m akkapros.cli.confwriter --conf run.yaml --set prosody.style=sob
python -m akkapros.cli.confwriter --conf run.yaml --set phonetize.process.geminate_policy=cumulative
python -m akkapros.cli.confwriter --conf run.yaml --set print.ipa=true
python -m akkapros.cli.confwriter --conf run.yaml --get common.log_append
python -m akkapros.cli.confwriter --conf run.yaml --list phonetize
python -m akkapros.cli.confwriter --conf run.yaml --unset prosody.style
python -m akkapros.cli.confwriter --conf run.yaml --set-default prosody.style
```

`--set` is repeatable and validates both key paths and values against the canonical schema before any file is written. If any requested key or value is invalid, `confwriter` exits with an error and leaves the config file unchanged.

`--unset KEY` writes `null` for that key. Downstream tools interpret that stored null through normal config/default resolution, so the effective value falls back to the built-in default when the schema defines one.

`--set-default KEY` writes the schema default value explicitly.

## Key Mapping

`confwriter` uses full YAML-path keys.

Examples:

- `common.prefix`
- `common.outdir`
- `common.quiet`
- `atfparse.preserve_case`
- `syllabify.merge_lines`
- `prosody.style`
- `phonetize.process.geminate_policy`
- `phonetize.timing_model.speech.wpm`
- `metrics.json`
- `print.ipa`

When you run `fullprosmaker`, those stage sections still apply. For example,
`prosody.style` feeds `--prosody-style`, `metrics.json` feeds
`--metrics-json`, and `print.ipa` feeds `--print-ipa`.

## Notes

- The config file uses the repository's restricted YAML subset: nested mappings, scalars, and JSON-style lists such as `[]`.
- Config files are not mandatory.
- The config file controls only recurring options. Input paths remain normal CLI arguments.
- `confwriter` writes files programmatically from the schema; it does not copy `default.yaml` byte-for-byte.
- `confwriter --list` is the schema inventory surface; normal `--help` stays concise.
