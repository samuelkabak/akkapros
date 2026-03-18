# Getting Started

This short guide helps you run the basic pipeline on a sample file and inspect outputs.

---

## Prerequisites

- Python 3.8 or higher

---

## Run the Full Pipeline on a Sample File

### Windows (PowerShell)

    python -m akkapros.cli.fullprosmaker data/samples/L_I.2_Poem_of_Creation_SB_II.atf -p demo --outdir outputs

### Unix/Linux/macOS

    python -m akkapros.cli.fullprosmaker data/samples/L_I.2_Poem_of_Creation_SB_II.atf -p demo --outdir outputs

---

## What to Inspect

After running the command, check these files in the `outputs/` directory:

| File | Description |
|------|-------------|
| `demo_syl.txt` | Syllabified output with syllable boundaries |
| `demo_tilde.txt` | Prosody-realized pivot format with `~` markers |
| `demo_metrics.csv` or `demo_metrics.json` | Metrics in machine-readable format |
| `demo_metrics.txt` | Human-readable metrics table |
| `demo_accent_bold.md` | Bold-marked text for visual inspection |
| `demo_accent_acute.txt` | Acute-accented text for scholarly notation |
| `demo_accent_ipa.txt` | IPA transcription with prosodic markers |

---

## Next Steps

- For detailed CLI documentation, see:
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