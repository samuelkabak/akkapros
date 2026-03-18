---
Status: Accepted
Date: 2026-03-17
---

# 22. Output Format Public Contract Boundaries

## Plain Summary

Explain which parts of the generated outputs are stable public contracts and which may change.
This helps users migrate when outputs change between releases.

## Context and Problem Statement

The toolkit is frequently used in scripted workflows. Users depend not only on CLI execution, but also on specific output file schemas and markers. Compatibility expectations must be explicit to avoid silent breakage.

## Decision Drivers

- Reproducibility for research pipelines
- Predictable upgrade behavior
- Clear SemVer criteria for output changes
- Minimize accidental breaking changes

## Considered Options

- Treat only CLI flags as public API
- Treat CLI + documented output formats as public contract
- Make no formal contract and rely on release notes only

## Decision Outcome

Chosen option: Define output formats as part of the public contract, including naming conventions and core file schemas (`*_syl.txt`, `*_tilde.txt`, `*_metrics.json`, `*_metrics.csv`, and documented printer outputs). Breaking changes to these require MAJOR version bumps.

## Pros and Cons of the Options

### CLI + output formats as contract (chosen)

- Good, because downstream tooling can depend on stable structures
- Good, because SemVer decisions become objective and auditable
- Good, because release communication is clearer
- Bad, because evolution pace is slower for format changes

### CLI-only contract

- Good, because internal formats can evolve quickly
- Bad, because users parsing outputs still break unexpectedly

### No formal contract

- Good, because short-term flexibility
- Bad, because reproducibility and trust degrade over time

## Implications and Consequences

- Output-structure changes must include migration notes and release-note callouts.
- Tests should cover contract-critical markers and schema fields for core outputs.

## Links

- Doc: `docs/akkapros/release-strategy.md`
- Doc: `docs/adr/015-semantic-versioning-and-release-discipline.md`
- Code: `src/akkapros/lib/syllabify.py`
- Code: `src/akkapros/lib/prosody.py`
- Code: `src/akkapros/lib/metrics.py`
- Code: `src/akkapros/lib/print.py`

## Reviewed By

- Akkapros maintainers
