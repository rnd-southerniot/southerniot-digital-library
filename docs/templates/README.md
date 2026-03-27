# DPL Templates

Use these templates when creating new product packs or state artifacts.

## Available Templates
- `manifest.template.yaml`
- `statepack.template.yaml`
- `checklist.template.yaml`
- `validation.template.yaml`
- `sop.template.md`
- `release-note.template.md`

## Usage
1. Copy template into target product/state path.
2. Replace placeholder values.
3. Validate with:
```bash
./.venv/bin/python tools/validate_library.py
```
4. Add a release-note entry in the product `release-notes/README.md`.
