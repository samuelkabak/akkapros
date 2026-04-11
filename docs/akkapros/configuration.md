# Package-Wide Configuration

The package supports one shared YAML configuration file for the file-processing CLIs under `src/akkapros/cli/`. The config file is optional. Even when you do not pass `--conf FILE`, each runtime CLI now materializes one effective in-memory config object from canonical defaults before processing starts.

Override precedence is always:

1. `-t/--option KEY=VALUE` path override
2. Dedicated config-backed CLI flag
3. YAML config value
4. Built-in default

Dedicated config-backed flags remain supported during the transition, but the preferred runtime interface is now config-first: `--conf FILE` plus optional repeatable `-t/--option KEY=VALUE` overrides.

## Files

- `src/akkapros/config/default.yaml`: canonical full example with every supported key present
- `python -m akkapros.cli.confwriter`: create or incrementally update config files programmatically
- `docs/akkapros/confwriter.md`: detailed command reference for schema-driven config editing

## Structure

The top-level sections are:

- `common`: shared run options under `common.run.*`
- `atfparse`
- `syllabify`
- `prosody`
- `phonetize`
- `metrics`
- `print`

Shared output naming stays in `common.run`. The schema intentionally does not define stage-specific duplicates such as `metrics_prefix` or `print_prefix`.

At runtime, `--help` is now program-scoped and path-scoped:

- `python -m akkapros.cli.phonetizer --help` shows the `common` section plus the config subtree relevant to `phonetizer`
- `python -m akkapros.cli.phonetizer --help phonetize.process.timing_model.durations` shows only that requested subtree

`common.run.prefix` is required for runnable grouped configs. `confwriter` rejects writes that would leave it null, and prefix-dependent CLIs reject execution if no effective prefix is available from `--prefix` or `common.run.prefix`.

The `syllabify` section is also the only grouped-config owner for
`extra_vowels`, `extra_consonants`, and the four `extra_*punct*` settings.
Those values are written into front matter by syllabify, preserved downstream,
and consumed by metrics from the input file rather than re-declared under
`metrics`.

`fullprosmaker` is a pipeline runner. It reads `common` plus the relevant
shared stage sections: `syllabify`, `prosody`, `phonetize`, `metrics`, and `print`.
It does not have a duplicated YAML section of its own for those stage-owned
options.

The `phonetize` section owns both the intonation presets under
`phonetize.process.intonation` and the timing-model controls under
`phonetize.process.timing_model`.
That means grouped config no longer defines `metrics.wpm` or
`metrics.pause_ratio`. Metricalc now computes its outputs from the phonetizer
artifacts `_ophone.txt` and `_phone.txt`, while still using the phonetize
transition defaults internally (`wpm = 193`, `pause_ratio = 35`) rather than
exposing separate metrics-owned timing knobs.

The active intonation presets are:

- `phonetize.process.intonation.stress`
- `phonetize.process.intonation.question`
- `phonetize.process.intonation.statement`
- `phonetize.process.intonation.exclamation`
- `phonetize.process.intonation.continuation`

Those values are normalized into canonical row-level intonation tokens in the
finalized phone-row artifacts and then reused when `.pho` export is emitted.

Those same `phonetize` settings are used when `phonetizer` and `fullprosmaker`
materialize and finalize the two phone-row outputs, `<prefix>_ophone.txt` and
`<prefix>_phone.txt`.

Before standalone phonetizer runtime continues into Phase 2 realization, it
now runs the shared phonetize semantic verification layer against the effective
`phonetize` config. Blocking failures stop `_ophone.txt` and `_phone.txt`
generation before runtime realization begins. Warning-only conditions are
reported distinctly and allow processing to continue.

## Example

```yaml
common:
  run:
    prefix: "demo"
    outdir: "outputs"

prosody:
  process:
    style: "lob"

phonetize:
  process:
    timing_model:
      geminate_policy: "corrective"

metrics:
  run:
    json: true

print:
  run:
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

In that case, `--prefix other` overrides the `common.run.prefix` value from the config file while the remaining config-supplied values continue to apply.

The preferred equivalent is the path-based form:

```bash
python -m akkapros.cli.fullprosmaker outputs/demo_proc.txt --conf run.yaml --option common.run.prefix="other"
```

Phonetize-owned runtime overrides and scoped help use the same canonical grouped
paths that are stored in YAML, including `phonetize.process.intonation.*` and
`phonetize.process.timing_model.*`.

## Confwriter

`confwriter` creates missing config files from the canonical schema and updates existing files incrementally. It now uses full YAML-path keys and a small schema-driven operation surface instead of one dedicated writer flag per config key.

Examples:

```bash
python -m akkapros.cli.confwriter --conf run.yaml --set common.run.prefix=demo
python -m akkapros.cli.confwriter --conf run.yaml --set common.run.outdir=outputs
python -m akkapros.cli.confwriter --conf run.yaml --set prosody.process.style=sob
python -m akkapros.cli.confwriter --conf run.yaml --set phonetize.process.timing_model.geminate_policy=cumulative
python -m akkapros.cli.confwriter --conf run.yaml --set print.run.ipa=true
python -m akkapros.cli.confwriter --conf run.yaml --get common.run.log_append
python -m akkapros.cli.confwriter --conf run.yaml --list phonetize
python -m akkapros.cli.confwriter --conf run.yaml --unset prosody.process.style
python -m akkapros.cli.confwriter --conf run.yaml --set-default prosody.process.style
python -m akkapros.cli.confwriter --conf run.yaml --verify
```

`--set` is repeatable and validates both key paths and values against the canonical schema before any file is written. If any requested key or value is invalid, `confwriter` exits with an error and leaves the config file unchanged.

`--unset KEY` writes `null` for that key. Downstream tools interpret that stored null through normal config/default resolution, so the effective value falls back to the built-in default when the schema defines one.

`--set-default KEY` writes the schema default value explicitly.

`--verify` is a standalone read-only operation. It runs the shared phonetize
semantic verification layer against the effective grouped config and reports one
of `pass`, `pass-with-warnings`, or `failure` without modifying the file.

## Key Mapping

`confwriter` uses full YAML-path keys.

Examples:

- `common.run.prefix`
- `common.run.outdir`
- `common.run.quiet`
- `atfparse.process.preserve_case`
- `syllabify.process.merge_lines`
- `prosody.process.style`
- `phonetize.process.intonation.stress`
- `phonetize.process.timing_model.geminate_policy`
- `phonetize.process.timing_model.speech.wpm`
- `metrics.run.json`
- `print.run.ipa`

When you run `fullprosmaker`, those stage sections still apply. For example,
`prosody.process.style` feeds `--prosody-style`, `metrics.run.json` feeds
`--metrics-json`, and `print.run.ipa` feeds `--print-ipa`.

## Notes

- The config file uses the repository's restricted YAML subset: nested mappings, scalars, and JSON-style lists such as `[]`.
- Config files are not mandatory.
- The config file controls only recurring options. Input paths remain normal CLI arguments.
- Runtime CLIs now expose repeatable `-t/--option KEY=VALUE` overrides for config-backed settings.
- Runtime `--help [PATH]` is schema-aware; deprecated dedicated flags are listed after the active config-path-driven sections.
- `confwriter` writes files programmatically from the schema; it does not copy `default.yaml` byte-for-byte.
- `confwriter --list` is the schema inventory surface; normal `--help` stays concise.
