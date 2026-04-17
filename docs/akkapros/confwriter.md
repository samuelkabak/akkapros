# Confwriter

`confwriter` is the schema-driven editor for the package-wide YAML config file.
It does not mirror every config key as a dedicated CLI flag. Instead, it works
with full YAML-path keys and a small set of operations.

`confwriter` is also intentionally outside the runtime effective-config-object
workflow used by the processing CLIs. It edits grouped config state, while the
runtime tools materialize their own effective in-memory config view before
processing begins.

## Command Model

All normal invocations use `--conf FILE` plus one or more operations:

```bash
python -m akkapros.cli.confwriter --conf run.yaml --set common.run.prefix=demo
python -m akkapros.cli.confwriter --conf run.yaml --set common.run.outdir=outputs --set prosody.process.style=sob
python -m akkapros.cli.confwriter --conf run.yaml --get prosody.process.style
python -m akkapros.cli.confwriter --conf run.yaml --list
python -m akkapros.cli.confwriter --conf run.yaml --list atfparse
python -m akkapros.cli.confwriter --conf run.yaml --unset prosody.process.style
python -m akkapros.cli.confwriter --conf run.yaml --set-default prosody.process.style
python -m akkapros.cli.confwriter --conf run.yaml --verify
```

Supported operations:

- `--set KEY=VALUE`: set one key; repeatable
- `--get KEY`: print one effective value
- `--list [SUBSTRING]`: print the schema-backed key inventory, optionally filtered
- `--unset KEY`: write `null` for one key; repeatable
- `--set-default KEY`: write the schema default value explicitly; repeatable
- `--verify`: run shared phonetize semantic verification against the effective grouped config without modifying the file

`--verify` is a standalone read-only operation.

## Key Paths

Keys use full YAML paths such as:

- `common.run.prefix`
- `common.run.outdir`
- `atfparse.process.preserve_case`
- `prosody.process.style`
- `phonetize.process.timing_model.geminate_policy`
- `phonetize.process.timing_model.speech.wpm`
- `metrics.run.json`
- `print.run.ipa`

Unknown keys are rejected before any file is modified.

The `phonetize.*` keys edited here govern the phonetizer stage used by both
`phonetizer` and `fullprosmaker`, including the finalized dual-output handoff
files `<prefix>_ophone.txt` and `<prefix>_phone.txt`.

The processing CLIs and `confwriter` now use the same canonical grouped path
surface, including `phonetize.process.timing_model.*`.

## Value Rules

`--set` values are parsed according to the schema:

- booleans: `true`, `false`
- null: `null`
- numbers: `165`, `35.0`
- strings: plain text or quoted JSON strings
- lists: JSON-style arrays such as `[]` or `["foo", "bar"]`

Examples:

```bash
python -m akkapros.cli.confwriter --conf run.yaml --set metrics.run.json=true
python -m akkapros.cli.confwriter --conf run.yaml --set phonetize.process.timing_model.geminate_policy=cumulative
python -m akkapros.cli.confwriter --conf run.yaml --set phonetize.process.timing_model.speech.wpm=201
python -m akkapros.cli.confwriter --conf run.yaml --set syllabify.process.extra_short_punct_pattern=["\\.\\.\\."]
```

If any requested key or value is invalid, `confwriter` exits with an error and
does not write the file.

## Shared Verify

`confwriter --verify` runs the same shared phonetize semantic verification layer
used by standalone phonetizer preflight.

The verify path assumes schema-valid grouped config first, then applies the
current baseline semantic invariant inventory and warning rules for the active
phonetize timing model. Output status is one of:

- `VERIFY STATUS: pass`
- `VERIFY STATUS: pass-with-warnings`
- `VERIFY STATUS: failure`

The live verification surface includes the validation-only bounds
`segmental_floor` and `segmental_ceiling`, plus class-local consonant
`perception_limits.gemination_max` values. Runtime consonant saturation uses the
class-local maxima, while verification still checks those maxima against the
global ceiling.

When verification fails, output includes the failing full dotted path or paths,
the failed relation, and the reason. When warnings fire without blocking,
output includes the warning path, threshold or formula, and configuration-wide
hint lines for warning sources such as weakened pause-band compatibility.

Example:

```bash
python -m akkapros.cli.confwriter --conf run.yaml --verify
```

## Listing Output

`--list` prints each known key with:

- full path
- type display
- schema default
- canonical help text

Example shape:

```text
common.run.prefix { TEXT | null } (default: "akkapros") : Shared output prefix used by file-producing CLIs.
atfparse.process.preserve_h { true | false } (default: false) : Preserve original h/H characters.
```

Filtering is case-insensitive substring matching on the full key path.

## Unset vs Set-Default

`--unset KEY` writes `null` into the YAML.

That means the config file no longer explicitly sets the option. Downstream
runtime resolution falls back to the built-in default when the schema defines
one.

`--set-default KEY` writes the schema default explicitly instead of `null`.

Examples:

```bash
python -m akkapros.cli.confwriter --conf run.yaml --unset prosody.process.style
python -m akkapros.cli.confwriter --conf run.yaml --set-default prosody.process.style
```

## Notes

- Missing config files are created programmatically from the canonical schema.
- Existing config files are updated incrementally.
- `--help` stays concise; use `--list` for the full schema inventory.
- `--verify` never mutates the config file, whether it passes, warns, or fails.
- `--stdout` prints the resulting config text after a successful mutating run.