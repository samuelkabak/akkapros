---
review_id: review-005
status: Done
created: 2026-04-05
updated: 2026-04-05
reviewer: GitHub Copilot (GPT-5.4)
scope: >-
  docs/internal/req/002-syllabification.md,
  docs/internal/req/004-metrics-computation.md,
  docs/internal/req/011-punctuation-whitelist-and-cli-extension.md,
  docs/internal/cr/003-change-escape-delimiters.md,
  docs/internal/cr/012-enforce-punctuation-whitelist-and-cli-extension.md,
  and the current internal stage-contract assumption that metrics consumes
  `_tilde` after prosody.
---

# Code and Project Review — Punctuation Armor Through `_tilde`

## 1. Executive Summary

The current internal contract is vulnerable at one narrow but important stage boundary. [REQ-002](../req/002-syllabification.md) correctly gives the syllabifier an explicit escape armor for punctuation and non-Akkadian chunks using `⟦...⟧`, and the punctuation-hardening work in [REQ-011](../req/011-punctuation-whitelist-and-cli-extension.md) and [CR-012](../cr/012-enforce-punctuation-whitelist-and-cli-extension.md) assumes that punctuation classification is a strict scientific contract. However, if prosody/prosmaker removes the armor and writes raw punctuation back into `_tilde`, then [REQ-004](../req/004-metrics-computation.md) inherits a more fragile input contract than the syllabifier produced. The highest-value next step is to keep punctuation armored throughout internal pivot artifacts, including `_tilde`, and reserve de-armoring for printer or other explicitly user-facing output stages only.

## 2. Architecture Assessment

### 2.1 Strengths

- [REQ-002](../req/002-syllabification.md) already defines a strong internal representation for escaped punctuation and non-Akkadian spans using `⟦...⟧`.
- [CR-003](../cr/003-change-escape-delimiters.md) deliberately chose rare escape delimiters, which makes the armor well suited to machine-readable internal use.
- [REQ-011](../req/011-punctuation-whitelist-and-cli-extension.md) and [CR-012](../cr/012-enforce-punctuation-whitelist-and-cli-extension.md) correctly treat punctuation as a controlled classification problem rather than as incidental formatting.
- `_tilde` is an internal pivot artifact, not the final presentation layer, so preserving machine-oriented structure there is architecturally reasonable.

### 2.2 Areas for Improvement

- There is no explicit internal requirement stating that punctuation armor must survive the prosody stage unchanged when `_tilde` is written.
- [REQ-004](../req/004-metrics-computation.md) says metrics consumes `_tilde`, but it does not state whether punctuation arrives as armored internal tokens or as raw restored text.
- If raw punctuation is reintroduced after prosody, metrics becomes sensitive to punctuation re-detection at exactly the point where earlier stages had already made punctuation explicit.
- This weakens the scientific value of the punctuation whitelist, because the pipeline stops carrying the most explicit punctuation state into the stage that still depends on it.

## 3. Code Quality Assessment

- This is primarily a contract-quality issue rather than a code-style issue.
- The current contract shape risks duplicated parsing logic: punctuation is recognized and armored in syllabification, then potentially flattened back into ordinary text, then inferred again by metrics.
- Re-inference after prior normalization is the kind of silent drift that this repository has otherwise worked hard to avoid.
- The narrowest robust design is to treat punctuation armor as part of the internal pivot representation, not as a temporary tokenizer convenience.

## 4. Documentation Assessment

- [REQ-002](../req/002-syllabification.md) is explicit about armored escapes in syllabifier output.
- [REQ-004](../req/004-metrics-computation.md) is explicit that metrics consumes `_tilde`, but it is not explicit about whether escape armor must remain present there.
- [REQ-011](../req/011-punctuation-whitelist-and-cli-extension.md) and [CR-012](../cr/012-enforce-punctuation-whitelist-and-cli-extension.md) document strict punctuation classification, but they do not close the prosody-stage handoff gap.
- A follow-up ADR/REQ/CR or an amendment to an existing open record is needed to specify that de-armoring is presentation behavior only, not prosody-pivot behavior.

## 5. Research / Functional Assessment

- Keeping punctuation armored through `_tilde` would make metrics less sensitive to formatting drift and more dependent on already-classified internal structure.
- This would better preserve the distinction between linguistic content and punctuation/preserve-block content across the full internal pipeline.
- It also aligns with the project’s broader pattern of keeping internal helper markers such as `¦`, `·`, `˙`, `¨`, and `~` until a later formatting stage decides how to render them.
- If punctuation is restored too early, the metrics stage must recover structure from ordinary text instead of inheriting the structure already computed upstream.
- Because `_tilde` is internal only, preserving the armor there has little user-facing downside and a clear downstream robustness upside.

## 6. Process and Engineering Practices

- The repository already uses ADR/REQ/CR layering to protect internal contracts from silent reinterpretation.
- This punctuation issue should therefore be handled additively through a new internal record or an explicit amendment to an existing open spec, not by informal convention alone.
- Any future phonetize-stage contract should inherit the same principle: punctuation-class decisions made upstream should stay explicit in internal artifacts until a presentation stage intentionally flattens them.
- Regression coverage should be required at the stage-boundary level, not only within the tokenizer and metrics entrypoints separately.

## 7. Recommendations (Priority Order)

1. High: Specify that punctuation escapes armored as `⟦...⟧` in syllabifier output remain armored in all internal downstream pivot artifacts that metrics or phonetize may consume. Minimal next step: add a new CR or amend an open CR/REQ to make armor preservation through `_tilde` an explicit contract.

2. High: Restrict punctuation de-armoring to printer or other explicitly presentation-oriented outputs. Minimal next step: document that prosody/prosmaker does not restore raw punctuation into `_tilde`; restoration, if desired, belongs to print-facing stages only.

3. High: Add boundary-level regression tests for `syllabify -> prosmaker -> metrics` covering escaped punctuation and mixed content. Minimal next step: require at least one integration fixture where punctuation is armored in `_syl`, remains armored in `_tilde`, and is consumed without reclassification drift by metrics.

4. Medium: Clarify how punctuation armor interacts with pause modeling. Minimal next step: document whether the metrics stage reads pause class directly from armored punctuation tokens, from inherited front matter, or from a dedicated normalized structure.

5. Medium: Keep the same principle in the phonetizer contract. Minimal next step: when `_phone` is finalized, ensure punctuation-triggered silence generation derives from explicit upstream punctuation state rather than from raw punctuation re-parsing wherever feasible.

## 8. Summary Verdict

The current internal punctuation story is close to coherent, but it is not fully robust until the specs explicitly require punctuation armor to survive through `_tilde` and reserve de-armoring for presentation-only outputs.