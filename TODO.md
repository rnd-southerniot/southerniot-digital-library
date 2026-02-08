# SouthernIoT DPL — Execution Plan (Multi-Agent)

This repo is built in parallel workstreams using git branches/worktrees.

## Agent A — Repo Architect (`feat/repo-skeleton`)
- [ ] Ensure repo structure matches target layout
- [ ] Create root taxonomy files: `states.yaml`, `roles.yaml`, `severities.yaml`, `tags.yaml`
- [ ] Ensure integrations mapping YAMLs exist and align to authoritative states
- [ ] Ensure product folders exist for both products and all states exist
- [ ] Write `TODO.md` and `DECISIONS.md`
- Acceptance:
  - Tree matches required layout
  - Authoritative states match exactly and in order

## Agent B — Schema Engineer (`feat/schemas`)
- [ ] Implement strict JSON Schemas in `schemas/` (no drift)
- [ ] Ensure all manifests/statepacks/checklists/validations validate
- Acceptance:
  - `tools/validate_library.py` validates schemas + content and exits non-zero on failures

## Agent C — Product Librarian (RAK7266) (`feat/rak7266-pack`)
- [ ] Populate product pack for `SOIT-SCOMM-CF-CD-RAK-7266`
- [ ] Ensure Basic Station default; UDP packet forwarder supported by variant
- [ ] Ensure state folders for all authoritative states, with docs/checklists/validations
- Acceptance:
  - Validator passes product-specific rules for RAK7266

## Agent D — Product Librarian (MFM384 Node) (`feat/mfm384-pack`)
- [ ] Populate product pack for `SOIT-SCOMM-CF-MD-RAK4630-RAK5802-MFM384`
- [ ] Provide Modbus folder contents (CSV/YAML/JSON/MD)
- [ ] Enforce defaults `9600-N-8-1` and evidence requirements
- Acceptance:
  - Validator passes product-specific rules for MFM384 node

## Agent E — Tooling/Automation Engineer (`feat/tooling-ci`)
- [ ] Implement validator, search index builder, field pack exporter
- [ ] Add CI workflow `.github/workflows/validate.yml`
- [ ] Provide `tools/requirements.txt`
- Acceptance:
  - CI runs validator + index build
  - Field pack export produces a zip successfully
