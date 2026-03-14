# Architecture Decision Records (ADR)

This folder contains architecture and engineering decisions for `akkapros`.

Canonical template: MADR (short form used in this project).

## Index

- [001. CLI/Lib Separation](001-cli-lib-separation.md)
- [002. Centralized Version Management](002-centralized-version-management.md)
- [003. Output Prefix Convention](003-output-prefix-convention.md)
- [004. Stage Pipeline and Pivot Format](004-stage-pipeline-and-pivot-format.md)
- [005. eBL ATF Normalization Policy](005-ebl-atf-normalization-policy.md)
- [006. Syllabifier Line and Hyphen Policy](006-syllabifier-line-and-hyphen-policy.md)
- [007. Two-Phase Diphthong Processing](007-two-phase-diphthong-processing.md)
- [008. Bimoraic Prosody and Accent Styles](008-bimoraic-prosody-and-accent-styles.md)
- [009. Function Word and Merge Policy](009-function-word-and-merge-policy.md)
- [010. Metrics From Text and Dual Percent-V](010-metrics-from-text-and-dual-percent-v.md)
- [011. Multi-Format Printer Outputs](011-multi-format-printer-outputs.md)
- [012. Phoneprep Coverage and Sidecars](012-phoneprep-coverage-and-sidecars.md)
- [013. Canonical Docs Location and Build Sync](013-canonical-docs-location-and-build-sync.md)
- [014. CLI Built-In Self-Tests](014-cli-built-in-self-tests.md)
- [015. Semantic Versioning and Release Discipline](015-semantic-versioning-and-release-discipline.md)

## How to add a new ADR

1. Copy the MADR template used in this folder.
2. Create `NNN-short-kebab-title.md`.
3. Link it in this index.
4. If it supersedes another ADR, mention it in the Links section.
