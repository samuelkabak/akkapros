**Demo Scripts**

This folder documents the small demo scripts included with the project. Each demo has two launcher variants (POSIX shell and PowerShell) and writes outputs into its `results/` subfolder.

**Akkapros Demo**
- **Script (POSIX):** [demo/akkapros/corpus-demo.sh](demo/akkapros/corpus-demo.sh) â€” runs the `akkapros` demo pipeline on the example corpus and produces processed, syllabified, prosody-realized, and metric outputs.
- **Script (PowerShell):** [demo/akkapros/corpus-demo.ps1](demo/akkapros/corpus-demo.ps1) â€” same as above for Windows PowerShell.
- **Outputs (in results/):**
  - **Processed text:** [demo/akkapros/results/corpus_proc.txt](demo/akkapros/results/corpus_proc.txt) â€” cleaned ATF â†’ plain Akkadian.
  - **Syllabified:** [demo/akkapros/results/corpus_syl.txt](demo/akkapros/results/corpus_syl.txt) â€” syllabification output used by the prosmaker.
  - **Tilde (prosody-realized):** [demo/akkapros/results/corpus-sob_tilde.txt](demo/akkapros/results/corpus-sob_tilde.txt) â€” prosody-realized (tilde-marked) pivot format.
  - **Metrics:** [demo/akkapros/results/corpus-sob-p30_metrics.txt](demo/akkapros/results/corpus-sob-p30_metrics.txt) â€” example metrics report (VarcoC, %V, Î”C) for the SOB model.
  - **Accent/IPA outputs:** [demo/akkapros/results/corpus-sob_accent_ipa.txt](demo/akkapros/results/corpus-sob_accent_ipa.txt) and [demo/akkapros/results/corpus-sob_accent_bold.md](demo/akkapros/results/corpus-sob_accent_bold.md).

**Akkapros Phoneprep Demo**
- **Script (POSIX):** [demo/akkapros/phoneprep/demo-phoneprep.sh](demo/akkapros/phoneprep/demo-phoneprep.sh) â€” runs the phone-preparation demo in the `akkapros` toolchain.
- **Script (PowerShell):** [demo/akkapros/phoneprep/demo-phoneprep.ps1](demo/akkapros/phoneprep/demo-phoneprep.ps1) â€” PowerShell variant.
- **Outputs (in results/):**
  - **Phoneprep text:** [demo/akkapros/phoneprep/results/phoneprep.txt](demo/akkapros/phoneprep/results/phoneprep.txt) â€” the prepared phonetic sequence.
  - **Diphones / manifests:** [demo/akkapros/phoneprep/results/phoneprep_diphones.tsv](demo/akkapros/phoneprep/results/phoneprep_diphones.tsv) and [demo/akkapros/phoneprep/results/phoneprep_manifest.tsv](demo/akkapros/phoneprep/results/phoneprep_manifest.tsv).
  - **Recording helper HTML:** [demo/akkapros/phoneprep/results/phoneprep_recording_helper.html](demo/akkapros/phoneprep/results/phoneprep_recording_helper.html).

**Where the inputs come from**
- The demos use sample ATF files contained in `data/samples/` (see the repository root `data/samples/` directory).

**How to run**
On Unix-like systems (bash):

```bash
sh demo/akkapros/corpus-demo.sh
sh demo/akkapros/phoneprep/demo-phoneprep.sh
```

On Windows PowerShell:

```powershell
.\demo\akkapros\corpus-demo.ps1
.\demo\akkapros\phoneprep\demo-phoneprep.ps1
```

**Notes**
- The shell and PowerShell scripts are small wrappers that call the Python CLI modules in `src/` with example arguments; inspect the scripts for exact command-line flags.
- Output files are overwritten on each run; keep copies if you want to compare runs.


