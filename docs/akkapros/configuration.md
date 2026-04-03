# Package-Wide Configuration

The package supports one shared YAML configuration file for the file-processing CLIs under `src/akkapros/cli/`. The config file is optional. If you do not pass `--conf FILE`, each CLI keeps its existing built-in defaults.

Override precedence is always:

1. Explicit CLI option
2. YAML config value
3. Built-in default

## Files

- `src/akkapros/config/default.yaml`: canonical full example with every supported key present
- `python -m akkapros.cli.confwriter`: create or incrementally update config files programmatically

## Structure

The top-level sections are:

- `common`: shared options such as `prefix`, `outdir`, and shared logging controls
- `atfparser`
- `syllabifier`
- `prosmaker`
- `metricalc`
- `printer`

Shared output naming stays in `common`. The schema intentionally does not define stage-specific duplicates such as `metrics_prefix` or `print_prefix`.

`fullprosmaker` is a pipeline runner. It reads `common` plus the relevant
shared stage sections: `syllabifier`, `prosmaker`, `metricalc`, and `printer`.
It does not have a duplicated YAML section of its own for those stage-owned
options.

## Example

```yaml
common:
  prefix: "demo"
  outdir: "outputs"

prosmaker:
  style: "lob"

metricalc:
  json: true

printer:
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

`confwriter` creates missing config files from the canonical schema and updates existing files incrementally. In wave one, it requires `--conf FILE` plus at least one override option.

Examples:

```bash
python -m akkapros.cli.confwriter --conf run.yaml --prefix demo
python -m akkapros.cli.confwriter --conf run.yaml --outdir outputs
python -m akkapros.cli.confwriter --conf run.yaml --prosmaker-style sob
python -m akkapros.cli.confwriter --conf run.yaml --printer-ipa
```

Boolean options also have `--no-...` forms in `confwriter` so existing values can be turned off explicitly.

For common logging keys that would otherwise collide with `confwriter`'s own runtime logging controls, use the config-writing forms `--config-quiet`, `--config-no-console`, `--config-log`, and `--config-log-append`.

## Key Mapping

`confwriter` uses unprefixed flags for `common` keys and section-prefixed flags for tool-specific keys.

Examples:

- `common.prefix` -> `--prefix`
- `common.outdir` -> `--outdir`
- `common.quiet` -> `--config-quiet`
- `atfparser.preserve_case` -> `--atfparser-preserve-case`
- `syllabifier.merge_lines` -> `--syllabifier-merge-lines`
- `prosmaker.style` -> `--prosmaker-style`
- `metricalc.json` -> `--metricalc-json`
- `printer.ipa` -> `--printer-ipa`

When you run `fullprosmaker`, those stage sections still apply. For example,
`prosmaker.style` feeds `--prosody-style`, `metricalc.json` feeds
`--metrics-json`, and `printer.ipa` feeds `--print-ipa`.

## Notes

- The config file uses the repository's restricted YAML subset: nested mappings, scalars, and JSON-style lists such as `[]`.
- Config files are not mandatory.
- The config file controls only recurring options. Input paths remain normal CLI arguments.
- `confwriter` writes files programmatically from the schema; it does not copy `default.yaml` byte-for-byte.
