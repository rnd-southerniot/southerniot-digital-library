#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _posix(p: Path) -> str:
    return p.as_posix()


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _find_product_dir(product_id: str) -> Path:
    matches = sorted(ROOT.glob(f"products/**/{product_id}/manifest.yaml"))
    if not matches:
        raise ValueError(f"Unknown product_id: {product_id}")
    return matches[0].parent


def _variant_file(product_dir: Path, variant_id: str) -> Path:
    variants_dir = product_dir / "variants"
    for vf in sorted(variants_dir.glob("*.yaml")):
        data = _load_yaml(vf) or {}
        if isinstance(data, dict) and (data.get("variant_id") == variant_id or data.get("variant") == variant_id):
            return vf
    by_name = variants_dir / f"{variant_id}.yaml"
    if by_name.exists():
        return by_name
    raise ValueError(f"Variant not found: {variant_id} in {product_dir}")


def _copy_file(src: Path, dst_root: Path) -> None:
    rel = src.relative_to(ROOT)
    dst = dst_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _select_artifacts(product_ids: list[str]) -> dict[str, Any]:
    idx = ROOT / "integrations" / "nextcloud" / "artifact-index.yaml"
    if not idx.exists():
        return {"version": 1, "artifacts": []}
    data = _load_yaml(idx) or {}
    if not isinstance(data, dict) or not isinstance(data.get("artifacts"), list):
        return {"version": 1, "artifacts": []}

    tags: set[str] = set()
    for pid in product_ids:
        if "RAK-7266" in pid:
            tags.update({"vendor", "hardware"})
        if "MFM384" in pid:
            tags.update({"vendor", "modbus"})

    selected = []
    for art in data["artifacts"]:
        if not isinstance(art, dict):
            continue
        art_tags = art.get("tags") or []
        if isinstance(art_tags, list) and any(t in tags for t in art_tags if isinstance(t, str)):
            selected.append(art)

    return {"version": data.get("version", 1), "artifacts": selected}


def _write_readme(
    dst_root: Path,
    project_id: str,
    items: list[tuple[str, str]],
    states: list[str],
    role_filter: set[str] | None,
) -> None:
    lines = [
        f"# Field Pack — {project_id}",
        "",
        "## Contents",
        *[f"- `{pid}` variant `{vid}`" for pid, vid in items],
        "",
        "## Role Filter",
        f"- `{','.join(sorted(role_filter))}`" if role_filter else "- (none)",
        "",
        "## Requested States",
        *[f"- `{s}`" for s in states],
        "",
        "## How to Use (Offline)",
        "1. Open the SOP for the current CRM state under `products/.../states/<state>/docs/`.",
        "2. Complete `checklist.yaml` for the state (capture required photo evidence).",
        "3. Run validations listed under `products/.../states/<state>/validations/`.",
        "4. Attach outputs back to the CRM comment thread when online.",
        "",
        "Note: when a role filter is set, states whose `statepack.yaml` does not include the role are omitted.",
        "",
        "## Artifact References",
        "- Nextcloud artifacts are included as references only (no downloads).",
        "- See `integrations/nextcloud/artifact-index.subset.yaml`.",
        "",
    ]
    (dst_root / "FIELD_PACK_README.md").write_text("\n".join(lines), encoding="utf-8")


def _zip_dir(src_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted([p for p in src_dir.rglob("*") if p.is_file()], key=_posix):
            zf.write(file_path, arcname=_posix(file_path.relative_to(src_dir)))


def main() -> int:
    ap = argparse.ArgumentParser(description="Export offline Field Pack zip(s) from the DPL.")
    ap.add_argument("--project-id", required=True)
    ap.add_argument("--out", required=True, help="Output folder (zip written here)")
    ap.add_argument("--states", help="Comma-separated list of states (default: all)")
    ap.add_argument(
        "--roles",
        help="Comma-separated role IDs to filter states (e.g. FIELD_ENGINEER,SUPPORT). "
        "When set, only states whose statepack.roles intersects are included.",
    )

    ap.add_argument("--product-id", help="Single product_id")
    ap.add_argument("--variant", help="Single variant_id")
    ap.add_argument(
        "--product",
        action="append",
        help="Repeatable PRODUCT_ID@VARIANT_ID entries for combined export",
    )
    ap.add_argument("--combined", action="store_true", help="Create one combined zip when multiple products are provided")
    args = ap.parse_args()

    items: list[tuple[str, str]] = []
    if args.product:
        for spec in args.product:
            if "@" not in spec:
                raise SystemExit(f"Invalid --product value (expected PRODUCT_ID@VARIANT): {spec}")
            pid, vid = spec.split("@", 1)
            items.append((pid.strip(), vid.strip()))
    else:
        if not args.product_id or not args.variant:
            raise SystemExit("Provide either --product-id/--variant or one or more --product PRODUCT_ID@VARIANT")
        items = [(args.product_id, args.variant)]

    if args.states:
        states = [s.strip() for s in args.states.split(",") if s.strip()]
    else:
        # Authoritative default (mirrors states.yaml)
        states = [
            "initialized",
            "site_survey",
            "hardware_preparation",
            "firmware_generate",
            "lab_test",
            "ready_for_installation",
            "on_site_installation",
            "testing",
            "live",
            "maintenance",
        ]

    role_filter = None
    if args.roles:
        role_filter = {r.strip() for r in args.roles.split(",") if r.strip()}

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if len(items) > 1 and args.combined:
        zip_name = f"field-pack_{args.project_id}_combined_{timestamp}.zip"
        targets = [("combined", items)]
    else:
        targets = [(pid, [(pid, vid)]) for pid, vid in items]

    for label, bundle in targets:
        with tempfile.TemporaryDirectory() as tmp:
            dst_root = Path(tmp) / f"field-pack_{args.project_id}"
            dst_root.mkdir(parents=True, exist_ok=True)

            product_ids = [pid for pid, _ in bundle]
            # Copy shared integration references
            subset = _select_artifacts(product_ids)
            (dst_root / "integrations" / "nextcloud").mkdir(parents=True, exist_ok=True)
            (dst_root / "integrations" / "nextcloud" / "artifact-index.subset.yaml").write_text(
                yaml.safe_dump(subset, sort_keys=False),
                encoding="utf-8",
            )

            for pid, vid in bundle:
                product_dir = _find_product_dir(pid)
                _copy_file(product_dir / "manifest.yaml", dst_root)
                _copy_file(_variant_file(product_dir, vid), dst_root)

                # Product-level docs
                for extra_dir in ("docs", "troubleshooting", "release-notes", "modbus"):
                    p = product_dir / extra_dir
                    if p.exists():
                        for fp in sorted([x for x in p.rglob("*") if x.is_file()], key=_posix):
                            _copy_file(fp, dst_root)

                # State material
                for st in states:
                    st_dir = product_dir / "states" / st
                    if role_filter:
                        sp = st_dir / "statepack.yaml"
                        try:
                            sp_data = _load_yaml(sp) or {}
                            roles = sp_data.get("roles") if isinstance(sp_data, dict) else None
                            roles_set = {r for r in roles if isinstance(r, str)} if isinstance(roles, list) else set()
                        except Exception:
                            roles_set = set()
                        if not (roles_set & role_filter):
                            continue
                    for fp in [
                        st_dir / "statepack.yaml",
                        st_dir / "checklist.yaml",
                    ]:
                        if fp.exists():
                            _copy_file(fp, dst_root)
                    for folder in ("docs", "validations"):
                        p = st_dir / folder
                        if p.exists():
                            for fp in sorted([x for x in p.rglob("*") if x.is_file()], key=_posix):
                                _copy_file(fp, dst_root)

            _write_readme(dst_root, args.project_id, bundle, states, role_filter)

            zip_path = out_dir / (zip_name if label == "combined" else f"field-pack_{args.project_id}_{label}_{timestamp}.zip")
            _zip_dir(dst_root, zip_path)
            print(f"[DPL-FIELD-PACK] Wrote {zip_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
