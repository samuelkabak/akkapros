---
Status: Accepted
Date: 2026-03-10
---

# 10. Metrics From Text and Dual Percent-V

## Plain Summary

We compute rhythm metrics from the project pivot text so we can compare texts without audio.
We report two versions of %V to make results clear under different assumptions.

## Context and Problem Statement

Ancient-language rhythm analysis cannot rely on native audio recordings. The project needs a transparent text-to-metrics method.

## Decision Drivers

- Reproducible quantitative analysis without audio
- Explicit assumptions about mora and pause timing
- Comparable outputs for baseline vs. realized text

## Considered Options

- Skip quantitative metrics for reconstructed text
- Compute metrics from symbolic text with documented duration assumptions

## Decision Outcome

Chosen option: Compute metrics from text using explicit mora/pause rules, including dual percent-V reporting and VarcoC/DeltaC families.

## Pros and Cons of the Options

### Text-derived metrics

- Good, because analysis is possible without recordings
- Good, because assumptions are inspectable and versionable
- Bad, because outputs depend on modeling assumptions

### No metrics on reconstructed text

- Good, because avoids assumption debates
- Bad, because removes objective comparison tools

## Implications and Consequences

- Keep implementation, tests, and docs aligned with this decision when related changes are introduced.
- Treat changes that alter this decision's user-facing behavior as release-note-worthy updates.

## Links

- Related: `docs/akkapros/metrics-computation.md`
- Related: `docs/akkapros/metricalc.md`

## Reviewed By

- Akkapros maintainers

