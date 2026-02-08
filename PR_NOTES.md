# PR: MFM384 edge-node product pack (complete states + Modbus assets)

## Summary
- Completes the `SOIT-SCOMM-CF-MD-RAK4630-RAK5802-MFM384` product pack to match the target layout:
  - `states/<state>/docs/sop.md`
  - `states/<state>/checklist.yaml`
  - `states/<state>/validations/*.yaml`
- Aligns `manifest.yaml` to new docs/validations paths and adds missing state requirement entries (`ready_for_installation`, `live`).
- Normalizes variant file name and keys (`variant_id`) to match manifest variant IDs.

## Review Notes
- Modbus defaults remain locked to `9600-N-8-1`.
- Evidence requirements remain enforced via `manifest.yaml` and validator rules.

## Risks / Rollback
- Medium risk: path moves require validator/indexer updates (handled in tooling PR).
- Rollback: revert this PR; no external systems impacted.
