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

## How CRM Uses the Library
- CRM states match `states.yaml` exactly.
- Workstreams (`gateway`, `edge_node`) are gated by `integrations/crm/parallel-workstreams.yaml`.
- Alerts route to CRM comment thread + email + Mattermost via `integrations/crm/notification-routing.yaml`.

## How to Add a New Product
1. Create `products/<type>/<PRODUCT_ID>/manifest.yaml` and `variants/*.yaml`.
2. Create `states/<each state>/` folders for every state in `states.yaml` with:
   - `statepack.yaml`, `checklist.yaml`, `validations/*.yaml`, `docs/*.md`
3. Run the validator and fix any blockers before committing.

## Tools
- Validate library: `python tools/validate_library.py`
- Build search index: `python tools/build_search_index.py`
- Export an offline field pack:
  - `python tools/export_field_pack.py --project-id P-123 --product-id SOIT-SCOMM-CF-CD-RAK-7266 --variant AS9231_BASIC_STATION_POE --out out/`

## CI
GitHub Actions runs validation + index build on push/PR (see `.github/workflows/validate.yml`).
