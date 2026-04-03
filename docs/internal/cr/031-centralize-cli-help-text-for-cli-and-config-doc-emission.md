---
cr_id: CR-031
status: Draft
priority: High
impact: Mutative
created: 2026-04-03
updated: 2026-04-03
implements: 'ADR-037'
---

# Change Request: Centralize CLI Help Text for CLI and Config Doc Emission

# Summary

Add one shared help-message registry in `src/akkapros/lib/helpmsg.py` and make
both CLI `--help` output and generated config-file comments reuse that same
canonical text.

This removes drift between parser help strings and `default.yaml`, and it keeps
future wording changes localized to one place.

---

# Scope

## Included

- Add `src/akkapros/lib/helpmsg.py`.
- Store canonical help strings there for config-eligible CLI options and shared
  logging/config flags.
- Reuse those strings from CLI argument definitions.
- Reuse those strings when emitting documented YAML config files.
- Keep wording consistent around "additional" option families such as extra
  vowels, extra consonants, and additional punctuation sets.

## Not Included

- Rewriting non-config CLI epilog examples.
- Introducing a new requirement document beyond the already approved config
  requirement set.

---

# Acceptance Criteria

- [ ] `src/akkapros/lib/helpmsg.py` exists and is the canonical source for the
      shared help text introduced by this CR.
- [ ] Config-eligible CLI modules reuse centralized help text rather than
      repeating local string literals for those options.
- [ ] Generated config comments in `default.yaml` and `confwriter` output reuse
      that centralized help text.
- [ ] Wording for related option families is consistent across CLI help and YAML
      comments.
- [ ] Tests cover the new documented-YAML expectations where needed.

---

# Related Issues

- [ADR-037](../adr/037-centralized-help-message-registry-for-cli-and-config-docs.md)
- [CR-030](030-add-package-wide-yaml-config-and-confwriter.md)
