# akkapros: Computational Akkadian Prosody Reconstruction

**A Research Showcase**

Samuel Kabak | ORCID: 0000-0001-7976-5038 | March 2026

---

## 🎯 The Research Problem

The standard model of Akkadian stress (Huehnergard 2011; Streck 2022) provides rules for lexical stress—where stress *could* fall in isolated words. However, it offers **no mechanism for phrasal timing** in connected speech.

Stress-timed languages like English require stressed syllables at roughly equal intervals, with unstressed material compressing or expanding between them. Fixed lexical stress positions cannot produce this effect alone.

**The question:** If Akkadian were realized as a stress-timed language (as its phonological structure suggests), what mechanism would connect lexical rules to phrasal realization?

---

## 🔬 The Solution: A Testable Algorithm

`akkapros` implements a **prosody realization algorithm** that:

1. Takes syllabified Akkadian text as input
2. Identifies stress-eligible syllables using LOB/SOB hierarchies
3. Adds exactly one mora to selected syllables through:
   - Vowel lengthening (CVV → CVV~)
   - Consonant gemination (CVC → CVC~)
4. Merges words prosodically when they cannot be realized alone
5. Outputs multiple formats for analysis and publication

### Core Principle: Bimoraic Alignment

Each prosodic unit should contain an even number of morae. This principle extends cross-linguistic observations about prosodic minimality (Hayes 1995) to the phrasal level.

---

## 📊 Validation Results

### Corpus (4,917 words, 14,684 syllables)

| Text | Source |
|------|--------|
| Enūma Eliš (tablets II, IV, VI, VII) | Lambert 2013 |
| Erra and Išum (tablet I) | Cagni 1969 |
| Marduk's Address to the Demons | Lambert 1999 |

### Key Metrics

| Metric | Original | Realized | Interpretation |
|--------|----------|----------|----------------|
| VarcoC | 69.09 | 70.67 | Remains in stress-timed range (cf. English 70–80) |
| %V (35% pauses) | 59.18% | 55.14% | Moves closer to English range (40–45%) |
| Prominence rate | — | 13.63% | Emerges from data, not design |
| Words merged | — | 49.9% | Extensive prosodic restructuring |
| Average merged unit | — | 2.21 words | Mostly binary mergers |

### Pause Correction

Short pauses are corrected to the nearest multiple of 2 morae, aligning them with the bimoraic rhythm:

| Pause Ratio | Initial Short | Corrected Short | Adjustment |
|-------------|---------------|-----------------|------------|
| 30% | 0.179 s | 0.206 s | +0.027 s |
| 35% | 0.209 s | 0.191 s | -0.018 s |
| 40% | 0.239 s | 0.235 s | -0.004 s |

Long pauses adjust to preserve total pause time, resulting in corrected long:short ratios clustering around 2:1.

---

## 🏛️ Implications for Assyriology

### 1. The Candidate Set Model

The standard stress rules describe **where stress could go**. The algorithm demonstrates that a coherent rhythmic system *can* be built from these rules—suggesting they describe eligibility, not realization.

### 2. Plene Spelling Recontextualized

If plene spellings sometimes mark phonetic prominence rather than lexical length, their inconsistent distribution becomes less puzzling. They may reflect variable realization in different performance contexts.

### 3. A Bridge Between Writing and Speech

For a dead language studied primarily through texts, this model offers a way to think about performance aspects that are otherwise inaccessible.

---

## 🔧 Technical Capabilities

### Input Processing

| Stage | Tool | Output |
|-------|------|--------|
| ATF parsing | `atfparser.py` | Clean phonological text |
| Syllabification | `syllabifier.py` | `*_syl.txt` with boundaries |
| Prosody realization | `prosmaker.py` | `*_tilde.txt` pivot format |
| Metrics | `metricalc.py` | Tables, JSON, CSV |
| Formatting | `printer.py` | Multiple reading formats |

### Output Formats

| Format | Use Case | Example |
|--------|----------|---------|
| Acute (`*_accent_acute.txt`) | Compact scholarly notation | `tāḫā´za ik´taṣar` |
| Bold (`*_accent_bold.md`) | Visual inspection | `tā**ḫā**za **ik**taṣar` |
| IPA (`*_accent_ipa.txt`) | Phonetic analysis | `taː.ˈχaːː.za.ˈʔikː.ta.sˤɑr` |
| XAR (`*_accent_xar.txt`) | Practical reading | `taaḫaaza iktaɉàr` |
| MBROLA (`*_accent_mbrola.txt`) | Speech synthesis | X-SAMPA format |

### IPA Features

- Post-emphatic vowel coloring (`a` → `ɑ` after `q`, `ṣ`, `ṭ`)
- Configurable pharyngeal mapping (Old Akkadian vs. Old Babylonian)
- Speculative circumflex hiatus mode (`qû` → `qʊ.ʊ`)

### XAR Practical Orthography

XAR is a reader-oriented script designed for:

| Feature | Implementation |
|---------|----------------|
| Emphatics | Marked family: `ꝗ`, `ꞓ`, `ɉ` |
| Long vowels | Doubled: `aa`, `ii`, `uu`, `ee` |
| Circumflex | Two-vowel memory: `eâ`, `eî`, `iû`, `aê` |
| Emphatic coloring | Grave accents: `à`, `ì`, `ù`, `è` |
| Fallback | Clean ASCII mapping for low-tech contexts |

---

## 🎙️ Speech Synthesis Foundation

`phoneprep.py` generates optimized recording scripts for MBROLA voice creation:

- **878 words** covering three phonotactic patterns
- **Interactive HTML recording assistant** with keyboard controls
- **Machine-readable sidecars** for automatic segmentation
- **Target coverage**: 3 occurrences per diphone

### Recording Workflow

    phoneprep.py → Recording materials → HTML helper → WAVs + event log
         ↓
    Sidecars (manifest, diphones, words)
         ↓
    [Segmenter - planned] → Aligned segments
         ↓
    MBROLATOR → MBROLA voice

---

## 📖 Example: Enūma Eliš Tablet II (Opening)

### Academic Transliteration

    ukappit-ma : tiāmtu pitiqša
    tāḫāza iktaṣar : ana ilī niprīša

### XAR Practical Reading Script

    ukappit-ma : tiaamtu pitiꝗx̌a
    taaḫaaza iktaɉàr : ana ilii nipriix̌a

### IPA (Old Babylonian Profile)

    u.kap.pit-ma ⟨colon⟩ | ˈtiaːːm.tu.pi.tiq.ʃa
    taː.ˈχaːː.za.ˈʔikː.ta.sˤɑr ⟨colon⟩ | ana.i.liː.nip.ˈriːː.ʃa

### English Translation

    Tiamat assembled her creatures,
    Drew up for battle against the gods her brood.

---

## 📚 Documentation

All documentation is available in the [GitHub repository](https://github.com/samuelkabak/akkapros):

- `docs/GETTING_STARTED.md` – Quick start guide
- `docs/akkapros/` – Detailed CLI and algorithm documentation
- `docs/akkapros/prosody-realization-algorithm.md` – Core algorithm
- `docs/akkapros/metrics-computation.md` – Metrics methodology
- `docs/akkapros/xar-script.md` – XAR orthography specification

---

## 🔗 Links

- **Repository**: https://github.com/samuelkabak/akkapros
- **Documentation**: https://github.com/samuelkabak/akkapros/tree/main/docs
- **Issues**: https://github.com/samuelkabak/akkapros/issues
- **DOI**: 10.5281/zenodo.19010721

---

## 📬 Contact

Samuel Kabak  
Independent Researcher  
ORCID: 0000-0001-7976-5038  
GitHub: @samuelkabak

---

## 🙏 Acknowledgments

This work builds on:

- The open-access resources of the **Electronic Babylonian Library (eBL)** at LMU Munich
- The foundational scholarship of **John Huehnergard** and **Michael Streck**
- The open-source community's tools and inspiration

---

*🏛️ Making Akkadian sound like language again.*
