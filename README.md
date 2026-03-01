# Akkadian Prosody Toolkit (akkapros)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A computational toolkit for reconstructing Babylonian accentuation. Processes phonological texts, applies a novel accentuation repair algorithm, computes acoustic metrics (VarcoC, ΔC, %V), and generates publication-ready output in multiple formats.

Developed for Assyriologists, historical linguists, and digital humanities researchers working with Akkadian literary texts.

---

## 📋 Overview

The Akkadian Prosody Toolkit addresses a fundamental problem in Assyriology: the standard moraic stress model describes *where* accent *could* fall, but not *how* it was realized in connected speech. This toolkit implements a computational solution:

1. **Parse** ATF files from the electronic Babylonian Library (eBL)
2. **Syllabify** according to standard Akkadian rules
3. **Repair** accentuation patterns using a phrase-level algorithm
4. **Compute** acoustic metrics (%V, ΔC, VarcoC)
5. **Generate** outputs for publication and speech synthesis

---

## 🔧 Tools Included

| Program | Version | Description |
|---------|---------|-------------|
| `atfparser.py` | 1.0.0 | Converts eBL ATF files to clean phonological text |
| `syllabify.py` | 1.0.0 | Syllabifies Akkadian text following Huehnergard (2011) |
| `repairer.py` | 1.0.0 | Applies accentuation repair algorithm |
| `metricser.py` | 1.0.0 | Computes acoustic metrics from repaired text |
| `format.py` | 1.0.0 | Generates Markdown, LaTeX, and IPA output |

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/samuelkabak/akkapros.git
cd akkapros

# Process an ATF file
python3 src/atfparser.py texts/erra.atf -p erra --outdir outputs

# Syllabify and repair
python3 src/repairer.py erra_proc.txt -p erra --outdir outputs

# Compute metrics
python3 src/akkapros/cli/metricser.py erra.tilde > erra_metrics.txt

# Generate publication outputs
python3 src/format.py erra.tilde --md --tex --ipa
