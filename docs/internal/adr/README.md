# Architecture Decision Records (ADR)

This folder contains architecture and engineering decisions for `akkapros`.

[CR index](index.md) 

---------------------------------------------------------------------

# How to add a new ADR

1. Copy the MADR template used in this folder.
2. Create `NNN-short-kebab-title.md`.
3. Link it in index.md, the latest adr first.
> Example:
> [NNN. Short Kebab Title](NNN-short-kebab-title.md) - status

4. If it supersedes another ADR, mention it in the Links section.

---------------------------------------------------------------------

# Naming Rules

ADR names use the format:

NNN-short-kebab-title

Examples:

001-initial-authentication  
002-rate-limiter  
003-support-oauth-login  

Where:

NNN is a sequential number.

## Picking the next ADR number

- When creating a new ADR, always assign the next unused sequential number
	(NNN). To find the next number, list the files in this directory and pick
	one greater than the highest existing NNN (e.g., if the highest ADR is
	`024-...`, the next ADR should be `025-...`).
- Do not reuse numbers.

---------------------------------------------------------------------

