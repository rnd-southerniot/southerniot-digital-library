# PR: Repo skeleton + authoritative taxonomy

## Summary
- Adds root-level authoritative taxonomy files (`states.yaml`, `roles.yaml`, `severities.yaml`, `tags.yaml`).
- Aligns CRM state mapping to authoritative state IDs (no spaces/hyphens).
- Expands Nextcloud artifact index structure with required fields and example placeholders.
- Adds `TODO.md` and `DECISIONS.md` to document execution plan and constraints.
- Updates `README.md` for architecture + usage and adds `.gitignore` for generated artifacts.

## Review Notes
- No product pack content is changed beyond taxonomy/integration alignment.
- Nextcloud artifact hashes are placeholders (`sha256=00..00`) until real uploads occur.

## Risks / Rollback
- Low risk: additive files and small mapping correction.
- Rollback: revert this PR; no runtime systems affected.
