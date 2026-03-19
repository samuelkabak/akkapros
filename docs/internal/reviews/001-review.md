# Code and Project Review — akkapros v1.0.1

Review ID: review-001
Date: 2026-03-19
Reviewer: GitHub Copilot (Claude Sonnet 4.6), based on full project scan
Scope: All Python source (`src/akkapros/`), demo scripts, `docs/akkapros/`, `docs/internal/`,
       `tmp/research-notes.md` (for context only; not MIT-licensed), `outputs/`, project root files.

---

## 1. Executive Summary

`akkapros` is a well-scoped, carefully motivated computational toolkit for Akkadian prosody
reconstruction. The codebase is clean, architecturally sound, and already carries a usable
release (v1.0.1) with production-quality documentation. The research hypothesis is original
and the implementation is reproducible. The main open areas are: one known test regression
(syllabifier diphthong separator), a pending breaking rename (CR-004), an incomplete
specifications folder (now filled), and some forward-looking gaps in the TTS pipeline
(segmenter not yet built).

The project punches well above its size. For a solo academic toolkit it shows professional
engineering discipline (ADR + CR process, semantic versioning, CLI/lib separation, built-in
self-tests, CHANGELOG, CITATION.cff). The phonological reasoning behind every design
decision is traceable, which is rare in computational humanities work.

---

## 2. Architecture Assessment

### 2.1 Strengths

**CLI/lib separation is correctly implemented.**
Every CLI module in `src/akkapros/cli/` is a thin argument-parsing wrapper. All substantive
logic lives in `src/akkapros/lib/`. The separation is consistently maintained across
`atfparse.py`, `syllabify.py`, `prosody.py`, `metrics.py`, `print.py`, and `phoneprep.py`.
This makes the library importable without CLI overhead, and it makes tests clean.

**Stage pipeline with explicit pivot format is solid.**
The `*_tilde.txt` pivot format is a genuine design achievement. It is human-readable (good
for debugging), machine-parseable (good for downstream tools), and stable enough to act as
a public contract. Each stage reads exactly the previous stage's output, so failures are
localised to stage boundaries. This is an appropriate architecture for a research tool that
needs reproducibility of intermediate results.

**Version management is centralised.**
`src/akkapros/__init__.py` carries `__version__`, `__author__`, `__license__`, and
`__repo_url__`; all CLIs import from this single source. The `--version` flag on every CLI
delegates to `get_version_display()`, producing a consistent multi-line output. This
followed ADR-002 correctly.

**Output prefix + outdir convention is consistent.**
Every CLI accepts `-p / --prefix` and `--outdir` and constructs output filenames with
`<prefix>_<suffix>.<ext>`. The convention is enforced via ADR-003. Downstream scripts and
makefiles can rely on this pattern without parsing CLI output.

**Unicode handling is explicit throughout.**
Files are always opened with `encoding='utf-8'`. No platform-default encoding is assumed.
Characters like ā, ē, ī, ū, â, ê, î, û, ṭ, ṣ, q, š, ḫ, ḥ, ʾ, ʿ are treated as
first-class citizens in character sets, not as "special cases". The
`.gitattributes` file enforces consistent line endings across platforms.

**Research motivation is encoded in the code.**
Unlike many research-adjacent tools where the algorithm is a black box, `akkapros` traces
every phonological constraint to an attested Akkadian process or a published grammar rule:
the prohibition on short-vowel lengthening, the ban on word-final gemination, the
precedence of coda over onset gemination. This is excellent practice for reproducible
digital humanities work.

---

### 2.2 Areas for Improvement

**`simple_safe_filename()` is duplicated.**
The function appears in `cli/prosmaker.py` and `cli/metricalc.py` in addition to its
canonical home in `lib/utils.py`. The CLI-level copies should be removed and the import
from `akkapros.lib.utils` used instead. This is a minor maintenance risk (the copies could
diverge).

**`fullprosmaker.py` contains its own `_resolve_ipa_options()` that mirrors `printer.py`.**
Both files define near-identical `_resolve_ipa_options()` functions. If the IPA flag names
change, both must be updated. The canonical function should live in a shared location
(either `lib` or `cli/_cli_common.py`) and be imported.

**`phoneprep.py` is a large monolithic CLI file.**
Unlike the other CLIs, `phoneprep.py` contains the full implementation (inventory
definitions, optimizer, pattern builder, sidecar emitter) in one file rather than
delegating to a library module. This breaks the ADR-001 CLI/lib separation pattern.
A future refactor should move the core logic to `lib/phoneprep.py`.

**No protection against corrupted intermediate files.**
If a `*_syl.txt` or `*_tilde.txt` file is partially written (e.g., process killed
mid-write), the next pipeline stage silently processes the partial file and produces
wrong output. A lightweight format-validation guard at the start of each stage would
improve robustness.

**`sys.path.insert(0, str(_repo_root / "src"))` in every CLI.**
This bootstrapping pattern is necessary for direct-script execution but adds noise. A
`src` layout is already declared in `pyproject.toml`; when installed via `pip install -e .`
the path manipulation is redundant. Consider removing it from installed-package usage via
an `if __name__ == '__main__':` guard or moving it to a single entry-point helper.

---

## 3. Code Quality Assessment

### 3.1 Positive patterns

- **Docstrings are functional**: they specify the purpose, the I/O format, and format
  examples. Not all functions are documented, but the most critical ones are.
- **Module-level constants for character sets**: `AKKADIAN_VOWELS`, `AKKADIAN_CONSONANTS`,
  `SHORT`, `LONG` etc. are defined once and used consistently. Extensibility via
  `--extra-vowels` / `--extra-consonants` is well-designed.
- **`_cli_common.py` reduces boilerplate**: `RawDefaultsHelpFormatter`,
  `print_startup_banner()`, and `add_standard_version_argument()` prevent repetition
  across seven CLI modules.
- **`AccentStyle` enum in `prosody.py`**: using an enum for `LOB` / `SOB` is the correct
  approach; it prevents magic-string bugs and gives IDE type checking a foothold.
- **`run_tests()` convention**: every module defines `run_tests() -> bool` returning
  `True`/`False` and printing per-case `PASS`/`FAIL`. This is a simple, portable
  self-test convention that works in any environment, including without pytest.
- **`CHANGELOG.md` is maintained**: the project keeps a clear record of what changed
  between v1.0.0 and v1.0.1, including breaking changes.

### 3.2 Issues and Gaps

**Known test regression: syllabifier diphthong separator.**
`tests/test_selftests_cli.py` marks `syllabifier --test` and `fullprosmaker --test-all`
as `xfail` due to a "known diphthong-separator regression in syllabify self-tests".
This means the tests are bypassed rather than fixed. The regression should be diagnosed
and resolved; an `xfail` in a correctness-sensitive module is a technical debt item.
Status: **open / should be prioritized**.

**CR-004 (accentuation rename) is approved but not fully implemented.**
Multiple places in the codebase still use `repair` / `repaired` / `repairs` in internal
variable names, JSON/CSV keys, and output labels. The ADR-023 decision to rename is the
right one. Until CR-004 is complete, external consumers parsing JSON/CSV output will
see inconsistent terminology depending on which module produces the output.

**No end-to-end integration test.**
There is no `tests/test_integration.py` or similar that runs the full pipeline
(`atfparser → syllabifier → prosmaker → metricalc → printer`) on a small sample and
asserts expected metric values. The built-in self-tests validate individual stages, but
a cross-stage regression would go undetected until the user notices wrong output.
Recommended: add at least one gold-standard regression test using a short excerpt
(e.g., 5 lines from Erra and Išum) with pinned expected VarcoC and accentuation rate.

**`phoneprep.py` self-test coverage is unclear.**
The `--test` flag exists and is invoked in the pytest suite, but it is not clear from the
code scan what cases are covered. Given the complexity of the coverage optimizer, a
richer test of coverage targets vs. achieved coverage would be valuable.

**Colored vowels in `phoneprep.py` are not part of the main Akkadian inventory.**
The `phoneprep.py` module defines `COLORED_VOWELS_SHORT = ['ɑ', 'ɨ', 'ʊ', 'ɛ']`
alongside the standard vowels. The relationship between these colored vowels and the
post-emphatic vowel coloring in IPA output is not documented in the CLI or in a spec.
A brief note on what colored vowels represent physiologically and how they are used in
MBROLA synthesis would clarify intent.

**`_gen_diphthongs.py` in the lib folder is not a production module.**
The leading underscore indicates it is a generator/utility, but its exact purpose and
whether it is included in the package build is not immediately clear. A short module
docstring would suffice.

---

## 4. Documentation Assessment

### 4.1 Strengths

- **`docs/akkapros/` is comprehensive and current.** Each CLI has its own `.md` file with
  purpose, options table, usage examples, and output file descriptions. The format is
  consistent across all modules. This is publication-quality technical documentation.
- **`docs/akkapros/prosody-realization-algorithm.md` is exemplary.** It explains the
  bimoraic principle, syllable typology, legal operations, accent hierarchies, merge logic,
  and diphthong processing with enough precision that an implementer could re-implement
  from scratch. Few academic tools achieve this level of algorithmic transparency.
- **`docs/internal/adr/`** contains 24 ADRs with consistent structure (status, problem,
  decision, pros/cons, consequences, links). This is an unusually mature practice for a
  solo academic project.
- **`CITATION.cff`** with DOI and ORCID enables proper academic citation.
- **`CONTRIBUTING.md`, `SUPPORT.md`, `CODE_OF_CONDUCT.md`** are all present; the project
  is community-ready even at v1.0.x.

### 4.2 Gaps

**`docs/internal/specs/` was empty before this review.**
The specs folder now contains 10 REQ documents (created as part of this review task).
Going forward, specs should be written *before* implementation for new features, as
recommended in `docs/internal/README.md`.

**The XAR circumflex memory forms are described but not formally specified.**
`docs/akkapros/xar-script.md` explains the two-vowel encoding rationale, but the exact
table of all circumflex → XAR correspondences is not pinned in a spec or test. If the
encoding changes, there is no automated check.

**`docs/akkapros/diphthong-processing.md`** (listed in CHANGELOG) — to be verified that
it exists and is current given the known diphthong-separator regression.

**`docs/internal/cr/index.md`** should be kept up to date as CRs are added.
At the time of this review, CR-005 (change bracket escapes to double braces) appears in
the folder but its status in the index should be verified after implementation.

---

## 5. Research Hypothesis Assessment

The phonological research model is coherent and the implementation follows from it
faithfully. Key observations:

**The core insight is well-supported by the data.**
- Original corpus VarcoC = 69.09 sits in the overlap zone between English (70–80) and
  Dutch (68–78). It is decisively above the syllable-timed range (50–55) and far above
  the mora-timed range (~37). The classification as stress-timed is robust.
- The 19.1% accentuation rate is emergent (not calibrated), which is methodologically
  honest. It falls within the 15–20% range expected for stress-timed prominence.
- The Arabic comparative evidence (research note 038) provides independent cross-linguistic
  support for the stress-timed classification of a Semitic language.

**The model's limitations are acknowledged.**
- The toolkit correctly represents VarcoC as evidence of *compatibility* with stress-timing,
  not proof of historical reconstruction.
- Sensitivity analysis (two CVVC hypotheses yielding < 0.1 VarcoC difference) demonstrates
  methodological robustness.
- The pause-ratio correction (35%) is a choice: the toolkit is transparent about this and
  exposes `--pause-ratio` for sensitivity testing.

**One analytical gap.**
The research notes discuss the "84% red herring" (note 028) — the error of counting
stressed words rather than stressed syllables. The corrected proportion (29.2%) is cited in
the notes but its role in motivating the merge algorithm could be made more explicit in the
algorithm documentation. A stress-eligibility rate of 29% is the *before-merge* baseline;
the toolkit brings this down to ~13.6% accentuated syllables by choosing one target per
prosodic unit, not per word. This reduction is the toolkit's main rhythmic contribution
and deserves a prominent one-paragraph explanation in the algorithm docs.

---

## 6. Process and Engineering Practices

| Practice | Assessment |
|----------|------------|
| Semantic versioning | ✓ Followed; v1.0.0 → v1.0.1 correctly a patch release |
| ADR discipline | ✓ 24 ADRs, all accepted, consistently structured |
| CR process | ✓ 5 CRs, linked to ADRs, with acceptance criteria |
| CHANGELOG | ✓ Maintained per Keep-a-Changelog |
| Built-in self-tests | ✓ Every CLI module has `--test`; pytest delegates to them |
| CLI/lib separation | ✓ Followed for 6 of 7 CLIs; `phoneprep.py` is the exception |
| Unicode discipline | ✓ UTF-8 everywhere; `.gitattributes` enforces line endings |
| No runtime dependencies | ✓ Pure Python; zero PyPI deps for production use |
| Test regression (`syllabifier --test`) | ✗ Marked `xfail`; should be resolved |
| CR-004 rename | ✗ Approved but incomplete; terminology inconsistency in outputs |
| End-to-end integration test | ✗ Missing; would catch cross-stage regressions |
| `phoneprep.py` lib separation | ✗ Monolithic; deviates from ADR-001 |
| Specs folder | was empty before this review; now populated |

---

## 7. Recommendations (Priority Order)

### High Priority

1. **Fix the syllabifier diphthong-separator regression** (`xfail` in `test_selftests_cli.py`).
   Identify which test case(s) fail, add them explicitly to the suite as known-failing,
   then fix the root cause in `syllabify.py`. This is the most important correctness item.

2. **Complete CR-004** (accentuation terminology rename). The approved ADR-023 decision
   is correct. Execute the mechanical rename: update all JSON/CSV keys, table headings,
   variable names, and documentation.

3. **Add an end-to-end integration test** with a pinned small-corpus gold standard
   (expected VarcoC, accentuation rate, and a sample line of `_tilde.txt` output).
   Place it in `tests/test_integration.py`.

### Medium Priority

4. **Remove duplicated `simple_safe_filename()` from `cli/prosmaker.py` and
   `cli/metricalc.py`**: import from `lib/utils.py`.

5. **Extract `phoneprep.py` core logic to `lib/phoneprep.py`** in a future minor release
   to align with ADR-001.

6. **Document the relationship between colored vowels (`ɑ ɨ ʊ ɛ`) and IPA post-emphatic
   coloring** in `phoneprep.py` and `printer.md`.

### Low Priority

7. **Add a module docstring to `lib/_gen_diphthongs.py`** explaining its scope and
   whether it is intended for use by external callers.

8. **Expand the algorithm documentation** with a one-paragraph explanation of the
   stress-eligibility rate (29% before merge → 13.6% after accentuation) to make the
   toolkit's main rhythmic contribution explicit.

9. **Add a format-validation guard** at the start of `prosmaker.py` and `metricalc.py`
   to detect and report obviously partial/corrupted input files.

10. **Verify and update `docs/akkapros/diphthong-processing.md`** for consistency with
    the current two-phase split/restore implementation.

---

## 8. Summary Verdict

**akkapros v1.0.1 is a high-quality, well-maintained academic toolkit.**
The architecture is sound, the documentation is excellent, and the research model is
transparent and reproducible. The project demonstrates a level of software engineering
discipline (ADR/CR workflow, semantic versioning, built-in tests, no runtime dependencies)
that is uncommon in computational humanities tools.

The two open items that should be resolved before claiming "stable" status are:
- the syllabifier `xfail` regression
- completion of the CR-004 accentuation rename

Everything else is either already handled well or a minor forward-improvement opportunity.

---

*This review was prepared by scanning all Python source files, all documentation under
`docs/`, the ADR and CR folders, and the research notes in `tmp/research-notes.md`
(used for context only; not part of the MIT-licensed codebase).*
