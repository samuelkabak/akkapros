# Akkadian Prosody Toolkit (akkapros)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![DOI](https://zenodo.org/badge/1158133867.svg)](https://doi.org/10.5281/zenodo.19010721)
[![GitHub release](https://img.shields.io/github/v/release/samuelkabak/akkapros)](https://github.com/samuelkabak/akkapros/releases)
[![Documentation](https://img.shields.io/badge/docs-latest-green.svg)](docs/GETTING_STARTED.md)

A computational toolkit for reconstructing Babylonian prosody. Bridges the gap between lexical stress rules (Huehnergard 2011; Streck 2022) and connected speech realization through a novel, testable algorithm.

Developed for Assyriologists, historical linguists, and digital humanities researchers working with Akkadian literary texts.

---

## ✨ Key Features

| Area | Capabilities |
|------|--------------|
| **🔤 Syllabification** | Converts cleaned Akkadian text to syllabified format following standard Assyriological conventions |
| **🎵 Prosody Realization** | Implements LOB (Literary Old Babylonian) and SOB (Standard Old Babylonian) accent styles with moraic algorithm |
| **📊 Metrics** | Computes %V, ΔC, VarcoC, and related rhythmic metrics with configurable pause ratios (30–40%) |
| **📝 Multiple Outputs** | Generates acute, bold (Markdown), IPA, XAR practical orthography, and MBROLA-ready formats |
| **🧪 Reproducible** | Built-in tests, demo scripts, and full pipeline validation on a 4,917-word corpus |

---

## 🚀 Quick Start

### Install

    pip install akkapros

### Run on a Sample Text

    python -m akkapros.cli.fullprosmaker data/samples/L_I.2_Poem_of_Creation_SB_II.atf -p demo --outdir outputs

### What You Get

| Output | Description |
|--------|-------------|
| `demo_syl.txt` | Syllabified text with boundaries |
| `demo_tilde.txt` | Prosody-realized pivot format |
| `demo_metrics.txt` | Human-readable metrics table |
| `demo_accent_bold.md` | Bold-marked text for visual inspection |

See [Getting Started](docs/GETTING_STARTED.md) for detailed instructions.

---

## 📊 Validation

Validated on a corpus of **4,917 words** from Standard Babylonian literary texts:

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
| [CLI Reference](docs/akkapros/) | Detailed documentation for each tool |
| [Algorithm](docs/akkapros/prosody-realization-algorithm.md) | How the prosody realization works |
| [Metrics](docs/akkapros/metrics-computation.md) | Full explanation of all computed metrics |
| [XAR Script](docs/akkapros/xar-script.md) | Practical reading orthography for Akkadian |
| [Release Strategy](docs/akkapros/release-strategy.md) | Versioning and release procedures |

---

## 🧪 Testing

    # Run all tests
    pytest

    # Run built-in CLI tests
    python -m akkapros.cli.fullprosmaker --test-all

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- Report bugs via [Issues](https://github.com/samuelkabak/akkapros/issues)
- Suggest features via [Discussions](https://github.com/samuelkabak/akkapros/discussions)
- Read our [Code of Conduct](CODE_OF_CONDUCT.md)

---

## 📄 License

MIT © Samuel Kabak (ORCID: 0000-0001-7976-5038)

---

## 📬 Citation

If you use akkapros in your research, please cite:

    @software{kabak2026akkapros,
      author       = {Kabak, Samuel},
      title        = {akkapros: Akkadian Prosody Reconstruction Toolkit},
      year         = 2026,
      publisher    = {Zenodo},
      version      = {1.0.1},
      doi          = {10.5281/zenodo.19010721},
      url          = {https://github.com/samuelkabak/akkapros}
    }

---

## 🙏 Acknowledgments

- Electronic Babylonian Library (eBL) at LMU Munich for open-access transcriptions
- John Huehnergard and Michael Streck for foundational scholarship
- The open-source community for tools and inspiration

---

*🏛️ Making Akkadian sound like language again.*