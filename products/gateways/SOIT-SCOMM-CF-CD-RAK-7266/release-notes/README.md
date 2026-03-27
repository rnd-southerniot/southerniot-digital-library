# Release Notes (RAK7266)

Track changes to this product pack using the standard process in:
- `docs/release-notes-process.md`

## 2026-03-27 — docs-launch-gate-2026-03
- Summary: Established phase-2 documentation launch gate requirements and linked the latest published gateway vendor artifact checksum record.
- Impact: Release approvals now require explicit artifact/checksum traceability in product release notes.
- Artifacts:
  - `NC-RAK7266-VENDOR-PDFS-2026-02-08` (`sha256: 0000000000000000000000000000000000000000000000000000000000000000`) from `integrations/nextcloud/artifact-index.yaml`
- Files:
  - `products/gateways/SOIT-SCOMM-CF-CD-RAK-7266/release-notes/README.md`
  - `docs/release-notes-process.md`
  - `docs/runbooks/docs-launch-gate.md`
- Validation:
  - `./.venv/bin/python tools/validate_library.py` (pass)
- Follow-up: Gateway product maintainer to replace placeholder artifact hash after next vendor PDF upload.

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
- Use SemVer for firmware/config bundle labels where applicable.
- Include state names when changes affect workflow gates or evidence requirements.
