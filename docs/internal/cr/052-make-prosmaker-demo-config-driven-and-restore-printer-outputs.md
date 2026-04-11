---
cr_id: CR-052
status: Done
priority: High
impact: Mutative
created: 2026-04-11
updated: 2026-04-11
implements: 'ADR-043, REQ-007, REQ-030'
---

# Change Request: Make prosmaker demo config-driven and restore printer outputs

# Summary

Bring the `demo/akkapros/prosmaker/` corpus demo back into alignment with the
active runtime contracts by making it load a checked-in config file and by
updating the demo pipeline so printer outputs are generated again under the
current phone-row downstream model.

This CR also requires the demo README to be updated so it describes the actual
demo inputs, execution model, produced artifacts, and the new config-backed
customization path instead of the older pre-phone-row printer workflow.

---

# Motivation

The current demo scripts are out of date in two visible ways.

First, they still hardcode most stage options directly in the wrapper scripts
instead of demonstrating the repository's grouped config support. That makes
the demo less useful as an example of current runtime usage and duplicates
settings across the PowerShell and POSIX launchers.

Second, the demo still invokes `printer.py` with `_tilde.txt` input even though
the active printer contract now consumes `_phone.txt` and the matching
`_ophone.txt`. As a result, the current `demo/akkapros/prosmaker/results/`
folder contains prosody, phonetizer, and metrics outputs, but no printer
artifacts. The demo README still advertises printer outputs as if they were
being produced.

This CR exists to repair the demo specification so the demo once again serves
as a trustworthy example of the current pipeline.

---

# Scope

## Included

- Add a checked-in demo config file for the prosmaker corpus demo.
- Update both demo launchers to load that config file instead of hardcoding the
  same runtime settings redundantly in script bodies.
- Update the demo pipeline so printer runs use `_phone.txt` and the matching
  `_ophone.txt` under the active printer contract.
- Restore generation of the printer outputs required for the demo branches,
  specifically acute, bold, accented XAR, and plain XAR outputs.
- Update `demo/README.md` so it accurately describes the demo workflow,
  config-file usage, and produced outputs.

## Not Included

- Redesigning the main runtime CLIs or their config schema.
- Reopening the phone-row downstream contract for metrics or printer.
- Broad demo redesign outside `demo/akkapros/prosmaker/` and its README entry.

---

# Current Behavior

Repository inspection on 2026-04-11 shows the following live state.

- `demo/akkapros/prosmaker/corpus-demo.ps1` and
  `demo/akkapros/prosmaker/corpus-demo.sh` run the corpus demo by calling the
  individual CLIs directly with hardcoded flags.
- Neither launcher currently loads a grouped YAML config file with `--conf`.
- Both launchers still call `printer.py` with `*_tilde.txt` paths.
- The active printer contract documented in `docs/akkapros/printer.md` expects
  `<prefix>_phone.txt` as the primary input and derives the matching
  `_ophone.txt` sibling unless `--ophone` is supplied explicitly.
- The active printer CLI does not accept `_ophone.txt` as the primary
  positional input. `_ophone.txt` is a paired auxiliary input resolved by
  sibling derivation or passed explicitly with `--ophone`.
- The current demo results directory contains `_tilde.txt`, `_ophone.txt`,
  `_phone.txt`, `.pho`, and metrics artifacts, but no printer outputs.
- `demo/README.md` still documents accent outputs in the prosmaker demo result
  set even though the current demo run does not generate them.

Observed current files include:

- `demo/akkapros/prosmaker/corpus-demo.ps1`
- `demo/akkapros/prosmaker/corpus-demo.sh`
- `demo/README.md`
- `demo/akkapros/prosmaker/results/`

---

# Proposed Change

- Add one checked-in grouped config file under `demo/akkapros/prosmaker/`
  containing the stable demo defaults that should not be repeated across both
  launchers.
- Make both demo launchers pass that file with `--conf` to the relevant CLIs.
- Treat that file as a user-editable grouped config artifact that can also be
  created or adjusted with `confwriter` when maintainers want to change the
  demo defaults without editing the wrapper logic directly.
- Keep branch-specific differences such as output prefix and prosody style
  explicit in the launcher or in clearly separated demo config variants, but do
  not duplicate the full stable option set in each script.
- Update printer invocation so each demo branch prints from the generated
  `<prefix>_phone.txt` stream and, when needed, relies on the matching
  `_ophone.txt` sibling or passes it explicitly.
- Update the demo README so it explains:
  - where the demo config file lives
  - that the file is a normal grouped config and can be maintained with
    `confwriter` if desired
  - that the wrappers are thin launchers over config-backed runtime CLIs
  - which outputs are expected after a successful run
  - that printer output now comes from phone-row artifacts, not from
    `_tilde.txt`

---

# Technical Design

Architecture notes:

Components:
- `demo/akkapros/prosmaker/corpus-demo.ps1`
- `demo/akkapros/prosmaker/corpus-demo.sh`
- one new demo config file under `demo/akkapros/prosmaker/`
- `demo/README.md`

Config direction:
- use the repository's grouped YAML config surface rather than script-local
  repeated flags wherever the values are stable across runs
- prefer a checked-in demo config that documents current recommended usage
- keep the config file compatible with normal `confwriter` maintenance rather
  than treating it as a one-off special demo format
- allow branch-specific overrides in the launcher when one shared config file
  cannot express all branch differences cleanly

Printer handoff direction:
- treat `_phone.txt` and `_ophone.txt` as the active downstream inputs for demo
  printer runs, consistent with the live printer and full-pipeline contracts
- do not keep the demo on the historical `_tilde.txt` printer path

Documentation direction:
- `demo/README.md` must describe current behavior only
- `demo/README.md` must explain how the checked-in config participates in the
  demo run and that maintainers may update it through `confwriter`
- if the README lists expected outputs, those outputs must be produced by the
  demo as currently written

---

# Files Likely Affected

demo/akkapros/prosmaker/corpus-demo.ps1
demo/akkapros/prosmaker/corpus-demo.sh
demo/akkapros/prosmaker/<demo-config>.yaml
demo/README.md

No production source files are expected to change unless implementation
discovers a separate runtime bug outside the demo wrappers.

---

# Acceptance Criteria

- [ ] The prosmaker corpus demo includes a checked-in config file under
- [x] The prosmaker corpus demo includes a checked-in config file under
      `demo/akkapros/prosmaker/`.
- [ ] Both demo launchers load that config file with `--conf` for the relevant
- [x] Both demo launchers load that config file with `--conf` for the relevant
      runtime CLIs instead of duplicating the same stable runtime settings only
      in script bodies.
- [ ] The checked-in demo config is a normal grouped YAML config that remains
- [x] The checked-in demo config is a normal grouped YAML config that remains
  compatible with maintenance through `confwriter`.
- [ ] The demo still produces the three existing prosody branches:
- [x] The demo still produces the three existing prosody branches:
      `corpus-lob`, `corpus-mono-lob`, and `corpus-sob`.
- [ ] Printer runs in the demo use `<prefix>_phone.txt` as the active input and
- [x] Printer runs in the demo use `<prefix>_phone.txt` as the active input and
      the matching `<prefix>_ophone.txt` contract where required.
- [ ] Running the demo regenerates, for each branch, at least these printer
- [x] Running the demo regenerates, for each branch, at least these printer
  outputs under the current printer contract:
  `<prefix>_accent_acute.txt`, `<prefix>_accent_bold.md`,
  `<prefix>_accent_xar.txt`, and `<prefix>_xar.txt`.
- [ ] The demo README describes the config-backed launch flow and no longer
- [x] The demo README describes the config-backed launch flow and no longer
      implies that printer still consumes `_tilde.txt`.
- [ ] The demo README explains that `_ophone.txt` is a paired auxiliary input
- [x] The demo README explains that `_ophone.txt` is a paired auxiliary input
  for printer and not the primary positional printer input.
- [ ] The demo README's documented output inventory matches the files actually
- [x] The demo README's documented output inventory matches the files actually
      produced by the demo.
- [ ] The CR is satisfied without redefining the active grouped config schema or
- [x] The CR is satisfied without redefining the active grouped config schema or
      the active printer input contract.

---

# Risks / Edge Cases

Possible issues:

- one shared demo config file may not be sufficient if the three demo branches
  require materially different stable settings
- the PowerShell and POSIX launchers may diverge again if one keeps branch
  overrides that the other forgets to mirror
- implementation may discover that missing printer outputs are caused by an
  additional runtime issue beyond the stale `_tilde` input path
- maintainers may assume printer can be driven from `_ophone.txt` alone, even
  though the active CLI contract requires `<prefix>_phone.txt` as the main
  positional input
- the README may become stale again if output filenames are listed manually but
  the wrapper changes later without synchronized documentation updates

---

# Testing Strategy

Manual/demo verification:

- run both demo launchers and confirm they complete successfully under the
  checked-in demo config
- confirm the results directory contains prosody, phonetizer, metrics, and
  printer outputs for all three demo branches
- confirm that acute, bold, accented XAR, and plain XAR files are present for
  each branch

Contract verification:

- verify that printer invocation paths in the launchers now follow the active
  `printer.py` phone/ophone input contract
- verify that the launchers do not treat `_ophone.txt` as a standalone primary
  printer input
- verify that the demo README output list matches the regenerated files

If implementation adds automated coverage:

- prefer a narrow regression test or script-level verification that checks for
  presence of the expected printer outputs after the demo run

---

# Rollback Plan

If the new config-backed demo flow proves misleading or unstable, revert the
demo-wrapper and README changes together and restore the prior scripts while a
smaller follow-up CR defines a narrower demo contract.

---

# Related Issues

- [CR-053](053-expand-prosmaker-demo-config-to-full-explicit-defaults.md)
- [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md)
- [REQ-007](../req/007-full-pipeline-orchestration.md)
- [REQ-013](../req/013-cli-file-front-matter-and-metadata-propagation.md)
- [REQ-030](../req/030-phone-ophone-only-metrics-and-interval-rhythm-computation.md)
- [CR-047](047-close-phonetizer-pause-and-reconstruction-gaps.md)
- [CR-051](051-align-and-enrich-research-facing-package-documentation.md)

---

# Tasks

## Implementation

- [x] Add the demo config file
- [x] Update the PowerShell launcher to use the demo config and current printer contract
- [x] Update the POSIX launcher to use the demo config and current printer contract

## Tests

- [x] Run the demo and confirm printer outputs are regenerated
- [x] Verify the launcher behavior matches the active CLI contracts

## Documentation

- [x] Update `demo/README.md`
- [x] Document the `confwriter`-compatible demo config workflow in `demo/README.md`
- [x] Align the documented demo outputs with the actual generated files

## Review

- [x] Verify acceptance criteria
- [x] Confirm the demo now reflects current config and printer usage


---

# Implementation Blockers

Use this section when implementation or verification cannot proceed safely.

Leave the section empty if no blockers are known.

---

# Notes

This CR is grounded in direct inspection of the current demo scripts, the live
printer documentation, and the current demo results directory on 2026-04-11.

Verification on 2026-04-11 confirmed the updated PowerShell demo regenerates
the three prosody branches and the requested printer outputs under the active
`_phone.txt` + `_ophone.txt` printer contract.

Further verification on 2026-04-11 confirmed the updated POSIX launcher also
executes successfully in this Windows environment when run through the local
MSYS bash executable. That verification additionally surfaced and resolved two
shell-wrapper issues during implementation: repository-root path resolution and
portable Python interpreter resolution inside the shell script.

Follow-up note: [CR-053](053-expand-prosmaker-demo-config-to-full-explicit-defaults.md)
adds a stronger requirement for the demo config to enumerate the full relevant
effective defaults instead of relying mostly on internal built-in defaults.

It intentionally treats the missing printer outputs as a demo-contract problem
first. If implementation later shows that a separate runtime bug also prevents
printer generation under correct `_phone.txt` input, that runtime bug should be
handled in a follow-up ADR/CR chain rather than being silently folded into this
demo-maintenance record.