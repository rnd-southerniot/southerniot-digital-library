#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_DIR = ROOT / "products"
OUT_DIR = ROOT / ".index"
OUT_FILE = OUT_DIR / "library_index.json"

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "into",
    "your",
    "must",
    "only",
    "when",
    "then",
    "true",
    "false",
}


def _posix(p: Path) -> str:
    return p.as_posix()


def _product_and_state(rel_path: str) -> tuple[str | None, str | None]:
    # products/<type>/<product_id>/...
    parts = rel_path.split("/")
    if len(parts) < 4 or parts[0] != "products":
        return None, None
    product_id = parts[2]
    state = None
    if "states" in parts:
        try:
            idx = parts.index("states")
            state = parts[idx + 1]
        except Exception:
            state = None
    return product_id, state


def _flatten_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if obj is None:
        return out
    if isinstance(obj, (str, int, float, bool)):
        out.append(str(obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            out.append(str(k))
            out.extend(_flatten_strings(v))
    elif isinstance(obj, list):
        for item in obj:
            out.extend(_flatten_strings(item))
    return out


def _tokenize(text: str) -> list[str]:
    words = re.split(r"[^A-Za-z0-9_\\-]+", text.lower())
    words = [w for w in words if len(w) >= 3 and w not in STOPWORDS]
    return words


def _extract_keywords(path: Path) -> list[str]:
    rel = _posix(path.relative_to(ROOT))
    suffix = path.suffix.lower()
    text_blobs: list[str] = [rel, path.name]

    try:
        if suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            text_blobs.extend(_flatten_strings(data))
        elif suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            text_blobs.extend(_flatten_strings(data))
        elif suffix == ".csv":
            with path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i > 25:
                        break
                    text_blobs.extend(row)
        elif suffix == ".md":
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("#"):
                    text_blobs.append(line.lstrip("#").strip())
    except Exception:
        # Indexing is best-effort; validator enforces correctness elsewhere.
        pass

    tokens: list[str] = []
    for blob in text_blobs:
        tokens.extend(_tokenize(blob))
    return sorted(set(tokens))


def _load_state_roles(product_dir: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    states_dir = product_dir / "states"
    if not states_dir.exists():
        return out
    for sp in sorted(states_dir.glob("*/statepack.yaml")):
        state = sp.parent.name
        try:
            data = yaml.safe_load(sp.read_text(encoding="utf-8")) or {}
            roles = data.get("roles") if isinstance(data, dict) else None
            if isinstance(roles, list):
                out[state] = sorted([r for r in roles if isinstance(r, str)])
        except Exception:
            continue
    return out


def main() -> int:
    if not PRODUCTS_DIR.exists():
        raise SystemExit("products/ missing")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build roles cache per product
    product_dirs = sorted({p.parent for p in PRODUCTS_DIR.glob("**/manifest.yaml")})
    roles_cache: dict[str, dict[str, list[str]]] = {}
    for pd in product_dirs:
        pid = pd.name
        roles_cache[pid] = _load_state_roles(pd)

    docs: list[dict[str, Any]] = []
    file_globs = ("**/*.md", "**/*.yaml", "**/*.yml", "**/*.json", "**/*.csv")
    files: list[Path] = []
    for pat in file_globs:
        files.extend(PRODUCTS_DIR.glob(pat))
    for path in sorted(set(files), key=lambda p: _posix(p)):
        rel = _posix(path.relative_to(ROOT))
        product_id, state = _product_and_state(rel)
        if not product_id:
            continue
        roles = roles_cache.get(product_id, {}).get(state or "", []) if state else []
        keywords = _extract_keywords(path)
        doc_id = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:16]
        docs.append(
            {
                "doc_id": f"{product_id}:{doc_id}",
                "path": rel,
                "product_id": product_id,
                "state": state,
                "roles": roles,
                "keywords": keywords,
            }
        )

    payload = {"version": 1, "docs": docs}
    OUT_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[DPL-INDEX] Wrote {OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
