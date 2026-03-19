<!--
Review template for `docs/internal/reviews`.
Filename conventions:
- Use a numeric prefix for stable ordering, e.g. `001-review.md` or `review-001.md`.
- Reserve `000-...` files for templates (these are ignored by the indexer).

Fill the sections below when preparing a code/project review. Keep prose concise; reviewers
should populate each section with a short, actionable statement and any file references.
-->

# Code and Project Review — PROJECT_NAME vX.Y.Z

Review ID: review-000
Date: YYYY-MM-DD
Reviewer: NAME (affiliation/contact)
Scope: Short, explicit list of files/directories the review covers (globs are OK).

---

## 1. Executive Summary

One-paragraph summary of the project's health, high-level verdict, and top 2–3 action items.

## 2. Architecture Assessment

### 2.1 Strengths

- Brief bullets of major strengths (architecture, design patterns, documentation, tests).

### 2.2 Areas for Improvement

- Brief bullets of issues, prioritized; include quick rationale and possible fix directions.

## 3. Code Quality Assessment

- Short bullets describing notable patterns, code smells, and testing gaps that affect maintainability.

## 4. Documentation Assessment

- Notes on missing or unclear documentation and needed updates to templates/specs or README.

## 5. Research / Functional Assessment

- For research projects: evaluate the hypothesis, data, and reproducibility. For apps: describe functional correctness.

## 6. Process and Engineering Practices

- Table or bullets summarizing release/versioning, ADR/CR usage, CI/test coverage, and contribution workflow.

## 7. Recommendations (Priority Order)

- Numbered list of recommended actions (High / Medium / Low priority). For each, give minimal next step.

## 8. Summary Verdict

- Single-sentence conclusion and statement of whether the project is ready for the next milestone.

---

Notes for tooling / coding agents:
- Preserve section headers exactly when programmatically generating or updating reviews.
- Use `Status:` or `Review ID:` metadata lines at the top for quick extraction by scripts.
- Keep the template filename starting with `000-` so indexers can ignore templates automatically.

