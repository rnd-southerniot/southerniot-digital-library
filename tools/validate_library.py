#!/usr/bin/env python3
"""Validate SouthernIoT Digital Product Library structure.

MVP validator:
- Ensures each product has manifest.yaml
- Ensures each state folder has statepack.yaml
- Ensures checklists/validations referenced in manifest exist
"""
from __future__ import annotations
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "products"

STATES = [
  "initialized","site_survey","hardware_preparation","firmware_generate","lab_test",
  "ready_for_installation","on_site_installation","testing","live","maintenance"
]

def die(msg: str) -> None:
    print(f"[DPL-VALIDATE] ERROR: {msg}")
    sys.exit(2)

def main() -> int:
    if not PRODUCTS.exists():
        die("products/ folder missing")

    manifests = list(PRODUCTS.glob("**/manifest.yaml"))
    if not manifests:
        die("No manifest.yaml found under products/")

    for m in manifests:
        data = yaml.safe_load(m.read_text())
        pid = data.get("product_id", m.parent.name)
        # check states
        states_dir = m.parent / "states"
        for s in STATES:
            sp = states_dir / s / "statepack.yaml"
            if not sp.exists():
                die(f"{pid}: missing {sp.relative_to(ROOT)}")

        # check references
        sr = data.get("state_requirements", {}) or {}
        for state, req in sr.items():
            chk = req.get("required_checklist")
            if chk:
                p = m.parent / chk
                if not p.exists():
                    die(f"{pid}: checklist ref missing: {chk}")
            for v in (req.get("validations") or []):
                p = m.parent / v
                if not p.exists():
                    die(f"{pid}: validation ref missing: {v}")

    print("[DPL-VALIDATE] OK ✅")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
