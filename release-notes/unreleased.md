## Unreleased

Commits since release `v2.0.0`:

- Preserve punctuation armor `⟦...⟧` in `_tilde` and keep pause classification on armored tokens through metrics, printer, phonetizer-facing docs, and full-pipeline docs.
- Distinguish explicit inherited merges (`+`) from internal prosody merges (`&`) in `_tilde` and document downstream consumer support across metrics, printer, phonetizer, and full-pipeline surfaces.
- Correct reader-facing `ḥ` mappings so XAR renders `ḥ/ʿ/ʾ` as apostrophe, IPA `replace` maps `ḥ/ʿ/ʾ` to `ʔ`, and `ḫ` remains distinct in both surfaces.
- Change phonetizer-owned `.pho` output from internal realization codes to MBROLA/X-SAMPA-like symbols derived from the realization inventory, and remove the residual printer MBROLA renderer.
- Breaking interface change: unify `_phone.txt`/`_ophone.txt` row separators to `|` and switch row-level drift tokens to signed arithmetic form `[+-]DDD` (for example `-012`, `+000`, `+054`).


