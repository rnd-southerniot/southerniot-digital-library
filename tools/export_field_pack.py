#!/usr/bin/env python3
"""Export an offline field pack for a project/workstream (MVP).

This script is intentionally simple:
- Copies statepacks + checklists + referenced docs into an output folder.
- Nextcloud artifacts are exported as references (unless separately downloaded).
"""
from __future__ import annotations
import shutil
from pathlib import Path
import argparse, yaml

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--product-path", required=True, help="e.g. products/gateways/.../SOIT-...")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    prod = ROOT / args.product_path
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    shutil.copytree(prod / "states", out / "states", dirs_exist_ok=True)
    # copy troubleshooting
    if (prod/"troubleshooting").exists():
        shutil.copytree(prod/"troubleshooting", out/"troubleshooting", dirs_exist_ok=True)

    # copy manifest
    shutil.copy2(prod/"manifest.yaml", out/"manifest.yaml")
    print(f"Exported field pack to {out}")

if __name__ == "__main__":
    main()
