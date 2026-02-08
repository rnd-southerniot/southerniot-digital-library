# PR: Tooling + CI (validator, indexer, field pack exporter)

## Summary
- Implements production-grade tooling:
  - `tools/validate_library.py`: schema + policy validator with non-zero exit codes
  - `tools/build_search_index.py`: deterministic `.index/library_index.json`
  - `tools/export_field_pack.py`: zipped offline field pack exporter (single or combined)
- Adds `tools/requirements.txt` and GitHub Actions workflow `.github/workflows/validate.yml`.

## Review Notes
- Validator enforces non-negotiables: evidence photo counts, firmware approvals, AS923-1 default, RAK7266 modes, MFM384 Modbus defaults, CRM gates, Nextcloud artifact references.
- Field pack exporter includes Nextcloud references only (no downloads).

## Risks / Rollback
- Medium risk: stricter validator may require content updates (handled in product/skeleton/schema PRs).
- Rollback: revert tooling PR; content remains intact.
