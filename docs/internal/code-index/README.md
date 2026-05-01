# Code Index — Usage and Maintenance

## Purpose

The code index helps contributors and coding agents choose a bounded code-reading slice during implementation. It supplements the governance records with structural information about the codebase.

## Files

| File | Description | Update method |
|------|-------------|---------------|
| `module-tags.yaml` | Domain tags, coupling levels, test markers, and logical sections for each module | **Manual** — update when modules are added, renamed, or significantly restructured |
| `*_callgraph.mmd` | Mermaid call graphs for each CLI program, showing runtime call relationships | **Automated** — run `python scripts/gen_code_graph.py` to regenerate all graphs |

## How to Use

1. **Start with `module-tags.yaml`** to find the module(s) relevant to your domain tag.
2. **Load coupling=independent modules** in isolation — they have no cross-module side effects.
3. **For coupling=pipeline-critical modules**, check upstream/downstream stage I/O contracts using the call graphs.
4. **Open the relevant `*_callgraph.mmd`** to understand runtime call flow before making changes.

## How to Update

### After adding, renaming, or restructuring modules

1. **Update `module-tags.yaml`** manually:
   - Add a new entry for each new module
   - Update existing entries for renamed or restructured modules
   - Remove entries for deleted modules
   - Follow the existing YAML schema (see entries in the file)

2. **Regenerate call graphs** automatically:
   ```bash
   python scripts/gen_code_graph.py
   ```
   This traces all CLI entry points via `explr` and writes updated `.mmd` files. The tracer automatically picks up new submodule structure.

3. **Run the test suite** to confirm no regressions:
   ```bash
   python -m pytest
   ```

### After governance changes that affect module structure

- Run `python scripts/update-indexes.py` to regenerate governance indexes
- Run `python scripts/gen_code_graph.py` to regenerate call graphs
- Update `module-tags.yaml` manually if module entries changed

## Related

- `docs/internal/GUIDELINES.md` — Section 8 (Code Index) has update rules
- `docs/internal/README.md` — Agent optimization artifacts section
- `tests/dependency_map.yaml` — Test marker routing
