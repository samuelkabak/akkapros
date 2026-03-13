# Getting Started

This short guide helps you run the basic pipeline on a sample file and inspect outputs.

Prerequisites
- Python 3.8+
- (optional) activate project venv: `sandbox\activate_project.ps1` on Windows

Run the full pipeline on a sample file:

PowerShell:

```powershell
python -m akkapros.cli.fullprosmaker data/samples/L_I.2_Poem_of_Creation_SB_II.atf -p demo --outdir outputs
```

What to inspect
- `<prefix>_syl.txt` — syllabified output
- `<prefix>_tilde.txt` — prosody-realized pivot format
- `<prefix>_metrics.csv` / `.json` — metrics
- `<prefix>_accent_bold.md` / `_accent_acute.txt` / `_accent_ipa.txt` — reading outputs

Further reading
- Detailed CLI docs: `docs/akkapros/prosmaker.md`, `docs/akkapros/metricalc.md`, `docs/akkapros/printer.md`
- Release checklist: `docs/akkapros/release-strategy.md`
