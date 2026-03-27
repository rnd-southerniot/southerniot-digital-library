# SouthernIoT Digital Product Library (DPL)

This repository is the **Git-first, schema-validated source-of-truth** for SouthernIoT delivery.
It drives:
- CRM state workflow (gated transitions + parallel workstreams)
- Deterministic AI guidance (retrieve + validate; never invent procedures)
- Field checklists + evidence capture requirements (photos with tags)
- R&D + implementation execution (repeatable SOPs)

## Defaults (Locked)
- LoRaWAN Region: **AS923-1**
- RAK7266 Gateway Modes: **Basic Station (default)** + **UDP Packet Forwarder (supported)**
- Selec MFM384 Modbus default: **9600-N-8-1**

## Key Concepts
- **Product manifest**: `/products/**/manifest.yaml`
- **Statepack**: `/products/**/states/<state>/statepack.yaml`
- **Checklist** (PWA-driven): `/products/**/states/<state>/checklist.yaml`
- **Validation rules**: `/products/**/states/<state>/validations/*.yaml`
- **Nextcloud artifacts**: `/integrations/nextcloud/artifact-index.yaml`

## Repository Layout
- `states.yaml`, `roles.yaml`, `severities.yaml`, `tags.yaml`: authoritative taxonomy
- `schemas/`: JSON Schemas (CI-enforced)
- `products/`: product packs (gateway + edge node)
- `integrations/`: CRM mappings, workstream gates, Nextcloud artifact index
- `tools/`: validator, search index builder, offline field pack exporter
- `docs/`: architecture, glossary, contribution workflow, and templates

## Contributor Docs
- [CONTRIBUTING.md](CONTRIBUTING.md): 30-minute onboarding quickstart and compliant PR checklist
- [AGENTS.md](AGENTS.md): ownership model for agents and maintainers
- [docs/architecture.md](docs/architecture.md): system architecture and data-flow diagram
- [docs/mvp-plan.md](docs/mvp-plan.md): phase-1 MVP scope, sequencing, and acceptance criteria
- [docs/backend-thin-slice-pilot-plan.md](docs/backend-thin-slice-pilot-plan.md): phase-2 backend pilot milestones, dependencies, and rollback gates
- [docs/glossary.md](docs/glossary.md): CRM and statepack vocabulary
- [docs/templates/README.md](docs/templates/README.md): reusable templates for new packs/states
- [docs/release-notes-process.md](docs/release-notes-process.md): release-note process used by all products
- [docs/runbooks/docs-launch-gate.md](docs/runbooks/docs-launch-gate.md): phase-2 docs launch gate (rotation, cadence, and release checks)
- [docs/runbooks/onboarding-dry-run.md](docs/runbooks/onboarding-dry-run.md): latest onboarding dry-run timing and corrective actions

## How CRM Uses the Library
- CRM states match `states.yaml` exactly.
- Workstreams (`gateway`, `edge_node`) are gated by `integrations/crm/parallel-workstreams.yaml`.
- Alerts route to CRM comment thread + email + Mattermost via `integrations/crm/notification-routing.yaml`.

## How to Add a New Product
1. Follow [CONTRIBUTING.md](CONTRIBUTING.md) quickstart.
2. Create `products/<type>/<PRODUCT_ID>/manifest.yaml` and `variants/*.yaml`.
3. Create `states/<each state>/` folders for every state in `states.yaml` with:
   - `statepack.yaml`, `checklist.yaml`, `validations/*.yaml`, `docs/*.md`
4. Use templates from [docs/templates/README.md](docs/templates/README.md).
5. Run the validator and fix blockers before committing.
6. Add or update release notes per [docs/release-notes-process.md](docs/release-notes-process.md).

## Tools
- Pin Python locally with `.python-version` (`3.11.9`) for parity with CI.
- Create/update tooling venv: `make venv`
- Validate library: `make validate`
- Generate machine-readable report: `out/validation-report.json` (created by `make validate`)
- Build search index: `make index`
- Run full clean-room checks (validator + index + field-pack export smoke test): `make ci`
- Export an offline field pack:
  - `./.venv/bin/python tools/export_field_pack.py --project-id P-123 --product-id SOIT-SCOMM-CF-CD-RAK-7266 --variant AS9231_BASIC_STATION_POE --out out/`
  - Role-filtered export example:
    - `./.venv/bin/python tools/export_field_pack.py --project-id P-123 --product-id SOIT-SCOMM-CF-CD-RAK-7266 --variant AS9231_BASIC_STATION_POE --roles FIELD_ENGINEER --out out/`

## CI
- `Validate DPL Library` (`.github/workflows/validate.yml`) runs four independent required jobs on every push/PR:
  - `validator` (`make validate`) and uploads `out/validation-report.json`
  - `fixtures` (`make test`)
  - `index-build` (`make index`)
  - `export-smoke` (`make export-smoke`) and uploads `out/release-smoke/*.zip` plus `out/release-smoke/SHA256SUMS.txt`
- `Release Field Pack` (`.github/workflows/release-field-pack.yml`) builds release artifacts, publishes `SHA256SUMS.txt`, and attaches assets to tags matching `field-pack-v*`.

## Phase-2 Launch Workflow
1. Update product/state files and cross-cutting docs in the same change.
2. Add release-note entries under each affected `products/**/release-notes/README.md` with artifact ID and checksum linkage from `integrations/nextcloud/artifact-index.yaml`.
3. Run `make validate` (or `./.venv/bin/python tools/validate_library.py`) and resolve blockers before review.
4. Confirm onboarding path remains under 30 minutes using `docs/runbooks/onboarding-dry-run.md`.
5. Complete launch-gate checklist in `docs/runbooks/docs-launch-gate.md` before tagging or release approvals.

## Ops Runbooks
- Branch protection + required checks: `docs/operations/branch-protection.md`
- Pipeline triage + rollback: `docs/runbooks/cicd-pipeline-failures.md`
- Docs launch gate + owner cadence: `docs/runbooks/docs-launch-gate.md`
- Onboarding rehearsal evidence: `docs/runbooks/onboarding-dry-run.md`
