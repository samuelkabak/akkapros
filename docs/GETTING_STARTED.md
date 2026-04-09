# Getting Started

This short guide helps you run the basic pipeline on a sample file and inspect outputs.

Text outputs produced by the CLI pipeline begin with YAML front matter,
followed by one blank line and then the content body. The cross-stage contract
is intentionally small: downstream stages rely on `file.title`, and metrics
also relies on `metadata.data.prosody.explicit_word_link_count` unless you
override it on the command line. Metrics JSON carries the same metadata under a
top-level `frontmatter` object.

Metrics and printer outputs do not republish `metadata.data`; they keep only
`metadata.input_file_id` and `metadata.options` in their output front matter.

---

## Prerequisites

- Python 3.8 or higher

---

## Run the Full Pipeline on a Sample File

### Windows (PowerShell)

  python -m akkapros.cli.atfparser data/samples/L_I.2_Poem_of_Creation_SB_II.atf -p demo --outdir outputs
  python -m akkapros.cli.fullprosmaker outputs/demo_proc.txt -p demo --outdir outputs

### Unix/Linux/macOS

  python -m akkapros.cli.atfparser data/samples/L_I.2_Poem_of_Creation_SB_II.atf -p demo --outdir outputs
  python -m akkapros.cli.fullprosmaker outputs/demo_proc.txt -p demo --outdir outputs

You can also move recurring options into a shared config file and reuse them with `--conf FILE`. See `docs/akkapros/configuration.md` for the package-wide schema and `confwriter` usage.

---

## What to Inspect

After running the command, check these files in the `outputs/` directory:

| File | Description |
|------|-------------|
| `demo_syl.txt` | Syllabified output with syllable boundaries |
| `demo_tilde.txt` | Prosody-realized pivot format with `~` markers |
| `demo_phone.txt` | Canonical phone-row artifact emitted by the phonetize stage |
| `demo_metrics.json` | Metrics in machine-readable format |
| `demo_metrics.txt` | Human-readable metrics table |
| `demo_accent_bold.md` | Bold-marked text for visual inspection |
| `demo_accent_acute.txt` | Acute-accented text for scholarly notation |
| `demo_accent_ipa.txt` | IPA transcription with prosodic markers |

Each text file starts with metadata like this:

```yaml
---
package:
  name: akkapros
pipeline: pipeline
step: syllabify
file:
  format: syl
metadata:
  input_file_id: "..."
---

u·kap¦ pi·tiq·ša¦
```

If you need only the linguistic body, skip everything through the second `---`
and the following blank line.

---

## Shared Logging Options

All major CLI entrypoints now expose the same runtime logging controls:

- `--quiet`: suppress console `INFO` output while keeping warnings and errors visible
- `--no-console`: disable console logging entirely
- `--log FILE`: write runtime logs to a file
- `--log-append`: append to the log file instead of overwriting it

Examples:

```powershell
python -m akkapros.cli.fullprosmaker outputs/demo_proc.txt -p demo --outdir outputs --quiet
python -m akkapros.cli.metricalc outputs/demo_tilde.txt --table --no-console --log outputs/metrics.log
python -m akkapros.cli.phoneprep --coverage 1 --log outputs/phoneprep.log --log-append
```

Built-in `--help` and `--version` remain parser-driven. Other runtime status,
warning, and error messages now use the shared logger.

---

## Next Steps

- For detailed CLI documentation, see:
  - `docs/akkapros/configuration.md` – Shared YAML config and `confwriter`
  - `docs/akkapros/fullprosmaker.md` – End-to-end pipeline
  - `docs/akkapros/syllabifier.md` – Syllabification stage
  - `docs/akkapros/prosmaker.md` – Prosody realization stage
  - `docs/akkapros/metricalc.md` – Metrics computation
  - `docs/akkapros/printer.md` – Output formatting

- For versioning and release information:
  - `docs/akkapros/release-strategy.md`

- For the underlying algorithms:
  - `docs/akkapros/prosody-realization-algorithm.md`
  - `docs/akkapros/diphthong-processing.md`
  - `docs/akkapros/metrics-computation.md`

---

## Quick Tips

- Use `--help` with any CLI tool to see all available options
- The demo scripts in `demo/akkapros/prosmaker/` show batch processing examples
- All outputs are fully reproducible given the same input and parameters
- `syllabifier.py` accepts frontmatter-bearing `*_proc.txt` files and plain content-only text files. The supported frontmatter-free path starts at syllabification: `syllabify -> prosmaker -> (metricalc or printer)`.
- `metricalc.py` can override inherited explicit-link metadata with `--explicit-link-count <n>` when needed.
- Escape syntax for non-Akkadian chunks is `{{text}}` or `{tag{text}}` (tag regex: `[0-9a-z_]{1,16}`)
- Internal tags begin with `_`; nested escapes are intentionally unsupported

### Migrating Older Bracket Escapes

If older datasets used bracket escapes like `[text]`, migrate them to `{{text}}` before re-running the pipeline.

```powershell
python scripts/migrate-escapes.py outputs/old_syl.txt --in-place
python scripts/migrate-escapes.py outputs/old_tilde.txt --in-place
```

---

## Need Help?

- Check existing issues on GitHub
- Open a new issue with your question
- Include your operating system, Python version, and the exact command you ran

---

## Running Tests

- Tests expect the `akkapros` package to be importable. In this repo we use a `src/` layout, so Python will not find `akkapros` unless you either install the package or add `src` to `PYTHONPATH`.

- Recommended (editable install from project root):

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest -q
```

- Quick alternative (temporary):

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m pytest -q
```

- Why this is necessary: an editable install (`-e .`) creates an importable package that points to the working tree, so tests can import `akkapros` while you continue editing code. Without it, imports fail during test collection because Python doesn't search `src/` by default.

---

### Pipeline CLI self-tests

Several pipeline components include small module-level self-tests useful for quick verification. From the project root you can run these CLI test harnesses:

```powershell
python .\src\akkapros\cli\fullprosmaker.py --test-all
python .\src\akkapros\cli\atfparser.py --test
python .\src\akkapros\cli\phoneprep.py --test
```

Note: while these CLI tests exercise individual stages, the full `pytest` test-suite assumes the package is importable. We recommend installing the package (editable or regular) before running `pytest` as shown above.