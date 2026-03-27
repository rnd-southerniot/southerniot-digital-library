# Release Notes (MFM384 Node)

Track changes to this product pack using the standard process in:
- `docs/release-notes-process.md`

## 2026-03-27 — docs-launch-gate-2026-03
- Summary: Established phase-2 documentation launch gate requirements and linked the latest published MFM384 artifact checksum record.
- Impact: Release approvals now require explicit artifact/checksum traceability in product release notes.
- Artifacts:
  - `NC-MFM384-REGISTER-MAP-2026-02-08` (`sha256: 0000000000000000000000000000000000000000000000000000000000000000`) from `integrations/nextcloud/artifact-index.yaml`
- Files:
  - `products/edge-nodes/SOIT-SCOMM-CF-MD-RAK4630-RAK5802-MFM384/release-notes/README.md`
  - `docs/release-notes-process.md`
  - `docs/runbooks/docs-launch-gate.md`
- Validation:
  - `./.venv/bin/python tools/validate_library.py` (pass)
- Follow-up: Edge-node product maintainer to replace placeholder artifact hash after next register-map publication.

## Entry Template
```md
## YYYY-MM-DD — <version-or-tag>
- Summary: one-line change statement.
- Impact: operator/CRM impact.
- Files:
  - `relative/path/one`
- Validation:
  - `./.venv/bin/python tools/validate_library.py` (pass/fail)
- Follow-up: optional actions.
```

## Notes
- Include firmware and codec version references when they change.
- Call out Modbus mapping changes (`modbus/`) as potentially breaking.
