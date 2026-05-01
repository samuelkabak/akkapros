**Demo Scripts**

This folder documents the small demo scripts included with the project. Each demo has two launcher variants (POSIX shell and PowerShell) and writes outputs into its `results/` subfolder.

**Akkapros Demo**
 - **Script (POSIX):** [akkapros/prosmaker/corpus-demo.sh](akkapros/prosmaker/corpus-demo.sh) — runs the `akkapros` demo pipeline on the example corpus using a checked-in grouped config file.
 - **Script (PowerShell):** [akkapros/prosmaker/corpus-demo.ps1](akkapros/prosmaker/corpus-demo.ps1) — same as above for Windows PowerShell.
 - **Config:** [akkapros/prosmaker/corpus-demo.yaml](akkapros/prosmaker/corpus-demo.yaml) — grouped YAML config shared by both launchers and intended as the main place to inspect or change demo parameters. The file now spells out the effective defaults for the demo-relevant `common`, `atfparse`, `syllabify`, `prosody`, `phonetize`, `metrics`, and `print` sections instead of leaving most of them implicit in the package defaults.
 - **Outputs (in results/):**
  - **Processed text:** [akkapros/prosmaker/results/corpus_proc.txt](akkapros/prosmaker/results/corpus_proc.txt) — cleaned ATF → plain Akkadian.
    - **Syllabified:** [akkapros/prosmaker/results/corpus_syl.txt](akkapros/prosmaker/results/corpus_syl.txt) — shared syllabification output consumed by all prosody branches.
    - **Tilde (prosody-realized):** [akkapros/prosmaker/results/corpus-sob_tilde.txt](akkapros/prosmaker/results/corpus-sob_tilde.txt), [akkapros/prosmaker/results/corpus-lob_tilde.txt](akkapros/prosmaker/results/corpus-lob_tilde.txt), and [akkapros/prosmaker/results/corpus-mono-lob_tilde.txt](akkapros/prosmaker/results/corpus-mono-lob_tilde.txt) — prosody-realized (tilde-marked) pivot formats for SOB, bimoraic LOB, and mono-mode LOB.
    - **Phone-row metrics handoff:** generated `_ophone.txt` and `_phone.txt` files are the active inputs for demo metrics runs.
    - **Metrics:** [akkapros/prosmaker/results/corpus-sob_metrics.txt](akkapros/prosmaker/results/corpus-sob_metrics.txt), [akkapros/prosmaker/results/corpus-lob_metrics.txt](akkapros/prosmaker/results/corpus-lob_metrics.txt), and [akkapros/prosmaker/results/corpus-mono-lob_metrics.txt](akkapros/prosmaker/results/corpus-mono-lob_metrics.txt) — example interval-metrics reports for the three demo branches.
    - **Printer outputs:** each branch now regenerates acute, bold, accented XAR, and plain XAR outputs from the generated `_phone.txt` plus matching `_ophone.txt` pair. Representative files are [akkapros/prosmaker/results/corpus-sob_accent_acute.txt](akkapros/prosmaker/results/corpus-sob_accent_acute.txt), [akkapros/prosmaker/results/corpus-lob_accent_bold.md](akkapros/prosmaker/results/corpus-lob_accent_bold.md), [akkapros/prosmaker/results/corpus-mono-lob_accent_xar.txt](akkapros/prosmaker/results/corpus-mono-lob_accent_xar.txt), and [akkapros/prosmaker/results/corpus-lob_xar.txt](akkapros/prosmaker/results/corpus-lob_xar.txt).

**Akkapros Lexlinks Demo**
 - **Script (POSIX):** [akkapros/lexlinks/construct-demo.sh](akkapros/lexlinks/construct-demo.sh) — runs `fullprosmaker.py` on the checked-in construct-prepared Erra lexical-links input.
 - **Script (PowerShell):** [akkapros/lexlinks/construct-demo.ps1](akkapros/lexlinks/construct-demo.ps1) — PowerShell variant of the same full-pipeline demo.
 - **Config:** [akkapros/lexlinks/construct-demo.yaml](akkapros/lexlinks/construct-demo.yaml) — grouped YAML config shared by both launchers. It sets the runnable prefix to `erra_construct` and keeps the demo outputs in `demo/akkapros/lexlinks/results/`.
 - **Input:** `data/lexlinks/construct_prep/erra_construct_proc.txt` — prebuilt cleaned construct text consumed directly by `fullprosmaker.py`.
 - **Outputs (in results/):** the run emits two parallel artifact sets:
   - **Bi mode (style lob):** `erra_construct_*` prefix — the standard `fullprosmaker` artifact set including `_syl.txt`, `_tilde.txt`, `_ophone.txt`, `_phone.txt`, `_metrics.txt`, `_metrics.json`, `_accent_acute.txt`, `_accent_bold.md`, `_accent_xar.txt`, `_xar.txt`, `_ombrola.pho`, and `_mbrola.pho`.
   - **Mono mode (style lob):** `erra_construct-mono_*` prefix — same artifact set produced with `--mora-mode mono`, allowing direct comparison of bi vs. mono mode outputs on the same input.

**Akkapros Phoneprep Demo**
 - **Script (POSIX):** [akkapros/phoneprep/phoneprep-demo.sh](akkapros/phoneprep/phoneprep-demo.sh) — runs the phone-preparation demo in the `akkapros` toolchain.
 - **Script (PowerShell):** [akkapros/phoneprep/phoneprep-demo.ps1](akkapros/phoneprep/phoneprep-demo.ps1) — PowerShell variant.
 - **Outputs (in results/):**
  - **Phoneprep text:** [akkapros/phoneprep/results/phoneprep.txt](akkapros/phoneprep/results/phoneprep.txt) — the prepared phonetic sequence.
  - **Diphones / manifests:** [akkapros/phoneprep/results/phoneprep_diphones.tsv](akkapros/phoneprep/results/phoneprep_diphones.tsv) and [akkapros/phoneprep/results/phoneprep_manifest.tsv](akkapros/phoneprep/results/phoneprep_manifest.tsv).
  - **Recording helper HTML:** [akkapros/phoneprep/results/phoneprep_recording_helper.html](akkapros/phoneprep/results/phoneprep_recording_helper.html).

**Where the inputs come from**
- The demos use sample ATF files contained in `data/samples/` (see the repository root `data/samples/` directory).

**How to run**
On Unix-like systems (bash):

```bash
sh demo/akkapros/prosmaker/corpus-demo.sh
sh demo/akkapros/lexlinks/construct-demo.sh
sh demo/akkapros/phoneprep/phoneprep-demo.sh
```

On Windows PowerShell:

```powershell
.\demo\akkapros\prosmaker\corpus-demo.ps1
.\demo\akkapros\lexlinks\construct-demo.ps1
.\demo\akkapros\phoneprep\phoneprep-demo.ps1
```

To inspect or update the checked-in prosmaker demo config, use `confwriter`:

```bash
python -m akkapros.cli.confwriter --conf demo/akkapros/prosmaker/corpus-demo.yaml --list
python -m akkapros.cli.confwriter --conf demo/akkapros/prosmaker/corpus-demo.yaml --get print.run.xar
python -m akkapros.cli.confwriter --conf demo/akkapros/prosmaker/corpus-demo.yaml --verify
```

**Notes**
- The shell and PowerShell scripts are thin wrappers over the current config-backed CLIs. Stable demo defaults live in `demo/akkapros/prosmaker/corpus-demo.yaml`, and that file is the primary experimentation surface for users. Branch-specific differences such as `corpus-lob` versus `corpus-sob`, plus the mono-mode branch, are still passed explicitly by the wrapper because one shared config file cannot express all three branch runs at once.
- The checked-in demo config intentionally mirrors the current effective defaults for the stages used by this demo. If package defaults change later, refresh the demo config as part of keeping the demo self-describing.
- The demo printer commands now run from `<prefix>_phone.txt` and use the matching `<prefix>_ophone.txt` pair under the active printer contract. `_ophone.txt` is not the primary standalone printer input.
- The demo metrics commands run phonetizer first and then feed `metricalc.py` with `<prefix>_phone.txt`.
- Output files are overwritten on each run; keep copies if you want to compare runs.



