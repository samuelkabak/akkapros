# 10. Metrics From Text and Dual Percent-V

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

## Links

- Related: `docs/akkapros/metrics-computation.md`
- Related: `docs/akkapros/metricalc.md`
