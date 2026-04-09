# Confwriter

`confwriter` is the schema-driven editor for the package-wide YAML config file.
It does not mirror every config key as a dedicated CLI flag. Instead, it works
with full YAML-path keys and a small set of operations.

## Command Model

All normal invocations use `--conf FILE` plus one or more operations:

```bash
python -m akkapros.cli.confwriter --conf run.yaml --set common.prefix=demo
python -m akkapros.cli.confwriter --conf run.yaml --set common.outdir=outputs --set prosody.style=sob
python -m akkapros.cli.confwriter --conf run.yaml --get prosody.style
python -m akkapros.cli.confwriter --conf run.yaml --list
python -m akkapros.cli.confwriter --conf run.yaml --list atfparse
python -m akkapros.cli.confwriter --conf run.yaml --unset prosody.style
python -m akkapros.cli.confwriter --conf run.yaml --set-default prosody.style
```

Supported operations:

- `--set KEY=VALUE`: set one key; repeatable
- `--get KEY`: print one effective value
- `--list [SUBSTRING]`: print the schema-backed key inventory, optionally filtered
- `--unset KEY`: write `null` for one key; repeatable
- `--set-default KEY`: write the schema default value explicitly; repeatable

## Key Paths

Keys use full YAML paths such as:

- `common.prefix`
- `common.outdir`
- `atfparse.preserve_case`
- `prosody.style`
- `phonetize.process.geminate_policy`
- `phonetize.timing_model.speech.wpm`
- `metrics.json`
- `print.ipa`

Unknown keys are rejected before any file is modified.

The `phonetize.*` keys edited here govern the phonetizer stage used by both
`phonetizer` and `fullprosmaker`, including the Phase 1 dual-output handoff
files `<prefix>_ophone.txt` and `<prefix>_phone.txt`.

## Value Rules

`--set` values are parsed according to the schema:

- booleans: `true`, `false`
- null: `null`
- numbers: `165`, `35.0`
- strings: plain text or quoted JSON strings
- lists: JSON-style arrays such as `[]` or `["foo", "bar"]`

Examples:

```bash
python -m akkapros.cli.confwriter --conf run.yaml --set metrics.json=true
python -m akkapros.cli.confwriter --conf run.yaml --set phonetize.process.geminate_policy=cumulative
python -m akkapros.cli.confwriter --conf run.yaml --set phonetize.timing_model.speech.wpm=201
python -m akkapros.cli.confwriter --conf run.yaml --set syllabify.extra_short_punct_pattern=["\\.\\.\\."]
```

If any requested key or value is invalid, `confwriter` exits with an error and
does not write the file.

## Listing Output

`--list` prints each known key with:

- full path
- type display
- schema default
- canonical help text

Example shape:

```text
common.prefix { TEXT | null } (default: "akkapros") : Shared output prefix used by file-producing CLIs.
atfparse.preserve_h { true | false } (default: false) : Preserve original h/H characters.
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
python -m akkapros.cli.confwriter --conf run.yaml --unset prosody.style
python -m akkapros.cli.confwriter --conf run.yaml --set-default prosody.style
```

## Notes

- Missing config files are created programmatically from the canonical schema.
- Existing config files are updated incrementally.
- `--help` stays concise; use `--list` for the full schema inventory.
- `--stdout` prints the resulting config text after a successful mutating run.