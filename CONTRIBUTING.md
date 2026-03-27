# Contributing To SouthernIoT DPL

## Goal
Ship schema-compliant product/state updates that can be reviewed and reused quickly.

## 30-Minute Onboarding Quickstart
1. Setup runtime (5 min)
```bash
python3 -m venv .venv
./.venv/bin/pip install -r tools/requirements.txt
```
2. Verify baseline (5 min)
```bash
./.venv/bin/python tools/validate_library.py
./.venv/bin/python tools/build_search_index.py
```
3. Create or update content (10-15 min)
- Use templates from `docs/templates/`.
- Follow the required state list in `states.yaml`.
- Keep product updates inside one product folder unless intentionally cross-product.
4. Final checks and PR (5 min)
```bash
./.venv/bin/python tools/validate_library.py
git status
```
- Compare your elapsed time and any friction with `docs/runbooks/onboarding-dry-run.md`; add corrective updates if you exceed 30 minutes.

## Authoritative References
- Taxonomy:
  - `states.yaml`
  - `roles.yaml`
  - `severities.yaml`
  - `tags.yaml`
- Schemas:
  - `schemas/manifest.schema.json`
  - `schemas/statepack.schema.json`
  - `schemas/checklist.schema.json`
  - `schemas/validation.schema.json`
  - `schemas/alerting.schema.json`
  - `schemas/crm-event.schema.json`

## Standard File Set For Each State
- `states/<state>/statepack.yaml`
- `states/<state>/checklist.yaml`
- `states/<state>/validations/*.yaml`
- `states/<state>/docs/sop.md`

## Release Notes Requirement
- Any behavior, workflow, validation, or artifact contract change must update:
  - `products/<type>/<product_id>/release-notes/README.md`
- Every entry must include artifact linkage to `integrations/nextcloud/artifact-index.yaml`:
  - `artifact_id`
  - `sha256`
- Follow `docs/release-notes-process.md`.

## Launch Gate Checklist (Phase-2)
- Complete `docs/runbooks/docs-launch-gate.md` before requesting release approval.
- Confirm cross-cutting docs stay aligned:
  - `README.md`
  - `CONTRIBUTING.md`
  - `docs/architecture.md`
- Capture validator proof in your update:
  - `./.venv/bin/python tools/validate_library.py`

## PR Checklist
- [ ] Updated docs/SOPs if operator behavior changed
- [ ] Updated release notes for affected product(s)
- [ ] Included artifact/checksum references in release-note entries
- [ ] Ran validator with zero blockers
- [ ] Added a `DECISIONS.md` entry for architecture/process policy changes
- [ ] Linked taxonomy/schema references when introducing new fields
