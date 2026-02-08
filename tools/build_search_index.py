#!/usr/bin/env python3
"""Build a lightweight search index for the local AI agent (MVP).

Outputs a JSON file with:
- product_id, name, workstream
- state -> key docs / checklist ids / validation ids
"""
from __future__ import annotations
from pathlib import Path
import json, yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "integrations" / "search-index.json"

def main():
    entries = []
    for m in ROOT.glob("products/**/manifest.yaml"):
        d = yaml.safe_load(m.read_text())
        entries.append({
            "product_id": d.get("product_id"),
            "name": d.get("name"),
            "workstream": d.get("workstream"),
            "defaults": d.get("defaults", {}),
            "variants": d.get("variants", []),
            "state_requirements": d.get("state_requirements", {}),
            "path": str(m.parent.relative_to(ROOT)),
        })
    OUT.write_text(json.dumps({"products": entries}, indent=2))
    print(f"Wrote {OUT}")
if __name__ == "__main__":
    main()
