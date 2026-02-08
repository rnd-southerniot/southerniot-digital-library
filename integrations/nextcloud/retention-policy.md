# Nextcloud Retention Policy (DPL)

## Stored in Nextcloud
- Vendor PDFs (manufacturer manuals, datasheets)
- Firmware bundles (binaries, build artifacts, release zips)
- Large diagrams and training decks

## Stored in Git
- Manifests, statepacks, checklists, validations
- Index references to Nextcloud artifacts (immutable IDs + hashes)

## Immutability
Every Nextcloud artifact referenced by the DPL must have:
- `artifact_id`
- `sha256`
- `version`
so that AI/CRM can reference exact content.

