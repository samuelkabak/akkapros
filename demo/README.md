**Demo Scripts**

This folder documents the small demo scripts included with the project. Each demo has two launcher variants (POSIX shell and PowerShell) and writes outputs into its `results/` subfolder.

**Akkapros Demo**
 - **Script (POSIX):** [akkapros/prosmaker/corpus-demo.sh](akkapros/prosmaker/corpus-demo.sh) — runs the `akkapros` demo pipeline on the example corpus and produces processed, syllabified, prosody-realized, and metric outputs.
 - **Script (PowerShell):** [akkapros/prosmaker/corpus-demo.ps1](akkapros/prosmaker/corpus-demo.ps1) — same as above for Windows PowerShell.
 - **Outputs (in results/):**
  - **Processed text:** [akkapros/prosmaker/results/corpus_proc.txt](akkapros/prosmaker/results/corpus_proc.txt) — cleaned ATF → plain Akkadian.
  - **Syllabified:** [akkapros/prosmaker/results/corpus_syl.txt](akkapros/prosmaker/results/corpus_syl.txt) — syllabification output used by the prosmaker.
  - **Tilde (prosody-realized):** [akkapros/prosmaker/results/corpus-sob_tilde.txt](akkapros/prosmaker/results/corpus-sob_tilde.txt) — prosody-realized (tilde-marked) pivot format.
  - **Metrics:** [akkapros/prosmaker/results/corpus-sob-p30_metrics.txt](akkapros/prosmaker/results/corpus-sob-p30_metrics.txt) — example metrics report (VarcoC, %V, ΔC) for the SOB model.
  - **Accent/IPA outputs:** [akkapros/prosmaker/results/corpus-sob_accent_ipa.txt](akkapros/prosmaker/results/corpus-sob_accent_ipa.txt) and [akkapros/prosmaker/results/corpus-sob_accent_bold.md](akkapros/prosmaker/results/corpus-sob_accent_bold.md).

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
sh demo/akkapros/phoneprep/phoneprep-demo.sh
```

On Windows PowerShell:

```powershell
.\demo\akkapros\prosmaker\corpus-demo.ps1
.\demo\akkapros\phoneprep\phoneprep-demo.ps1
```

**Notes**
- The shell and PowerShell scripts are small wrappers that call the Python CLI modules in `src/` with example arguments; inspect the scripts for exact command-line flags.
- Output files are overwritten on each run; keep copies if you want to compare runs.



