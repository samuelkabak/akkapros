#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Format Converter
Version: 1.0.0

Converts .tilde files to multiple output formats:
- IPA (International Phonetic Alphabet) for speech synthesis
- Markdown with bold repaired syllables for publications
- LaTeX with \\textbf{} for academic papers

Input:  *_tilde.txt (pivot format with spaces, _, ~)
Output: *_ipa.txt, *_md.txt, *_tex.tex
"""

import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

__version__ = "1.0.0"


# ------------------------------------------------------------
# IPA consonant mapping
# ------------------------------------------------------------
IPA_MAP = {
    # Consonants
    'b': 'b', 'd': 'd', 'g': 'g', 'k': 'k', 'p': 'p',
    'q': 'q', 'ṭ': 'tˤ', 'ṣ': 'sˤ', 'š': 'ʃ',
    's': 's', 'z': 'z', 'l': 'l', 'm': 'm', 'n': 'n',
    'r': 'r', 'ḥ': 'ħ', 'ḫ': 'χ', 'ʿ': 'ʕ', 'ʾ': 'ʔ',
    'w': 'w', 'y': 'j', 't': 't',
    
    # Glottal stop (already mapped)
    'ʔ': 'ʔ',
    
    # Length marker
    ':': 'ː',
    
    # Vowels will be handled by separate logic
}


def apply_ipa_vowel(v: str) -> str:
    """
    Convert Akkadian vowel to IPA.
    Handles short, long, and extra-long vowels.
    """
    # Short vowels
    if v == 'a': return 'a'
    if v == 'i': return 'i'
    if v == 'u': return 'u'
    if v == 'e': return 'e'
    
    # Long vowels (macron)
    if v == 'ā': return 'aː'
    if v == 'ī': return 'iː'
    if v == 'ū': return 'uː'
    if v == 'ē': return 'eː'
    
    # Long vowels (circumflex)
    if v == 'â': return 'aː'
    if v == 'î': return 'iː'
    if v == 'û': return 'uː'
    if v == 'ê': return 'eː'
    
    # Extra-long vowels (grave)
    if v == 'à': return 'aːː'
    if v == 'ì': return 'iːː'
    if v == 'ù': return 'uːː'
    if v == 'è': return 'eːː'
    
    return v


def tilde_to_ipa_line(line: str) -> str:
    """
    Convert a line from .tilde format to IPA.
    
    Rules:
    - Syllable boundaries (.) are removed
    - Repaired syllables get ˈ before them
    - ~ becomes ː (length marker)
    - Words merged with _ become connected with +
    - Spaces become word boundaries
    - Line breaks preserved, with (.) pause markers
    """
    result = []
    words = line.split()
    
    for word_idx, word in enumerate(words):
        if '_' in word:
            # Handle merged words
            parts = word.split('_')
            for i, part in enumerate(parts):
                result.append(word_to_ipa(part, is_merged=True))
                if i < len(parts) - 1:
                    result.append('+')
        else:
            result.append(word_to_ipa(word, is_merged=False))
        
        if word_idx < len(words) - 1:
            result.append(' ')
    
    return ''.join(result)


def word_to_ipa(word: str, is_merged: bool = False) -> str:
    """
    Convert a single word to IPA.
    
    Args:
        word: Word in .tilde format (may contain . for syllable boundaries)
        is_merged: Whether this word is part of a merged group
    """
    # Split into syllables
    syllables = word.split('.')
    result = []
    
    for syl in syllables:
        if not syl:
            continue
        
        # Check if this syllable is repaired (contains ː or extra-long vowel)
        is_repaired = 'ː' in syl or any(v in 'àìùè' for v in syl)
        
        if is_repaired:
            result.append('ˈ')
        
        # Convert each character
        for c in syl:
            if c in IPA_MAP:
                result.append(IPA_MAP[c])
            elif c in 'aeiuāēīūâêîûàìùè':
                result.append(apply_ipa_vowel(c))
            else:
                result.append(c)
    
    return ''.join(result)


def tilde_to_markdown_line(line: str) -> str:
    """
    Convert a line from .tilde format to Markdown with bold repairs.
    
    Rules:
    - Repaired syllables are wrapped in ** **
    - Words merged with _ become connected with ‿ (U+203F)
    - Spaces become spaces
    - Line breaks preserved with periods
    """
    result = []
    words = line.split()
    
    for word_idx, word in enumerate(words):
        if '_' in word:
            parts = word.split('_')
            for i, part in enumerate(parts):
                result.append(word_to_markdown(part))
                if i < len(parts) - 1:
                    result.append('‿')
        else:
            result.append(word_to_markdown(word))
        
        if word_idx < len(words) - 1:
            result.append(' ')
    
    return ''.join(result)


def word_to_markdown(word: str) -> str:
    """
    Convert a single word to Markdown with bold repairs.
    """
    syllables = word.split('.')
    result = []
    
    for syl in syllables:
        if not syl:
            continue
        
        # Check if this syllable is repaired (contains ː or extra-long vowel)
        is_repaired = 'ː' in syl or any(v in 'àìùè' for v in syl)
        
        if is_repaired:
            result.append(f'**{syl}**')
        else:
            result.append(syl)
    
    return ''.join(result)


def tilde_to_latex_line(line: str) -> str:
    """
    Convert a line from .tilde format to LaTeX with \\textbf{}.
    
    Rules:
    - Repaired syllables are wrapped in \\textbf{}
    - Words merged with _ become connected with ‿ (U+203F)
    - Spaces become spaces
    - Line breaks preserved with periods
    """
    result = []
    words = line.split()
    
    for word_idx, word in enumerate(words):
        if '_' in word:
            parts = word.split('_')
            for i, part in enumerate(parts):
                result.append(word_to_latex(part))
                if i < len(parts) - 1:
                    result.append('‿')
        else:
            result.append(word_to_latex(word))
        
        if word_idx < len(words) - 1:
            result.append(' ')
    
    return ''.join(result)


def word_to_latex(word: str) -> str:
    """
    Convert a single word to LaTeX with \\textbf{}.
    """
    syllables = word.split('.')
    result = []
    
    for syl in syllables:
        if not syl:
            continue
        
        # Check if this syllable is repaired (contains ː or extra-long vowel)
        is_repaired = 'ː' in syl or any(v in 'àìùè' for v in syl)
        
        if is_repaired:
            result.append(f'\\textbf{{{syl}}}')
        else:
            result.append(syl)
    
    return ''.join(result)


def process_file(input_file: str, output_prefix: str, outdir: Path, 
                 formats: List[str], wpm: float = 165, pause_ratio: float = 35):
    """
    Process a .tilde file and generate requested outputs.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Prepare output lines for each format
    ipa_lines = []
    md_lines = []
    tex_lines = []
    
    for line in lines:
        line = line.rstrip('\n')
        
        if not line.strip():
            # Empty line = paragraph break
            if 'ipa' in formats:
                ipa_lines.append('(.)')
            if 'md' in formats:
                md_lines.append('')
            if 'tex' in formats:
                tex_lines.append('')
            continue
        
        if 'ipa' in formats:
            ipa_line = tilde_to_ipa_line(line)
            ipa_lines.append(f'[{ipa_line}] (.)')
        
        if 'md' in formats:
            md_line = tilde_to_markdown_line(line)
            md_lines.append(md_line + '.')
        
        if 'tex' in formats:
            tex_line = tilde_to_latex_line(line)
            tex_lines.append(tex_line + '.')
    
    # Write output files
    if 'ipa' in formats:
        ipa_file = outdir / f"{output_prefix}_ipa.txt"
        with open(ipa_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(ipa_lines))
        print(f"IPA saved to: {ipa_file}")
    
    if 'md' in formats:
        md_file = outdir / f"{output_prefix}_md.txt"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        print(f"Markdown saved to: {md_file}")
    
    if 'tex' in formats:
        tex_file = outdir / f"{output_prefix}_tex.tex"
        with open(tex_file, 'w', encoding='utf-8') as f:
            # Add minimal LaTeX preamble
            f.write(r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{tipa}
\begin{document}

""")
            f.write('\n'.join(tex_lines))
            f.write(r"""

\end{document}""")
        print(f"LaTeX saved to: {tex_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert .tilde files to IPA, Markdown, and LaTeX formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
EXAMPLES:
  python format.py erra_tilde.txt -o erra --ipa --md --tex
  python format.py erra_tilde.txt -o erra --ipa
  python format.py --input-list files.txt --ipa --md

OUTPUT FORMATS:
  --ipa   IPA notation with stress (ˈ) and length (ː)
  --md    Markdown with **bold** repaired syllables
  --tex   LaTeX with \\textbf{{}} repaired syllables

Version {__version__}
"""
    )
    parser.add_argument('--version', action='version',
                       version=f'akkapros-format {__version__}')
    parser.add_argument('input', nargs='?', help='Input *_tilde.txt file')
    parser.add_argument('--input-list', help='File containing list of input files')
    parser.add_argument('-o', '--output', default='output', help='Output prefix')
    parser.add_argument('--outdir', default='.', help='Output directory')
    parser.add_argument('--ipa', action='store_true', help='Generate IPA output')
    parser.add_argument('--md', action='store_true', help='Generate Markdown output')
    parser.add_argument('--tex', action='store_true', help='Generate LaTeX output')
    parser.add_argument('--wpm', type=float, default=165, help='Words per minute for speech rate (default: 165)')
    parser.add_argument('--pause-ratio', type=float, default=35, help='Pause ratio percentage (default: 35)')
    
    args = parser.parse_args()
    
    # Determine which formats to generate
    formats = []
    if args.ipa:
        formats.append('ipa')
    if args.md:
        formats.append('md')
    if args.tex:
        formats.append('tex')
    
    if not formats:
        print("Error: No output format specified. Use --ipa, --md, and/or --tex")
        sys.exit(1)
    
    # Collect input files
    input_files = []
    if args.input_list:
        with open(args.input_list, 'r', encoding='utf-8') as f:
            input_files = [line.strip() for line in f if line.strip()]
    elif args.input:
        input_files = [args.input]
    else:
        parser.print_help()
        sys.exit(1)
    
    # Verify files exist
    for f in input_files:
        if not Path(f).exists():
            print(f"Error: File not found: {f}")
            sys.exit(1)
    
    # Create output directory
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    # Process each file
    for input_file in input_files:
        print(f"\nProcessing: {input_file}")
        
        # Use input filename as base if multiple files, otherwise use specified output
        if len(input_files) > 1:
            stem = Path(input_file).stem
            output_prefix = stem.replace('_tilde', '')
        else:
            output_prefix = args.output
        
        process_file(input_file, output_prefix, outdir, formats, 
                    args.wpm, args.pause_ratio)


if __name__ == "__main__":
    main()