# Akkadian Prosody Toolkit (akkapros)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![DOI](https://zenodo.org/badge/1158133867.svg)](https://doi.org/10.5281/zenodo.19010721)
[![GitHub release](https://img.shields.io/github/v/release/samuelkabak/akkapros)](https://github.com/samuelkabak/akkapros/releases)
[![Documentation](https://img.shields.io/badge/docs-latest-green.svg)](docs/GETTING_STARTED.md)
[![Tests](https://img.shields.io/badge/tests-375%20passing-brightgreen.svg)](https://github.com/samuelkabak/akkapros)

> **Making Akkadian sound like language again.**  
> A computational toolkit for reconstructing Babylonian prosody from cuneiform
> transcriptions — from syllabification through prosodic realization to
> speech-synthesis-ready output.

---

## 🌟 Overview

Akkadian, the world's oldest attested Semitic language, is read today in
isolation — word by word, sign by sign. But no language is spoken that way.
**akkapros** bridges the gap between lexical stress rules and connected-speech
realization through a novel, testable algorithm that reconstructs how a
Babylonian scribe might have actually recited a literary text.

The pipeline transforms an ATF (ASCII Transliteration Format) transcription
through five stages:

```
ATF Input → Parse → Syllabify → Prosody → Metrics → Format/Phonetize
```

Developed for Assyriologists, historical linguists, and digital humanities
researchers working with Akkadian literary texts. Fully reproducible,
configurable, and validated on a 4,917-word corpus.

---

## ✨ Key Features

| Area | Capabilities |
|------|--------------|
| **🔤 Syllabification** | Converts cleaned Akkadian text to syllabified format following Huehnergard (2011) conventions |
| **🎵 Prosody Realization** | Two accent styles — LOB (Literary Old Babylonian) and SOB (Standard Old Babylonian) — with moraic algorithm for stress assignment |
| **📊 Metrics** | Interval-based metrics from phone/ophone pairs: %V, %C, ΔC, ΔV, VarcoC, VarcoV, rPVI-C, nPVI-V, speech rate (WPM), pause ratio, articulation duration |
| **🔊 Phonetizer** | Full phoneme framework with MBROLA/X-SAMPA `.pho` output, duration modeling, intonation contours, pause typing, and drift tracking |
| **📝 Multiple Outputs** | Acute, bold (Markdown), IPA, XAR practical orthography, and MBROLA-ready formats |
| **⚙️ Configurable** | Package-wide YAML configuration with `--conf`/`--option` CLI, `confwriter` for config management |
| **🧪 Reproducible** | 375+ tests, built-in CLI test suites, demo scripts, and full pipeline validation on a 4,917-word corpus |

---

## 🚀 Quick Start

### Install

```bash
pip install akkapros
```

### Run on a Sample Text

```bash
python -m akkapros.cli.fullprosmaker data/samples/L_I.2_Poem_of_Creation_SB_II.atf -p demo --outdir outputs
```

### What You Get

| Output | Description |
|--------|-------------|
| `demo_syl.txt` | Syllabified text with syllable boundaries |
| `demo_tilde.txt` | Prosody-realized pivot format with stress markers |
| `demo_phone.txt` | Canonical phone-row artifact for the phonetize stage |
| `demo_ophone.txt` | Original (non-accentuated) phone-row artifact |
| `demo_metrics.txt` | Human-readable metrics table with speech/pause timing |
| `demo_accent_bold.md` | Bold-marked text for visual inspection of stress placement |

See [Getting Started](docs/GETTING_STARTED.md) for detailed instructions.

---

## 🔬 The Problem It Solves

Babylonian literary texts were composed and performed orally, but the
cuneiform writing system records only consonants and some vowels — not stress,
intonation, or rhythm. Modern readers face fundamental questions:

- **Which syllable was stressed?** Lexical stress rules exist (Huehnergard
  2011; Streck 2022), but they apply to isolated words, not connected speech.
- **How did words merge in recitation?** Akkadian poetry shows prosodic
  merging (sandhi), but the rules are implicit in the meter.
- **What did it sound like?** Without a testable model, reconstructions remain
  speculative.

**akkapros** answers these questions with an explicit, algorithmic model:

1. **Syllabify** the text following standard Assyriological conventions
2. **Assign stress** using a moraic algorithm with two accent styles
3. **Model prosodic merging** of words in connected speech
4. **Generate phone-level realizations** with duration, intonation, and pauses
5. **Compute rhythmic metrics** (VarcoC, %V, ΔC, etc.) to characterize the
   resulting speech rhythm

The result is a fully reproducible pipeline that turns a cuneiform
transcription into something that can be heard — and measured.

---

## 📊 Validation

Validated on a corpus of **4,917 words** from Standard Babylonian literary
texts:

- Enūma Eliš (tablets II, IV, VI, VII)
- Erra and Išum (tablet I)
- Marduk's Address to the Demons

| Metric | Original | Realized |
|--------|----------|----------|
| VarcoC | 69.09 | 70.67 |
| Prominence rate | — | 13.63% |
| Words merged | — | 49.9% |

All results are fully reproducible using the included demo scripts.

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/GETTING_STARTED.md) | Run the pipeline on a sample file |
| [Configuration](docs/akkapros/configuration.md) | Shared YAML config, effective runtime config, `--conf`, `--option`, and `confwriter` |
| [CLI Reference](docs/akkapros/) | Detailed documentation for each tool |
| [Algorithm](docs/akkapros/prosody-realization-algorithm.md) | How the prosody realization works |
| [Metrics](docs/akkapros/metrics-computation.md) | Full explanation of all computed metrics |
| [Phonetizer](docs/akkapros/phonetizer.md) | Phone realization, duration modeling, intonation, and MBROLA export |
| [XAR Script](docs/akkapros/xar-script.md) | Practical reading orthography for Akkadian |
| [Release Strategy](docs/akkapros/release-strategy.md) | Versioning and release procedures |
| [Release Notes](release-notes/v3.0.1.md) | Current release summary and upgrade notes |
| [ADR Index](docs/internal/adr/index.md) | Architecture Decision Records |
| [CR Index](docs/internal/cr/index.md) | Change Request records |
| [Req Index](docs/internal/req/index.md) | Requirements and short specifications |

### Escape Syntax

The pipeline preserves escaped non-Akkadian chunks using:

- `{{text}}` — plain escape
- `{tag{text}}` — tagged escape (`tag` matches `[0-9a-z_]{1,16}`)

Internal tags begin with `_` and are reserved for pipeline-internal behavior.
Nested escape blocks are intentionally unsupported.

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run built-in CLI tests
python -m akkapros.cli.fullprosmaker --test-all
```

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for
guidelines.

- Report bugs via [Issues](https://github.com/samuelkabak/akkapros/issues)
- Suggest features via
  [Discussions](https://github.com/samuelkabak/akkapros/discussions)
- Read our [Code of Conduct](CODE_OF_CONDUCT.md)

---

## 📄 License

MIT © Samuel Kabak (ORCID: 0000-0001-7976-5038)

---

## 📬 Citation

If you use akkapros in your research, please cite:

```bibtex
@software{kabak2026akkapros,
  author       = {Kabak, Samuel},
  title        = {akkapros: Akkadian Prosody Reconstruction Toolkit},
  year         = 2026,
  publisher    = {Zenodo},
  version      = {3.0.1},
  doi          = {10.5281/zenodo.19010721},
  url          = {https://github.com/samuelkabak/akkapros}
}
```

---

## 🙏 Acknowledgments

- [Electronic Babylonian Library (eBL)](https://www.ebl.lmu.de/) at LMU Munich
  for open-access transcriptions
- John Huehnergard and Michael Streck for foundational scholarship on Akkadian
  prosody
- The open-source community for tools and inspiration

---

*🏛️ Making Akkadian sound like language again.*
