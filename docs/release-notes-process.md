# Release Notes Process

## Purpose
Record what changed in a product pack and whether field operations or CRM behavior are affected.

## When To Update
- Any change to `manifest.yaml`, statepack/checklist/validation/SOP, variants, or troubleshooting.
- Any change that affects approvals, evidence requirements, or alert routing.

## Entry Format
Use reverse chronological entries in each product `release-notes/README.md`:

```md
## YYYY-MM-DD — <version-or-tag>
- Summary: one-line change statement.
- Impact: operator/CRM impact.
- Artifacts:
  - `<artifact_id>` (`sha256: <hash>`) from `integrations/nextcloud/artifact-index.yaml`
- Files:
  - `relative/path/one`
  - `relative/path/two`
- Validation:
  - `./.venv/bin/python tools/validate_library.py` (pass/fail)
- Follow-up: optional actions.
```

## Quality Rules
- Keep entries actionable and linked to changed files.
- Call out breaking changes explicitly.
- Mention required rollout sequencing if cross-workstream.
- Include artifact linkage for the latest published (or verified) product artifact checksum on every entry.
- If artifact hash is a placeholder, note follow-up ownership and replacement target date.
