# 9. Function Word and Merge Policy

## Context and Problem Statement

Certain words and explicit links require prosodic grouping decisions across word boundaries to satisfy realization constraints.

## Decision Drivers

- Handle function-word behavior consistently
- Resolve odd-mora groups without ad hoc exceptions
- Preserve explicit user-marked links

## Considered Options

- Treat all words independently
- Allow controlled forward/backward merge behavior and explicit linker handling

## Decision Outcome

Chosen option: Support merge-forward and merge-backward logic, function-word constraints, and explicit `+` group behavior.

## Pros and Cons of the Options

### Controlled merge policy

- Good, because unresolved units can be repaired systematically
- Good, because explicit user structure can be respected
- Bad, because edge-case behavior needs careful tests

### Fully independent words

- Good, because simpler algorithm
- Bad, because many real contexts remain unresolved or unnatural

## Links

- Related: `docs/akkapros/prosody-realization-algorithm.md`
- Related: `src/akkapros/lib/prosody.py`
