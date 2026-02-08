#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, RefResolver

try:
    from rich.console import Console
    from rich.table import Table
except Exception:  # pragma: no cover
    Console = None  # type: ignore
    Table = None  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"
PRODUCTS_DIR = ROOT / "products"
INTEGRATIONS_DIR = ROOT / "integrations"


@dataclass(frozen=True)
class Finding:
    severity: str  # blocker | warning | info
    message: str
    path: str | None = None


def _posix(p: Path) -> str:
    return p.as_posix()


def _load_yaml(path: Path) -> Any:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"Failed to parse YAML: {path}: {e}") from e
    return data


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {path}: {e}") from e


def _extract_ids(value: Any, *, key: str, item_key: str = "id") -> list[str]:
    """
    Accepts either:
      - {key: ["A", "B"]}
      - {key: [{id: "A"}, {id: "B"}]}
    """
    if not isinstance(value, dict) or key not in value:
        raise ValueError(f"Missing key '{key}'")
    items = value[key]
    if not isinstance(items, list):
        raise ValueError(f"'{key}' must be a list")

    out: list[str] = []
    for item in items:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and isinstance(item.get(item_key), str):
            out.append(item[item_key])
        else:
            raise ValueError(f"Invalid '{key}' item: {item!r}")
    if len(out) != len(set(out)):
        raise ValueError(f"Duplicate IDs in '{key}'")
    return out


def _load_taxonomy() -> dict[str, list[str]]:
    taxonomy_files = {
        "states": ROOT / "states.yaml",
        "roles": ROOT / "roles.yaml",
        "severities": ROOT / "severities.yaml",
        "tags": ROOT / "tags.yaml",
    }
    for k, p in taxonomy_files.items():
        if not p.exists():
            raise ValueError(f"Missing taxonomy file: {p} (required)")

    states = _extract_ids(_load_yaml(taxonomy_files["states"]), key="states")
    roles = _extract_ids(_load_yaml(taxonomy_files["roles"]), key="roles")
    severities = _extract_ids(_load_yaml(taxonomy_files["severities"]), key="severities")
    tags_doc = _load_yaml(taxonomy_files["tags"])
    tags = _extract_ids(tags_doc, key="tags")
    photo_tags: list[str] = []
    if isinstance(tags_doc, dict) and "photo_tags" in tags_doc:
        photo_tags = _extract_ids(tags_doc, key="photo_tags")

    return {
        "states": states,
        "roles": roles,
        "severities": severities,
        "tags": tags,
        "photo_tags": photo_tags,
    }


def _load_schema_store() -> tuple[dict[str, Any], dict[str, Draft202012Validator]]:
    if not SCHEMAS_DIR.exists():
        raise ValueError("schemas/ folder missing")

    schemas: list[tuple[Path, Any]] = []
    for path in sorted(SCHEMAS_DIR.glob("*.schema.json")):
        schemas.append((path, _load_json(path)))

    store: dict[str, Any] = {}
    for path, schema in schemas:
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ValueError(f"Schema missing $id: {path}")
        store[schema_id] = schema

    validators: dict[str, Draft202012Validator] = {}
    for path, schema in schemas:
        name = path.name
        resolver = RefResolver.from_schema(schema, store=store)
        validators[name] = Draft202012Validator(schema, resolver=resolver)
    return store, validators


def _find_product_manifests() -> list[Path]:
    if not PRODUCTS_DIR.exists():
        raise ValueError("products/ folder missing")
    manifests = sorted(PRODUCTS_DIR.glob("**/manifest.yaml"))
    if not manifests:
        raise ValueError("No manifest.yaml found under products/")
    return manifests


def _read_variant_map(product_dir: Path) -> dict[str, Path]:
    variants_dir = product_dir / "variants"
    if not variants_dir.exists():
        return {}
    variant_map: dict[str, Path] = {}
    for vf in sorted(variants_dir.glob("*.yaml")):
        data = _load_yaml(vf) or {}
        if isinstance(data, dict):
            vid = data.get("variant_id") or data.get("variant")
            if isinstance(vid, str) and vid.strip():
                variant_map[vid] = vf
    return variant_map


def _validate_file(validator: Draft202012Validator, instance: Any, *, path: Path) -> None:
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.json_path)
    if errors:
        msg = errors[0].message
        raise ValueError(f"Schema validation failed for {path}: {msg}")


def _ensure(condition: bool, msg: str, *, path: Path | None = None, severity: str = "blocker") -> Finding | None:
    if condition:
        return None
    return Finding(severity=severity, message=msg, path=_posix(path) if path else None)


def _check_nextcloud_artifacts(tax: dict[str, list[str]]) -> list[Finding]:
    findings: list[Finding] = []
    idx = INTEGRATIONS_DIR / "nextcloud" / "artifact-index.yaml"
    if not idx.exists():
        f = _ensure(False, "Missing Nextcloud artifact index", path=idx)
        return [f] if f else []

    data = _load_yaml(idx) or {}
    if not isinstance(data, dict):
        return [Finding("blocker", "Nextcloud artifact index must be a mapping", _posix(idx))]

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        return [Finding("blocker", "artifact-index.yaml must include 'artifacts: []'", _posix(idx))]

    sha_re = re.compile(r"^[A-Fa-f0-9]{64}$")
    for art in artifacts:
        if not isinstance(art, dict):
            findings.append(Finding("blocker", "Artifact entry must be a mapping", _posix(idx)))
            continue
        for k in ("artifact_id", "sha256", "nextcloud_path"):
            if not isinstance(art.get(k), str) or not art.get(k):
                findings.append(Finding("blocker", f"Artifact missing required field '{k}'", _posix(idx)))
        sha = art.get("sha256")
        if isinstance(sha, str) and not sha_re.match(sha):
            findings.append(Finding("blocker", "Artifact sha256 must be 64 hex chars", _posix(idx)))
        if isinstance(sha, str) and sha == "0" * 64:
            findings.append(Finding("warning", "Artifact sha256 is placeholder all-zeros; replace after upload", _posix(idx)))
    return findings


def _check_integrations(states: list[str]) -> list[Finding]:
    findings: list[Finding] = []

    crm_dir = INTEGRATIONS_DIR / "crm"
    required = [
        crm_dir / "state-mapping.yaml",
        crm_dir / "parallel-workstreams.yaml",
        crm_dir / "notification-routing.yaml",
    ]
    for p in required:
        if not p.exists():
            findings.append(Finding("blocker", "Missing CRM integration mapping file", _posix(p)))
            return findings

    mapping = _load_yaml(crm_dir / "state-mapping.yaml") or {}
    mapped = []
    if isinstance(mapping, dict) and isinstance(mapping.get("states"), list):
        for row in mapping["states"]:
            if isinstance(row, dict):
                mapped.append((row.get("crm"), row.get("library")))
    missing = [s for s in states if (s, s) not in mapped]
    if missing:
        findings.append(Finding("blocker", f"CRM state-mapping missing states: {missing}", _posix(crm_dir / "state-mapping.yaml")))

    pw = _load_yaml(crm_dir / "parallel-workstreams.yaml") or {}
    deps = pw.get("dependencies") if isinstance(pw, dict) else None
    if not isinstance(deps, list):
        findings.append(Finding("blocker", "parallel-workstreams.yaml missing 'dependencies' list", _posix(crm_dir / "parallel-workstreams.yaml")))
        return findings

    def has_rule(kind: str, when_ws: str, when_state: str, req_ws: str, req_state: str) -> bool:
        for d in deps:
            if not isinstance(d, dict) or kind not in d:
                continue
            rule = d[kind]
            if not isinstance(rule, dict):
                continue
            when = rule.get("when") or {}
            requires = rule.get("requires") or rule.get("recommends") or {}
            if (
                when.get("workstream") == when_ws
                and when.get("state") == when_state
                and requires.get("workstream") == req_ws
                and requires.get("min_state") == req_state
            ):
                return True
        return False

    if not has_rule("blocker", "edge_node", "on_site_installation", "gateway", "ready_for_installation"):
        findings.append(Finding("blocker", "Missing dependency gate: edge_node:on_site_installation blocked until gateway>=ready_for_installation", _posix(crm_dir / "parallel-workstreams.yaml")))
    if not has_rule("warning", "edge_node", "testing", "gateway", "testing"):
        findings.append(Finding("blocker", "Missing dependency warning: edge_node:testing warns unless gateway>=testing", _posix(crm_dir / "parallel-workstreams.yaml")))

    # notification routing just needs to parse
    nr = _load_yaml(crm_dir / "notification-routing.yaml")
    if not isinstance(nr, dict):
        findings.append(Finding("blocker", "notification-routing.yaml must be a mapping", _posix(crm_dir / "notification-routing.yaml")))

    return findings


def _check_product(
    manifest_path: Path,
    states: list[str],
    validators: dict[str, Draft202012Validator],
) -> list[Finding]:
    findings: list[Finding] = []
    product_dir = manifest_path.parent
    product = _load_yaml(manifest_path) or {}
    if not isinstance(product, dict):
        return [Finding("blocker", "manifest.yaml must be a mapping", _posix(manifest_path))]

    _validate_file(validators["manifest.schema.json"], product, path=manifest_path)

    product_id = product.get("product_id", product_dir.name)

    # Policy checks
    defaults = product.get("defaults") or {}
    if not (isinstance(defaults, dict) and defaults.get("region") == "AS923-1"):
        findings.append(Finding("blocker", "defaults.region must be AS923-1", _posix(manifest_path)))

    if product_id == "SOIT-SCOMM-CF-CD-RAK-7266":
        if defaults.get("gateway_mode") != "basic_station":
            findings.append(Finding("blocker", "RAK7266 defaults.gateway_mode must be basic_station", _posix(manifest_path)))
        variants = product.get("variants") or []
        if not any(isinstance(v, str) and "UDP_PACKET_FORWARDER" in v for v in variants):
            findings.append(Finding("blocker", "RAK7266 must support an udp_packet_forwarder variant", _posix(manifest_path)))

    if product_id == "SOIT-SCOMM-CF-MD-RAK4630-RAK5802-MFM384":
        modbus = defaults.get("modbus") if isinstance(defaults, dict) else None
        if not isinstance(modbus, dict):
            findings.append(Finding("blocker", "MFM384 node must define defaults.modbus", _posix(manifest_path)))
        else:
            expected = {"baudrate": 9600, "parity": "N", "databits": 8, "stopbits": 1}
            for k, v in expected.items():
                if modbus.get(k) != v:
                    findings.append(Finding("blocker", "MFM384 modbus defaults must be 9600-N-8-1", _posix(manifest_path)))
                    break

    sr = product.get("state_requirements") or {}
    if not isinstance(sr, dict):
        findings.append(Finding("blocker", "state_requirements must be a mapping", _posix(manifest_path)))
        return findings

    # Evidence + approvals enforcement
    evidence_states = {"site_survey", "on_site_installation", "testing"}
    for st in evidence_states:
        req = sr.get(st) or {}
        if not isinstance(req, dict):
            findings.append(Finding("blocker", f"state_requirements.{st} must be a mapping", _posix(manifest_path)))
            continue
        ev = req.get("required_evidence") or {}
        if not (isinstance(ev, dict) and ev.get("photos_min") == 4 and ev.get("photos_max") == 5):
            findings.append(Finding("blocker", f"{product_id}:{st} must require 4–5 evidence photos", _posix(manifest_path)))
        tags = ev.get("required_photo_tags")
        if not (isinstance(tags, list) and 4 <= len([t for t in tags if isinstance(t, str) and t]) <= 8):
            findings.append(Finding("warning", f"{product_id}:{st} should list required_photo_tags", _posix(manifest_path)))

    fw = sr.get("firmware_generate") or {}
    if isinstance(fw, dict):
        approvals = fw.get("approvals")
        if approvals != ["RND_LEAD"]:
            findings.append(Finding("blocker", "firmware_generate approvals must be exactly [RND_LEAD]", _posix(manifest_path)))

    # File references in manifest
    for st, req in sorted(sr.items()):
        if not isinstance(req, dict):
            continue
        for doc in req.get("required_docs") or []:
            if isinstance(doc, str):
                p = product_dir / doc
                f = _ensure(p.exists(), f"{product_id}:{st} missing required doc: {doc}", path=p)
                if f:
                    findings.append(f)
        chk = req.get("required_checklist")
        if isinstance(chk, str):
            p = product_dir / chk
            f = _ensure(p.exists(), f"{product_id}:{st} missing checklist: {chk}", path=p)
            if f:
                findings.append(f)
        for v in req.get("validations") or []:
            if isinstance(v, str):
                p = product_dir / v
                f = _ensure(p.exists(), f"{product_id}:{st} missing validation: {v}", path=p)
                if f:
                    findings.append(f)

    # Variants map
    variant_map = _read_variant_map(product_dir)
    for vid in product.get("variants") or []:
        if not isinstance(vid, str):
            continue
        if vid not in variant_map and not (product_dir / "variants" / f"{vid}.yaml").exists():
            findings.append(Finding("blocker", f"{product_id}: missing variant file for {vid}", _posix(manifest_path)))

    # State folders
    states_dir = product_dir / "states"
    for st in states:
        st_dir = states_dir / st
        f = _ensure(st_dir.exists(), f"{product_id}: missing state folder {st_dir.relative_to(ROOT)}", path=st_dir)
        if f:
            findings.append(f)
            continue

        sp = st_dir / "statepack.yaml"
        f = _ensure(sp.exists(), f"{product_id}:{st} missing statepack.yaml", path=sp)
        if f:
            findings.append(f)
        else:
            sp_data = _load_yaml(sp) or {}
            _validate_file(validators["statepack.schema.json"], sp_data, path=sp)

        docs_dir = st_dir / "docs"
        if not docs_dir.exists() or not any(docs_dir.glob("*.md")):
            findings.append(Finding("blocker", f"{product_id}:{st} missing docs/*.md", _posix(st_dir)))

        checklist = st_dir / "checklist.yaml"
        if checklist.exists():
            chk_data = _load_yaml(checklist) or {}
            _validate_file(validators["checklist.schema.json"], chk_data, path=checklist)

        validations_dir = st_dir / "validations"
        if not validations_dir.exists() or not any(validations_dir.glob("*.yaml")):
            findings.append(Finding("blocker", f"{product_id}:{st} missing validations/*.yaml", _posix(st_dir)))
        else:
            for vf in sorted(validations_dir.glob("*.yaml")):
                vdata = _load_yaml(vf) or {}
                _validate_file(validators["validation.schema.json"], vdata, path=vf)

    return findings


def _print_summary(findings: list[Finding], checked: dict[str, int]) -> None:
    if Console and Table:
        console = Console()
        table = Table(title="DPL Validation Summary")
        table.add_column("Category")
        table.add_column("Checked", justify="right")
        table.add_column("Blockers", justify="right")
        table.add_column("Warnings", justify="right")
        table.add_row("taxonomy", str(checked.get("taxonomy", 0)),
                      str(sum(1 for f in findings if f.severity == "blocker" and (f.path or "").endswith(".yaml") and "taxonomy" in (f.path or ""))),  # best-effort
                      str(sum(1 for f in findings if f.severity == "warning")))
        table.add_row("products", str(checked.get("products", 0)),
                      str(sum(1 for f in findings if f.severity == "blocker")),
                      str(sum(1 for f in findings if f.severity == "warning")))
        console.print(table)
        for f in findings[:10]:
            loc = f" ({f.path})" if f.path else ""
            console.print(f"[{f.severity.upper()}] {f.message}{loc}")
    else:  # pragma: no cover
        print("DPL Validation Summary")
        print(f"Checked products: {checked.get('products', 0)}")
        for f in findings[:10]:
            loc = f" ({f.path})" if f.path else ""
            print(f"[{f.severity.upper()}] {f.message}{loc}")


def main() -> int:
    checked: dict[str, int] = {}
    findings: list[Finding] = []

    try:
        taxonomy = _load_taxonomy()
        checked["taxonomy"] = 1
    except Exception as e:
        findings.append(Finding("blocker", str(e)))
        _print_summary(findings, checked)
        return 2

    try:
        _, validators = _load_schema_store()
    except Exception as e:
        findings.append(Finding("blocker", str(e), _posix(SCHEMAS_DIR)))
        _print_summary(findings, checked)
        return 2

    # Integrations + Nextcloud
    findings.extend(_check_integrations(taxonomy["states"]))
    findings.extend(_check_nextcloud_artifacts(taxonomy))
    if any(f.severity == "blocker" for f in findings):
        _print_summary(findings, checked)
        return 2

    # Products (fail fast on first blocker)
    manifests = _find_product_manifests()
    checked["products"] = len(manifests)
    for mp in manifests:
        try:
            pf = _check_product(mp, taxonomy["states"], validators)
            findings.extend(pf)
        except Exception as e:
            findings.append(Finding("blocker", str(e), _posix(mp)))
        if any(f.severity == "blocker" for f in findings):
            _print_summary(findings, checked)
            return 2

    _print_summary(findings, checked)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
