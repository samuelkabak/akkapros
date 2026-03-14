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

---

## Need Help?

- Check existing issues on GitHub
- Open a new issue with your question
- Include your operating system, Python version, and the exact command you ran