# Packaged Documentation Mirror

The canonical project documentation is maintained at the repository top level in:

- `docs/`
- `docs/akkapros/`

This `src/akkapros/docs/` directory is a packaging mirror used so documentation files can be included in built distributions.

Do not edit documentation files here directly.

Before packaging, docs are synced from `docs/akkapros/` into this directory by:

- `python scripts/sync_docs.py`
- `python scripts/build_package.py` (runs sync automatically, then builds)
