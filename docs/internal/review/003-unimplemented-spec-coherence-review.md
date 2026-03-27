Status: Draft

# Code and Project Review — Unimplemented Internal Spec Coherence

Review ID: review-003
Date: 2026-03-27
Reviewer: GitHub Copilot (GPT-5.4)
Scope: `docs/internal/adr/027-yaml-front-matter-for-cli-pipeline-files.md`, `docs/internal/adr/028-centralized-cli-logging-with-logging-actions.md`, `docs/internal/adr/029-cli-runtime-output-via-logger-only.md`, `docs/internal/req/013-cli-file-front-matter-and-metadata-propagation.md`, `docs/internal/req/014-remove-metrics-csv-output.md`, `docs/internal/req/015-frontmatter-derived-word-indicators-in-metrics.md`, `docs/internal/req/016-standardized-cli-logging-and-console-options.md`, `docs/internal/cr/018-add-cli-file-front-matter-and-metadata-propagation.md`, `docs/internal/cr/020-metrics-word-stats-lex-input.md`, `docs/internal/cr/021-remove-metrics-csv-output.md`, `docs/internal/cr/022-add-frontmatter-derived-word-indicators-to-metrics.md`, and `docs/internal/cr/023-adopt-logging-actions-for-cli-logging.md`. Template files `docs/internal/cr/000-cr-template.md` and `docs/internal/req/000-req-template.md` were checked for structure only. Historical filenames `docs/internal/cr/018-lex-output.md` and `docs/internal/req/013-lexical-output-from-prosmaker.md` are not present in the workspace and are treated as superseded, not current review targets.

---

## 1. Executive Summary

The current unimplemented spec set is directionally coherent: front matter replaces ad hoc metadata propagation, metrics moves toward JSON-only machine-readable output, and CLI runtime behavior is being centralized around shared logging. The set is not yet approval-ready as a bundle, because three cross-document issues remain under-specified: the front matter identifier contract is still open, the metrics changes depend on that unresolved contract, and the logging REQ/CR still use weaker language than the later logger-only ADR. The highest-value next step is to close these three gaps explicitly before implementation sequencing begins.

## 2. Architecture Assessment

### 2.1 Strengths

- `ADR-027`, `REQ-013`, and `CR-018` correctly replace the obsolete `_lex.txt` path with one general provenance mechanism.
- `REQ-014` and `CR-021` reduce metrics contract surface area in a way that is consistent with JSON-first downstream processing.
- `REQ-015` and `CR-022` correctly avoid reconstructing lexical counts from transformed pivot text and instead depend on approved propagated metadata.
- `ADR-028` aligns with the existing repository pattern of centralizing CLI helpers in `src/akkapros/lib/utils.py`.
- `ADR-029` adds the missing policy layer needed to make `--quiet` and `--no-console` semantically reliable.
- `CR-020` is correctly retained as a rejected historical branch, which reduces the chance of accidentally reviving the obsolete design.

### 2.2 Areas for Improvement

- The front matter contract is still missing approved values for `pipeline` and for metrics-specific `file.format` identifiers. That blocks implementation readiness not only for `REQ-013` and `CR-018`, but also for `REQ-015` and `CR-022` because those specs depend on metrics reading approved front matter.
- `ADR-027` still describes metrics CSV as a present format exception, while `REQ-014` and `CR-021` define CSV removal. This is not a hard contradiction if read as transitional, but the relationship should be made explicit to prevent implementers from treating CSV support as a stable long-term requirement.
- `REQ-016` and `CR-023` say logger-based output should replace direct `print()` usage “where practical”, while `ADR-029` requires that all runtime output use the logger except `--help`. The weaker wording is no longer coherent with the later ADR and should be tightened.
- The logging rollout scope remains unresolved, especially for `phoneprep`. Without a first-wave scope, `REQ-016` and `CR-023` are harder to estimate and approve.
- `REQ-015` still carries an open question about whether `prominence_statistics` should be mirrored elsewhere for compatibility. That question conflicts with the otherwise clear direction to keep the new fields in one dedicated section only.

## 3. Code Quality Assessment

- The specs are mostly concrete and implementation-oriented, but a few critical behaviors are still framed as review questions rather than approved contract text.
- Dependency ordering is implied but not stated strongly enough. `REQ-015` and `CR-022` should be treated as blocked by the front matter rollout from `REQ-013` and `CR-018`.
- Logging policy is split sensibly across ADR and REQ/CR layers, but the current wording invites partial migration unless the stronger ADR-029 rule is pulled down into the lower-level specs.
- The current set has good historical hygiene: the rejected CR is explicit, and the deleted lexical-output filenames are no longer active artifacts.

## 4. Documentation Assessment

- The live set should explicitly distinguish transitional statements from end-state contract. The main place this matters is metrics CSV.
- The review set should be read as active documents plus one rejected record. The template files are structurally useful but are not current implementation targets.
- The missing historical filenames in the requested list should remain absent from active indexes and approval discussions; they are superseded by the replacement `REQ-013` and `CR-018`.
- The logging documents would benefit from one explicit statement that `ADR-029` constrains the interpretation of `REQ-016` and `CR-023`.

## 5. Research / Functional Assessment

From a functional standpoint, the proposed sequence is sound:

- front matter first,
- metrics consumers of front matter second,
- CSV removal in the same metrics-contract cleanup window,
- shared logging setup and logger-only runtime behavior as a coordinated CLI migration.

The main risk is not conceptual but procedural. If metrics indicators or logging migration proceed before the remaining contract questions are closed, implementers will have to guess at schema values or rollout scope. That would undermine the conservative-change discipline stated elsewhere in the repository.

## 6. Process and Engineering Practices

- ADR / REQ / CR layering is being used correctly overall.
- Cross-spec dependency management is present but should be stated more sharply in the metrics documents.
- Rejected work is documented instead of silently deleted, which is a strength.
- Approval readiness is currently limited by unresolved identifiers and migration-scope questions rather than by missing rationale.
- Implementation sequencing should be explicit: `ADR-027` / `REQ-013` / `CR-018` before `REQ-015` / `CR-022`; `ADR-028` plus `ADR-029` before approving the final wording of `REQ-016` / `CR-023`.

## 7. Recommendations (Priority Order)

1. High: Close the front matter identifier set in `REQ-013` and `CR-018`, specifically approved `pipeline` values and metrics `file.format` identifiers. Minimal next step: amend those two documents so no implementation-critical identifier remains open.
2. High: Resolve the CSV end-state wording in the front matter family. Minimal next step: update `ADR-027` or the dependent specs so it is explicit that CSV is an exceptional case only during any approved transition and is not part of the intended long-term metrics contract.
3. High: Tighten `REQ-016` and `CR-023` so they match `ADR-029` exactly on runtime output policy. Minimal next step: replace “where practical” and similar soft language with the logger-only rule, keeping `--help` as the sole direct-print exception.
4. High: Make the dependency of `REQ-015` and `CR-022` on approved front matter operationally explicit. Minimal next step: add wording that these metrics indicators are blocked until the front matter schema and required keys are finalized and available.
5. Medium: Decide whether `prominence_statistics` is the sole JSON location for the new metrics fields. Minimal next step: close the open compatibility question in `REQ-015` to avoid a second output location appearing later.
6. Medium: Define first-rollout CLI scope for `REQ-016` and `CR-023`, including whether `phoneprep` is mandatory in wave one. Minimal next step: add a short in-scope list or staged rollout note.
7. Low: Keep `CR-020` as rejected history and continue excluding the deleted lexical-output files from active review sets. Minimal next step: none beyond normal index hygiene.

## 8. Summary Verdict

The spec set is close to implementation-ready, but approval should wait until the front matter identifiers, the CSV transition/end-state boundary, and the logging-policy wording are closed consistently across the active ADR/REQ/CR documents.

---

Notes:

- Active implementation targets in this review are the live ADR/REQ/CR files listed in Scope, not the `000-*` templates.
- `CR-020` is coherent as a rejected record and does not block current work.
- The deleted historical filenames in the original review list should be treated as superseded references only.