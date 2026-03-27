# Documentation Launch Gate Runbook

Use this runbook before release approvals or tag creation.

## Purpose
- Keep cross-cutting docs and product release notes synchronized.
- Enforce artifact/checksum traceability per active product.
- Maintain onboarding readiness under 30 minutes.

## Scope
- `README.md`
- `CONTRIBUTING.md`
- `docs/architecture.md`
- `products/**/release-notes/README.md`
- `integrations/nextcloud/artifact-index.yaml`

## Ownership Rotation
- Weekly coordinator: `docs-core`
- Product release-note owner: product maintainer for each changed product pack
- Escalation owner (blockers over 30 min): `CTO`

## Cadence
- Every merge that changes behavior/process/artifact contracts:
  - run this checklist before approval
- Weekly (Monday) docs sweep:
  - cross-check doc links, workflow consistency, and onboarding timing

## Launch Checklist
1. Cross-cutting consistency:
- `README.md`, `CONTRIBUTING.md`, and `docs/architecture.md` describe the same release workflow.
2. Product release notes:
- every affected active product has a new dated entry.
- each entry includes `artifact_id` + `sha256` from `integrations/nextcloud/artifact-index.yaml`.
3. Validation proof:
```bash
./.venv/bin/python tools/validate_library.py
```
4. Onboarding readiness:
- verify `docs/runbooks/onboarding-dry-run.md` latest elapsed time is under 30 minutes.
- if over 30 minutes, record corrective action and owner before release.
5. Decision logging:
- if architecture/process policy changed, append `DECISIONS.md`.

## Exit Criteria
- Validator reports zero blockers.
- Release-note entries are present for all affected products.
- Open corrective actions have explicit owner and due date.
