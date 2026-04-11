---
cr_id: CR-053
status: Done
priority: Medium
impact: Additive
created: 2026-04-11
updated: 2026-04-11
implements: 'ADR-043'
---

# Change Request: Expand prosmaker demo config to full explicit defaults

## Summary

Expand the checked-in prosmaker demo config so it lists the full effective
parameter surface relevant to the demo instead of relying mainly on internal
built-in defaults.

The goal is pedagogical and exploratory: a demo config should be readable as a
working parameter sheet that users can modify directly when they want to try
alternative prosody, phonetizer, metrics, or print settings.

---

## Motivation

[CR-052](052-make-prosmaker-demo-config-driven-and-restore-printer-outputs.md)
successfully moved the demo to a checked-in grouped config file and restored
printer outputs. However, the implemented demo config intentionally stayed
minimal and relied on many internal defaults.

That keeps the wrapper concise, but it weakens the demo as an exploratory tool.
For a demo, users should be able to open one file and see the effective default
settings that shape the run, then change those settings without first needing
to discover hidden defaults elsewhere in the repository.

This CR therefore adds a stronger documentation and usability requirement for
the demo config itself: it should be explicit, not merely present.

---

## Scope

## Included

- Expand the checked-in prosmaker demo config to list the full effective
  defaults relevant to the demo workflow.
- Make the demo config a self-describing example of the grouped YAML schema for
  the stages used in the prosmaker demo.
- Update demo documentation so users understand that the checked-in config file
  is intended as the primary place to experiment with parameters.
- Keep the wrapper scripts thin and config-driven after the config expansion.

## Not Included

- Changing the global built-in defaults in `src/akkapros/config/default.yaml`.
- Requiring the demo config to include unrelated sections not used by the demo.
- Redefining stage behavior or CLI contracts.

---

## Current Behavior

After CR-052, the prosmaker demo loads a checked-in grouped config file under
`demo/akkapros/prosmaker/`, but that file currently contains only a small
subset of the effective settings and still relies heavily on internal defaults.

This means the demo is now config-driven, but not yet self-describing. Users
who want to explore other parameter settings still need to consult
`src/akkapros/config/default.yaml`, CLI help, or other documentation to learn
what the remaining defaults are.

---

## Proposed Change

- Expand the checked-in demo config so it explicitly lists the effective
  settings used by the prosmaker demo for the relevant sections.
- Prefer copying the effective defaults for demo-relevant keys into the demo
  config rather than leaving them implicit.
- Keep branch-specific per-run overrides in the wrapper only when one single
  config file cannot express all branch differences cleanly.
- Update `demo/README.md` so it presents the demo config as the main user entry
  point for experimenting with parameters.

---

## Technical Design

Architecture notes:

Components:

- `demo/akkapros/prosmaker/corpus-demo.yaml`
- `demo/README.md`
- demo wrappers only if needed to keep them aligned with the expanded config

Config design guidance:

- include the relevant `common`, `atfparse`, `syllabify`, `prosody`,
  `phonetize`, `metrics`, and `print` sections used by the demo
- prefer explicit values over implicit fallback to internal defaults
- remain valid grouped YAML compatible with `confwriter`
- do not duplicate every repository setting if a section is unrelated to the
  demo workflow

---

## Files Likely Affected

demo/akkapros/prosmaker/corpus-demo.yaml
demo/README.md
demo/akkapros/prosmaker/corpus-demo.ps1
demo/akkapros/prosmaker/corpus-demo.sh

---

## Acceptance Criteria

- [x] The checked-in prosmaker demo config explicitly lists the effective
      defaults relevant to the demo workflow instead of leaving most of them to
      implicit internal defaults.
- [x] The config remains valid grouped YAML compatible with `confwriter`.
- [x] The demo wrappers remain thin and continue to rely on the config file as
      the primary parameter source.
- [x] `demo/README.md` explains that the config file is the main place for
      users to inspect and modify demo parameters.
- [x] The expanded config does not silently change the observed demo behavior
      compared with CR-052; it makes that behavior explicit.

---

## Risks / Edge Cases

Possible issues:

- copying too much from the package default config may make the demo config
  harder to read instead of easier
- wrapper-specific branch overrides may still obscure a few effective values if
  not documented clearly
- future built-in default changes may require explicit demo config refreshes to
  keep the file synchronized

---

## Testing Strategy

Manual verification:

- inspect the expanded demo config and confirm that the effective demo behavior
  is readable from the file itself
- rerun the demo and confirm outputs remain consistent with CR-052

Documentation verification:

- confirm `demo/README.md` directs users to the demo config as the main
  experimentation surface

---

## Rollback Plan

If the expanded config becomes too verbose or misleading, revert the config and
README changes together and restore the narrower CR-052 configuration until a
more targeted demo-config design is agreed.

---

## Related Issues

- [CR-052](052-make-prosmaker-demo-config-driven-and-restore-printer-outputs.md)
- [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md)

---

## Tasks

## Implementation

- [x] Expand the demo config with explicit effective defaults
- [x] Keep wrapper behavior aligned with the expanded config

## Tests

- [x] Rerun the demo and confirm behavior remains unchanged

## Documentation

- [x] Update `demo/README.md` to present the config as the main experimentation surface

## Review

- [x] Verify acceptance criteria

---

## Implementation Blockers

Use this section when implementation or verification cannot proceed safely.

Leave the section empty if no blockers are known.

---

## Notes

This CR is additive relative to CR-052. It does not say the earlier work was
wrong; it says the new requirement is stronger: the demo config should be
explicit enough for users to learn and experiment from one file.

Verification completed on 2026-04-11:

- expanded `demo/akkapros/prosmaker/corpus-demo.yaml` to spell out the active
  grouped-config defaults for the demo-relevant `common`, `atfparse`,
  `syllabify`, `prosody`, `phonetize`, `metrics`, and `print` sections
- updated `demo/README.md` so the checked-in config is presented as the main
  user-facing experimentation surface and documented the remaining wrapper-only
  per-branch overrides
- verified the config with `python -m akkapros.cli.confwriter --conf
  demo/akkapros/prosmaker/corpus-demo.yaml --verify`
- reran `demo/akkapros/prosmaker/corpus-demo.ps1` and confirmed that the demo
  still regenerates the same branch outputs introduced by CR-052, including
  `_accent_acute.txt`, `_accent_bold.md`, `_accent_xar.txt`, `_xar.txt`,
  `_phone.txt`, `_ophone.txt`, `_metrics.txt`, `_metrics.json`, and `.pho`
  artifacts for `corpus-lob`, `corpus-mono-lob`, and `corpus-sob`
