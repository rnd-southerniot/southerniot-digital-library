# PR: RAK7266 gateway product pack (complete states)

## Summary
- Completes the `SOIT-SCOMM-CF-CD-RAK-7266` product pack to match the target layout:
  - `states/<state>/docs/sop.md`
  - `states/<state>/checklist.yaml`
  - `states/<state>/validations/*.yaml`
- Adds missing variants to support both Basic Station (default) and UDP packet forwarder.
- Updates `manifest.yaml` references to new docs/validations paths and adds missing state requirement entries (`ready_for_installation`, `live`).

## Review Notes
- Validation rules are policy checks; evaluator is implemented in tooling PR.
- Evidence photo requirements remain enforced via `manifest.yaml` and validator rules.

## Risks / Rollback
- Medium risk: path moves require validator/indexer updates (handled in tooling PR).
- Rollback: revert this PR; no external systems impacted.
