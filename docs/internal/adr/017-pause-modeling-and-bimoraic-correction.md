---
Status: Accepted
Date: 2026-03-17
---

# 17. Pause Modeling and Bimoraic Correction

## Plain Summary

Take line breaks and pauses into account when counting morae and fixing odd mora counts across words.
This keeps rhythm metrics accurate near pauses.

## Context and Problem Statement

Metrics are derived from text, not audio. Raw text-derived percent-V values are inflated if pause time is excluded. The project also aims for rhythmically coherent timing where both speech and silence align with bimoraic organization.

## Decision Drivers

- Produce comparable metrics against cross-linguistic rhythm literature
- Make pause assumptions explicit and configurable
- Keep timing model internally coherent with bimoraic rhythm
- Preserve deterministic, reproducible outputs

## Considered Options

- Ignore pauses in metric computation
- Apply a single global pause ratio only
- Classify pause types and apply bimoraic correction after initial allocation

## Decision Outcome

Chosen option: Model pauses explicitly (short vs. long), estimate durations from configured pause ratio, then apply correction so pause durations align with bimoraic units while preserving global budget.

## Pros and Cons of the Options

### Pause classification + correction (chosen)

- Good, because `%V` and related metrics are comparable to speech-based references
- Good, because assumptions are explicit and sensitivity-testable
- Good, because silence follows the same rhythmic system as syllables
- Bad, because model complexity is higher than raw metrics

### Ignore pauses

- Good, because simpler implementation
- Bad, because `%V` is systematically biased

### Fixed global ratio only

- Good, because easy to explain
- Bad, because misses punctuation-level structure and local timing behavior

## Implications and Consequences

- Pause-class constants and correction logic are architectural behavior and require regression tests.
- Changes to pause punctuation categories are metrics-breaking changes and must be documented in release notes.

## Links

- Code: `src/akkapros/lib/metrics.py`
- Code: `src/akkapros/lib/constants.py`
- CLI: `src/akkapros/cli/metricalc.py`
- Doc: `docs/akkapros/metrics-computation.md`
- Research notes: `tmp/research-notes.md` (094-101)

## Reviewed By

- Akkapros maintainers


