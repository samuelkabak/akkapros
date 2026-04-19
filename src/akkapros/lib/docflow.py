from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from akkapros._gencode import lib_diphthongs as diphthong_generator
from akkapros.cli import fullprosmaker
from akkapros.lib import metrics, phonetize, print as accent_print, prosody, syllabify


ROOT = Path(__file__).resolve().parents[3]


class FlowchartSyncError(ValueError):
    """Raised when a generated user-facing flowchart is out of sync."""


@dataclass(frozen=True)
class FlowchartTarget:
    key: str
    doc_path: str
    validator: Callable[[], None]
    mermaid_lines: tuple[str, ...]

    @property
    def start_marker(self) -> str:
        return f"<!-- GENERATED FLOWCHART: {self.key} -->"

    @property
    def end_marker(self) -> str:
        return f"<!-- END GENERATED FLOWCHART: {self.key} -->"


def _source_text(obj: object) -> str:
    return inspect.getsource(obj)


def _module_text(module: object) -> str:
    module_file = getattr(module, "__file__", None)
    if not module_file:
        raise FlowchartSyncError(f"Module {module!r} has no __file__ for flowchart verification")
    return Path(module_file).read_text(encoding="utf-8")


def _require_fragments_in_order(source: str, fragments: Iterable[str], label: str) -> None:
    position = -1
    for fragment in fragments:
        next_position = source.find(fragment, position + 1)
        if next_position == -1:
            raise FlowchartSyncError(
                f"Flowchart source for {label} is missing required fragment {fragment!r}"
            )
        position = next_position


def _validate_phonetizer_target() -> None:
    stream_source = _source_text(phonetize.realize_phone_streams)
    _require_fragments_in_order(
        stream_source,
        (
            "build_phone_streams(",
            "realize_phone_rows(original_rows",
            "realize_phone_rows(accentuated_rows",
            "realize_row_intonation(original_rows",
            "realize_row_intonation(accentuated_rows",
        ),
        "phonetizer flowchart",
    )

    rows_source = _source_text(phonetize.realize_phone_rows)
    for fragment in ("_pause_duration_and_drift(", "_maybe_insert_mini_pause("):
        if fragment not in rows_source:
            raise FlowchartSyncError(
                f"Flowchart source for phonetizer flowchart is missing required fragment {fragment!r}"
            )


def _validate_phonetizer_phase1_target() -> None:
    build_source = _source_text(phonetize.build_phone_rows)
    _require_fragments_in_order(
        build_source,
        (
            "if symbol == '~':",
            "if symbol in {SYL_SEPARATOR, '.'}:",
            "if symbol == '-':",
            "if symbol in INTERNAL_MERGE_CHARS:",
            "if symbol == WORD_LINKER:",
            "if symbol == ' ':",
            "if symbol == '\\n':",
            "if symbol == OPEN_ESCAPE:",
            "if symbol in short_pause_chars or symbol in long_pause_chars or symbol == '…':",
            "if symbol in INPUT_CHARACTER_LABELS",
            "_resolve_transition_rows(rows)",
        ),
        "phonetizer Phase 1 flowchart",
    )
    finalize_source = _source_text(phonetize._finalize_syllable)
    for fragment in ("row['position'] = 'O' if index < nucleus_index else 'C'", "syllable[-1]['boundary'] = boundary_code"):
        if fragment not in finalize_source:
            raise FlowchartSyncError(
                f"Flowchart source for phonetizer Phase 1 flowchart is missing required fragment {fragment!r}"
            )


def _validate_phonetizer_phase2_target() -> None:
    rows_source = _source_text(phonetize.realize_phone_rows)
    _require_fragments_in_order(
        rows_source,
        (
            "if unit['kind'] == 'pause':",
            "pause_duration, drift_cursor = _pause_duration_and_drift(",
            "for onset_index in analysis['onset_indices']:",
            "for coda_index in analysis['coda_indices']:",
            "durations[nucleus_index] = _vowel_anchor(",
            "if allow_accentuation and analysis['accent_shape'] is not None:",
            "supports_post_accent_cleanup = _supports_post_accent_long_vowel_cleanup(rows, analysis)",
            "if supports_post_accent_cleanup:",
            "elif abs(drift_after_assignment) > tolerance and nucleus_row['length'] == 'L':",
            "if _should_fold_completed_syllable(rows, analysis):",
            "mini_pause = _maybe_insert_mini_pause(",
            "_validate_chrono_checkpoints(",
        ),
        "phonetizer Phase 2 flowchart",
    )


def _validate_phonetizer_hiatus_transition_target() -> None:
    classify_source = _source_text(phonetize._classify_symbol)
    _require_fragments_in_order(
        classify_source,
        (
            "if symbol in CONSONANT_HIATUS:",
            "return 'C', 'H', 'S'",
            "if symbol in CONSONANT_VOWEL_TRANSITION:",
            "return 'C', 'T', 'S'",
        ),
        "phonetizer hiatus/transition flowchart",
    )

    transition_source = _source_text(phonetize._resolve_transition_rows)
    for fragment in (
        "if row['label'] != 'ENA':",
        "_choose_vowel_transition_realization(previous_vowel['realization'], next_vowel['realization'])",
    ):
        if fragment not in transition_source:
            raise FlowchartSyncError(
                f"Flowchart source for phonetizer hiatus/transition flowchart is missing required fragment {fragment!r}"
            )

    timing_source = _source_text(phonetize._consonant_timing_key)
    for fragment in (
        "if row['type'] in {'C', 'H'}:",
        "return 'closure'",
        "if row['type'] in {'S', 'T'}:",
        "return 'sonorant'",
    ):
        if fragment not in timing_source:
            raise FlowchartSyncError(
                f"Flowchart source for phonetizer hiatus/transition flowchart is missing required fragment {fragment!r}"
            )

    anchor_source = _source_text(phonetize._consonant_anchor)
    for fragment in (
        "if row['type'] == 'H':",
        "special_realization']['hiatus']",
        "if row['type'] == 'T':",
        "special_realization']['vowel_transition']",
    ):
        if fragment not in anchor_source:
            raise FlowchartSyncError(
                f"Flowchart source for phonetizer hiatus/transition flowchart is missing required fragment {fragment!r}"
            )

    analyze_source = _source_text(phonetize._analyze_syllable)
    if "accent_shape = 'C:V'" not in analyze_source:
        raise FlowchartSyncError(
            "Flowchart source for phonetizer hiatus/transition flowchart is missing C:V accent-shape handling"
        )

    accent_source = _source_text(phonetize._apply_accent_increment)
    for fragment in (
        "geminate_min = float(consonants_cfg[timing_key]['perception_limits']['geminate_min'])",
        "return min(_consonant_maximum(row, config), geminate_min - 1.0)",
        "return _consonant_maximum(row, config)",
    ):
        if fragment not in accent_source:
            raise FlowchartSyncError(
                f"Flowchart source for phonetizer hiatus/transition flowchart is missing required fragment {fragment!r}"
            )


def _validate_fullprosmaker_target() -> None:
    pipeline_source = _source_text(fullprosmaker.run_pipeline)
    _require_fragments_in_order(
        pipeline_source,
        (
            "syllabify.syllabify_text(",
            "engine.process_file(",
            "realize_phone_streams(",
            "process_metrics_file(",
            "accent_print.process_file(",
        ),
        "fullprosmaker flowchart",
    )


def _validate_diphthong_target() -> None:
    syllabify_source = _source_text(syllabify.preprocess_diphthongs)
    for fragment in ("DIPH_SEPARATOR", "re.sub(vowels_pattern"):
        if fragment not in syllabify_source:
            raise FlowchartSyncError(
                f"Flowchart source for diphthong flowchart is missing required fragment {fragment!r}"
            )

    generator_source = _source_text(diphthong_generator.generate_diphthongs_file)
    for fragment in ("_build_entries()", "_combine_entries(entries)"):
        if fragment not in generator_source:
            raise FlowchartSyncError(
                f"Flowchart source for diphthong flowchart is missing required fragment {fragment!r}"
            )

    restore_source = _source_text(prosody.postprocess_restore_diphthongs)
    if "ALL_REPLACEMENTS" not in restore_source:
        raise FlowchartSyncError(
            "Flowchart source for diphthong flowchart is missing runtime replacement-table usage"
        )

    print_source = _module_text(accent_print)
    for fragment in ("char == DIPH_SEPARATOR", "char == HIATUS_MARKER"):
        if fragment not in print_source:
            raise FlowchartSyncError(
                f"Flowchart source for diphthong flowchart is missing required fragment {fragment!r}"
            )


def _validate_metrics_target() -> None:
    process_source = _source_text(metrics.process_phone_pair)
    _require_fragments_in_order(
        process_source,
        (
            "_load_phone_rows(ophone_filename)",
            "_load_phone_rows(phone_filename)",
            "compute_speech_metrics_from_rows(ophone_rows",
            "compute_speech_metrics_from_rows(phone_rows",
            "compute_interval_metrics(ophone_rows)",
            "compute_interval_metrics(phone_rows)",
        ),
        "metrics flowchart",
    )

    interval_source = _source_text(metrics.compute_interval_metrics)
    _require_fragments_in_order(
        interval_source,
        (
            "intervals = _coalesce_intervals(rows)",
            "vocalic = [duration for interval_class, duration in intervals if interval_class == 'V']",
            "consonantal = [duration for interval_class, duration in intervals if interval_class == 'C']",
            "pauses = [duration for interval_class, duration in intervals if interval_class == 'P']",
        ),
        "metrics flowchart",
    )


FLOWCHART_TARGETS: tuple[FlowchartTarget, ...] = (
    FlowchartTarget(
        key="phonetizer-algorithm",
        doc_path="docs/akkapros/phonetizer-algorithm.md",
        validator=_validate_phonetizer_target,
        mermaid_lines=(
            "flowchart TD",
            "    A[\"_tilde.txt input\"] --> B[\"Build paired row streams\\nderive original, keep accentuated\"]",
            "    B --> C{\"Phase 1 scan current symbol\"}",
            "    C -->|\"segment glyph\"| D[\"Seed a segment row\\nappend to current syllable\"]",
            "    C -->|\"accent mark ~\"| E[\"Mark previous segment or row\\nas accent-bearing\"]",
            "    C -->|\"separator or linker\"| F[\"Finalize current syllable\\nset boundary I, E, L, X, or F\"]",
            "    C -->|\"newline or pause suite\"| G[\"Finalize syllable, classify pause\\nand append a short or long pause row\"]",
            "    C -->|\"armored pause span\"| H[\"Classify armored suite\\nand append the owned pause row\"]",
            "    D --> I[\"Continue scanning until end of stream\"]",
            "    E --> I",
            "    F --> I",
            "    G --> I",
            "    H --> I",
            "    I --> J[\"Resolve ENA transition rows\\nfrom neighboring vowels\"]",
            "    J --> K{\"Phase 2 current unit\"}",
            "    K -->|\"pause\"| L[\"Choose the closest legal pause duration\\nand update drift\"]",
            "    K -->|\"syllable\"| M[\"Assign onset, coda, and nucleus anchors\\nthen compute post-assignment drift\"]",
            "    M --> N{\"Long-vowel correction or accentuation needed?\"}",
            "    N -->|\"yes\"| O[\"Use legal long-vowel or accent routing\\nthen recompute drift\"]",
            "    N -->|\"no\"| P[\"Keep anchored syllable timing\"]",
            "    O --> Q{\"Completed boundary is F?\"}",
            "    P --> Q",
            "    Q -->|\"yes\"| R[\"Fold drift to the nearest beat-equivalent branch\\nand optionally insert one mini pause\"]",
            "    Q -->|\"no\"| S[\"Carry raw drift into the next linked syllable\"]",
            "    L --> T[\"Phase 3 assign row-level intonation\"]",
            "    R --> T",
            "    S --> T",
            "    T --> U[\"Emit finalized _ophone.txt and _phone.txt\\nplus per-stream drift reports\"]",
        ),
    ),
    FlowchartTarget(
        key="phonetizer-phase1-row-building",
        doc_path="docs/akkapros/phonetizer-algorithm.md",
        validator=_validate_phonetizer_phase1_target,
        mermaid_lines=(
            "flowchart TD",
            "    A[\"Start Phase 1 with normalized _tilde input\"] --> B[\"Read current symbol\"]",
            "    B --> C{\"What kind of symbol is it?\"}",
            "    C -->|\"segment glyph\"| D[\"Create a seed row\\nappend it to the current syllable buffer\"]",
            "    C -->|\"accent mark ~\"| E[\"Mark the previous buffered segment\\nor previous completed row as accented\"]",
            "    C -->|\"syllable separator . or ·\"| F[\"Finalize the buffered syllable\\nwrite boundary I\"]",
            "    C -->|\"enclitic dash -\"| G[\"Finalize the buffered syllable\\nwrite boundary E\"]",
            "    C -->|\"internal merge &\"| H[\"Finalize the buffered syllable\\nwrite boundary L\"]",
            "    C -->|\"explicit merge +\"| I[\"Finalize the buffered syllable\\nwrite boundary X\"]",
            "    C -->|\"space\"| J[\"Finalize the buffered syllable\\nwrite boundary F\"]",
            "    C -->|\"newline\"| K[\"Finalize the buffered syllable as F\\nand append one long EOL pause row\"]",
            "    C -->|\"armored punctuation span\"| L[\"Classify the armored suite\\nand append its pause row\"]",
            "    C -->|\"plain punctuation suite\"| M[\"Consume the full suite\\nclassify it as Q, E, S, C, or I\\nand append a short or long pause row\"]",
            "    D --> N[\"Advance to the next symbol\"]",
            "    E --> N",
            "    F --> N",
            "    G --> N",
            "    H --> N",
            "    I --> N",
            "    J --> N",
            "    K --> N",
            "    L --> N",
            "    M --> N",
            "    N --> O{\"End of input reached?\"}",
            "    O -->|\"no\"| B",
            "    O -->|\"yes\"| P[\"Finalize any remaining syllable as F\"]",
            "    P --> Q[\"Resolve ENA transition rows\\nfrom neighboring vowels\"]",
            "    Q --> R[\"Phase 1 output: structure-only rows\\nwith positions, boundaries, placeholder duration, and neutral intonation\"]",
        ),
    ),
    FlowchartTarget(
        key="phonetizer-phase2-duration-solver",
        doc_path="docs/akkapros/phonetizer-algorithm.md",
        validator=_validate_phonetizer_phase2_target,
        mermaid_lines=(
            "flowchart TD",
            "    A[\"Partition Phase 1 rows into syllable and pause units\"] --> B[\"Walk units from left to right\\ncarrying drift_cursor\"]",
            "    B --> C{\"Current unit kind\"}",
            "    C -->|\"pause\"| D[\"Choose the closest legal pause duration\\ninside the active band and update drift\"]",
            "    C -->|\"syllable\"| E[\"Analyze the syllable\\nidentify onset, nucleus, coda, and accent shape\"]",
            "    E --> F[\"Assign anchor durations\\nonset first, then coda, then nucleus\"]",
            "    F --> G[\"If needed, pre-assign the next same-consonant onset\\nthrough the geminate policy\"]",
            "    G --> H[\"Compute the non-accentuated target\\nand post-assignment drift\"]",
            "    H --> I{\"Long nucleus and unresolved drift beyond tolerance?\"}",
            "    I -->|\"yes\"| J[\"Apply ordinary long-vowel correction\\ninside the legal long-vowel window\"]",
            "    I -->|\"no\"| K[\"Keep the anchored syllable timing\"]",
            "    J --> L{\"Accentuated stream and accent shape present?\"}",
            "    K --> L",
            "    L -->|\"yes\"| M[\"Apply accent increment routing\\nand recompute drift against the half-foot target\"]",
            "    L -->|\"no\"| N[\"Leave the syllable non-accentuated\"]",
            "    M --> O{\"Completed boundary folds here?\"}",
            "    N --> O",
            "    O -->|\"F boundary\"| P[\"Fold drift to the nearest beat-equivalent branch\"]",
            "    O -->|\"I, E, L, or X\"| Q[\"Carry raw drift forward\\ninside the linked prosodic unit\"]",
            "    P --> R{\"Mini pause exactly legal here?\"}",
            "    Q --> S[\"Write row drift tokens\\nand continue to the next unit\"]",
            "    R -->|\"yes\"| T[\"Insert one mini pause\\nand update drift again\"]",
            "    R -->|\"no\"| S",
            "    T --> S",
            "    D --> U[\"After all units, write realized durations and drift tokens\\nthen validate chrono checkpoints\"]",
            "    S --> U",
            "    U --> V[\"Phase 2 output: finalized timing plus drift summary\"]",
        ),
    ),
    FlowchartTarget(
        key="phonetizer-hiatus-and-vowel-transition-processing",
        doc_path="docs/akkapros/phonetizer-algorithm.md",
        validator=_validate_phonetizer_hiatus_transition_target,
        mermaid_lines=(
            "flowchart TD",
            "    A[\"Phase 1 reads a special marker\nhiatus ˙ or transition ¨\"] --> B{\"Which marker enters the row model?\"}",
            "    B -->|\"hiatus ˙\"| C[\"Type the row as H\nuse the closure timing class\"]",
            "    B -->|\"transition ¨\"| D[\"Type the row as T\nuse the sonorant timing class\"]",
            "    C --> E[\"Unstressed singleton timing uses\nspecial_realization.hiatus\"]",
            "    D --> F[\"Unstressed singleton timing uses\nspecial_realization.vowel_transition\"]",
            "    D --> G[\"Resolve the emitted glide from neighboring vowels\nrealization becomes WA or YI\"]",
            "    C --> H{\"Accentuated onset C:V?\"}",
            "    D --> H",
            "    G --> H",
            "    H -->|\"no\"| I[\"Keep the singleton special anchor\nand its class-specific realization\"]",
            "    H -->|\"yes\"| J[\"Accent increment can land on the special row\nbut the anchor stays special\"]",
            "    J --> K{\"Which timing ceiling applies?\"}",
            "    K -->|\"H row\"| L[\"Use closure gemination_max\nas the runtime upper ceiling\"]",
            "    K -->|\"T row\"| M[\"Use sonorant gemination_max\nas the runtime upper ceiling\"]",
            "    L --> N[\"Current limit: no promotion to the ordinary onset lower bound\nand no forced move to the ordinary geminate target\"]",
            "    M --> N",
        ),
    ),
    FlowchartTarget(
        key="fullprosmaker-pipeline",
        doc_path="docs/akkapros/fullprosmaker.md",
        validator=_validate_fullprosmaker_target,
        mermaid_lines=(
            "flowchart TD",
            "    A[\"_proc.txt input\"] --> B[\"Syllabify\\nwrite _syl.txt\"]",
            "    B --> C[\"Prosody realization\\nwrite _tilde.txt\"]",
            "    C --> D[\"Phonetize\\nwrite _ophone.txt, _phone.txt,\\n_ombrola.pho, _mbrola.pho\"]",
            "    D --> E[\"Metrics\\nread paired phone streams\\nwrite _metrics.txt and/or _metrics.json\"]",
            "    E --> F[\"Print\\nread paired phone streams\\nwrite accent outputs\"]",
        ),
    ),
    FlowchartTarget(
        key="diphthong-processing",
        doc_path="docs/akkapros/diphthong-processing.md",
        validator=_validate_diphthong_target,
        mermaid_lines=(
            "flowchart TD",
            "    A[\"Adjacent vowels in source text\"] --> B[\"Syllabifier splits the sequence\\ninsert syllable separator and diphthong marker\"]",
            "    B --> C[\"Prosody works on separated syllables\"]",
            "    C --> D[\"Generated replacement table restores\\ndiphthong memory in _tilde.txt\"]",
            "    D --> E[\"Printer consumes internal markers\\nduring surface rendering\"]",
        ),
    ),
    FlowchartTarget(
        key="metrics-computation",
        doc_path="docs/akkapros/metrics-computation.md",
        validator=_validate_metrics_target,
        mermaid_lines=(
            "flowchart TD",
            "    A[\"_ophone.txt and _phone.txt\"] --> B[\"Load paired phone rows\"]",
            "    B --> C[\"Normalize each row to V, C, or P\"]",
            "    C --> D[\"Coalesce adjacent rows\\ninto interval stretches\"]",
            "    D --> E[\"Compute rhythmic and structural summaries\"]",
            "    E --> F[\"Write _metrics.txt and/or _metrics.json\"]",
        ),
    ),
)


def validate_flowchart_target(target: FlowchartTarget) -> None:
    target.validator()


def render_mermaid_block(target: FlowchartTarget) -> str:
    return "```mermaid\n" + "\n".join(target.mermaid_lines) + "\n```"


def sync_flowchart_block(document_text: str, target: FlowchartTarget) -> str:
    start_index = document_text.find(target.start_marker)
    end_index = document_text.find(target.end_marker)
    if start_index == -1 or end_index == -1 or end_index < start_index:
        raise FlowchartSyncError(
            f"Document {target.doc_path} is missing the required flowchart markers for {target.key}"
        )

    prefix = document_text[: start_index + len(target.start_marker)]
    suffix = document_text[end_index:]
    block = "\n\n" + render_mermaid_block(target) + "\n"
    return prefix + block + suffix


def sync_registered_flowcharts(
    *,
    check: bool,
    repo_root: Path | None = None,
    targets: Iterable[FlowchartTarget] | None = None,
) -> list[str]:
    root = repo_root or ROOT
    selected_targets = tuple(targets or FLOWCHART_TARGETS)
    problems: list[str] = []

    for target in selected_targets:
        try:
            validate_flowchart_target(target)
        except FlowchartSyncError as exc:
            problems.append(str(exc))
            continue

        doc_path = root / target.doc_path
        if not doc_path.exists():
            problems.append(f"Document target does not exist: {target.doc_path}")
            continue

        current_text = doc_path.read_text(encoding="utf-8")
        try:
            expected_text = sync_flowchart_block(current_text, target)
        except FlowchartSyncError as exc:
            problems.append(str(exc))
            continue

        if check:
            if current_text != expected_text:
                problems.append(
                    f"Generated Mermaid block is out of sync for {target.doc_path}; run scripts/sync_doc_flowcharts.py"
                )
            continue

        if current_text != expected_text:
            doc_path.write_text(expected_text, encoding="utf-8")

    return problems


__all__ = [
    "FLOWCHART_TARGETS",
    "FlowchartSyncError",
    "FlowchartTarget",
    "ROOT",
    "render_mermaid_block",
    "sync_flowchart_block",
    "sync_registered_flowcharts",
    "validate_flowchart_target",
]