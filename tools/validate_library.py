#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SEVERITY_ORDER = {"blocker": 0, "warning": 1, "info": 2}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str  # blocker | warning | info
    message: str
    path: str | None = None
    details: dict[str, Any] | None = None


@dataclass(frozen=True)
class Paths:
    root: Path
    schemas_dir: Path
    products_dir: Path
    integrations_dir: Path


def _paths_for_root(root: Path) -> Paths:
    return Paths(
        root=root,
        schemas_dir=root / "schemas",
        products_dir=root / "products",
        integrations_dir=root / "integrations",
    )


def _posix(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _load_yaml(path: Path) -> Any:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to parse YAML: {path}: {exc}") from exc
    return data


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to parse JSON: {path}: {exc}") from exc


def _extract_ids(value: Any, *, key: str, item_key: str = "id") -> list[str]:
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


def _load_taxonomy(paths: Paths) -> dict[str, list[str]]:
    taxonomy_files = {
        "states": paths.root / "states.yaml",
        "roles": paths.root / "roles.yaml",
        "severities": paths.root / "severities.yaml",
        "tags": paths.root / "tags.yaml",
    }
    for name, path in taxonomy_files.items():
        if not path.exists():
            raise ValueError(f"Missing taxonomy file: {path} (required for {name})")

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


def _load_schema_store(paths: Paths) -> tuple[dict[str, Any], dict[str, Draft202012Validator]]:
    if not paths.schemas_dir.exists():
        raise ValueError("schemas/ folder missing")

    schemas: list[tuple[Path, Any]] = []
    for path in sorted(paths.schemas_dir.glob("*.schema.json")):
        schemas.append((path, _load_json(path)))

    store: dict[str, Any] = {}
    for path, schema in schemas:
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ValueError(f"Schema missing $id: {path}")
        store[schema_id] = schema

    registry = Registry().with_resources(
        [(schema_id, Resource.from_contents(schema)) for schema_id, schema in store.items()]
    )

    validators: dict[str, Draft202012Validator] = {}
    for path, schema in schemas:
        validators[path.name] = Draft202012Validator(schema, registry=registry)
    return store, validators


def _schema_enum(schema: dict[str, Any], *path: str) -> set[str]:
    node: Any = schema
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return set()
        node = node[key]
    if not isinstance(node, list):
        return set()
    values = {item for item in node if isinstance(item, str)}
    return values


def _check_taxonomy_drift(
    *,
    paths: Paths,
    taxonomy: dict[str, list[str]],
    validators_by_name: dict[str, Draft202012Validator],
) -> list[Finding]:
    findings: list[Finding] = []
    required_validators = (
        "manifest.schema.json",
        "statepack.schema.json",
        "validation.schema.json",
    )
    missing_validators = sorted(
        validator_name for validator_name in required_validators if validator_name not in validators_by_name
    )
    if missing_validators:
        findings.append(
            Finding(
                code="taxonomy_drift_schema_missing",
                severity="blocker",
                message="Cannot compare taxonomy enums because required core schemas are missing",
                path=_posix(paths.schemas_dir, root=paths.root),
                details={"missing_schemas": missing_validators},
            )
        )
        return findings

    manifest_schema = validators_by_name["manifest.schema.json"].schema
    statepack_schema = validators_by_name["statepack.schema.json"].schema
    validation_schema = validators_by_name["validation.schema.json"].schema

    taxonomy_states = set(taxonomy["states"])
    schema_states = _schema_enum(manifest_schema, "properties", "state_requirements", "propertyNames", "enum")
    schema_states |= _schema_enum(statepack_schema, "properties", "state", "enum")
    schema_states |= _schema_enum(validation_schema, "properties", "when_state", "enum")
    extra_states = sorted(schema_states - taxonomy_states)
    missing_states = sorted(taxonomy_states - schema_states)
    if extra_states or missing_states:
        findings.append(
            Finding(
                code="taxonomy_drift_states",
                severity="blocker",
                message="State taxonomy drifts from schema enums",
                path=_posix(paths.root / "states.yaml", root=paths.root),
                details={"extra_in_schema": extra_states, "missing_in_schema": missing_states},
            )
        )

    taxonomy_roles = set(taxonomy["roles"])
    schema_roles = _schema_enum(statepack_schema, "properties", "roles", "items", "enum")
    extra_roles = sorted(schema_roles - taxonomy_roles)
    missing_roles = sorted(taxonomy_roles - schema_roles)
    if extra_roles or missing_roles:
        findings.append(
            Finding(
                code="taxonomy_drift_roles",
                severity="blocker",
                message="Role taxonomy drifts from schema enums",
                path=_posix(paths.root / "roles.yaml", root=paths.root),
                details={"extra_in_schema": extra_roles, "missing_in_schema": missing_roles},
            )
        )

    taxonomy_severities = set(taxonomy["severities"])
    schema_severities = _schema_enum(validation_schema, "properties", "severity", "enum")
    extra_severities = sorted(schema_severities - taxonomy_severities)
    missing_severities = sorted(taxonomy_severities - schema_severities)
    if extra_severities or missing_severities:
        findings.append(
            Finding(
                code="taxonomy_drift_severities",
                severity="blocker",
                message="Severity taxonomy drifts from schema enums",
                path=_posix(paths.root / "severities.yaml", root=paths.root),
                details={"extra_in_schema": extra_severities, "missing_in_schema": missing_severities},
            )
        )

    return findings


def _find_product_manifests(paths: Paths) -> list[Path]:
    if not paths.products_dir.exists():
        raise ValueError("products/ folder missing")
    manifests = sorted(paths.products_dir.glob("**/manifest.yaml"))
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
    errors = sorted(validator.iter_errors(instance), key=lambda err: err.json_path)
    if errors:
        raise ValueError(f"Schema validation failed for {path}: {errors[0].message}")


def _placeholder_hash_kind(value: str) -> str | None:
    lower = value.lower()
    if lower == "0" * 64:
        return "zeros"
    if re.fullmatch(r"(.)\1{63}", lower):
        return "repeated-char"
    if re.fullmatch(r"(?:deadbeef){8}", lower):
        return "deadbeef"
    if lower in {"todo", "tbd", "placeholder", "replace_me"}:
        return "token"
    return None


def _check_nextcloud_artifacts(paths: Paths, taxonomy: dict[str, list[str]]) -> list[Finding]:
    findings: list[Finding] = []
    idx = paths.integrations_dir / "nextcloud" / "artifact-index.yaml"
    if not idx.exists():
        return [
            Finding(
                code="integrations_nextcloud_index_missing",
                severity="blocker",
                message="Missing Nextcloud artifact index",
                path=_posix(idx, root=paths.root),
            )
        ]

    data = _load_yaml(idx) or {}
    if not isinstance(data, dict):
        return [
            Finding(
                code="integrations_nextcloud_index_format",
                severity="blocker",
                message="Nextcloud artifact index must be a mapping",
                path=_posix(idx, root=paths.root),
            )
        ]

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        return [
            Finding(
                code="integrations_nextcloud_artifacts_missing",
                severity="blocker",
                message="artifact-index.yaml must include 'artifacts: []'",
                path=_posix(idx, root=paths.root),
            )
        ]

    tag_set = set(taxonomy["tags"])
    artifact_ids: set[str] = set()
    sha_re = re.compile(r"^[A-Fa-f0-9]{64}$")
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            findings.append(
                Finding(
                    code="integrations_nextcloud_artifact_entry_format",
                    severity="blocker",
                    message="Artifact entry must be a mapping",
                    path=_posix(idx, root=paths.root),
                )
            )
            continue

        artifact_id = artifact.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            findings.append(
                Finding(
                    code="integrations_nextcloud_artifact_id_missing",
                    severity="blocker",
                    message="Artifact missing required field 'artifact_id'",
                    path=_posix(idx, root=paths.root),
                )
            )
        elif artifact_id in artifact_ids:
            findings.append(
                Finding(
                    code="integrations_nextcloud_artifact_id_duplicate",
                    severity="blocker",
                    message="Duplicate artifact_id in Nextcloud index",
                    path=_posix(idx, root=paths.root),
                    details={"artifact_id": artifact_id},
                )
            )
        else:
            artifact_ids.add(artifact_id)

        for key in ("sha256", "nextcloud_path"):
            if not isinstance(artifact.get(key), str) or not artifact.get(key):
                findings.append(
                    Finding(
                        code=f"integrations_nextcloud_{key}_missing",
                        severity="blocker",
                        message=f"Artifact missing required field '{key}'",
                        path=_posix(idx, root=paths.root),
                    )
                )

        sha = artifact.get("sha256")
        if isinstance(sha, str):
            if not sha_re.match(sha):
                findings.append(
                    Finding(
                        code="integrations_nextcloud_sha256_format",
                        severity="blocker",
                        message="Artifact sha256 must be 64 hex chars",
                        path=_posix(idx, root=paths.root),
                    )
                )
            else:
                placeholder_kind = _placeholder_hash_kind(sha)
                if placeholder_kind == "zeros":
                    findings.append(
                        Finding(
                            code="placeholder_hash",
                            severity="warning",
                            message="Artifact sha256 is all-zeros placeholder; replace after upload",
                            path=_posix(idx, root=paths.root),
                            details={"artifact_id": artifact_id, "kind": placeholder_kind},
                        )
                    )
                elif placeholder_kind:
                    findings.append(
                        Finding(
                            code="placeholder_hash",
                            severity="blocker",
                            message="Artifact sha256 appears to use a placeholder hash",
                            path=_posix(idx, root=paths.root),
                            details={"artifact_id": artifact_id, "kind": placeholder_kind},
                        )
                    )

        tags = artifact.get("tags")
        if isinstance(tags, list):
            unknown_tags = sorted(tag for tag in tags if isinstance(tag, str) and tag not in tag_set)
            if unknown_tags:
                findings.append(
                    Finding(
                        code="taxonomy_unknown_artifact_tag",
                        severity="blocker",
                        message="Artifact tag is not defined in tags.yaml",
                        path=_posix(idx, root=paths.root),
                        details={"artifact_id": artifact_id, "unknown_tags": unknown_tags},
                    )
                )

    return findings


def _check_integrations(paths: Paths, states: list[str]) -> list[Finding]:
    findings: list[Finding] = []

    crm_dir = paths.integrations_dir / "crm"
    required = [
        crm_dir / "state-mapping.yaml",
        crm_dir / "parallel-workstreams.yaml",
        crm_dir / "notification-routing.yaml",
    ]
    for path in required:
        if not path.exists():
            findings.append(
                Finding(
                    code="integrations_crm_file_missing",
                    severity="blocker",
                    message="Missing CRM integration mapping file",
                    path=_posix(path, root=paths.root),
                )
            )
            return findings

    mapping_path = crm_dir / "state-mapping.yaml"
    mapping = _load_yaml(mapping_path) or {}
    mapped: list[tuple[str, str]] = []
    if isinstance(mapping, dict) and isinstance(mapping.get("states"), list):
        for row in mapping["states"]:
            if isinstance(row, dict):
                mapped.append((row.get("crm"), row.get("library")))
    missing_states = [state for state in states if (state, state) not in mapped]
    if missing_states:
        findings.append(
            Finding(
                code="integrations_crm_state_mapping_missing",
                severity="blocker",
                message="CRM state-mapping missing library states",
                path=_posix(mapping_path, root=paths.root),
                details={"missing_states": missing_states},
            )
        )

    pw_path = crm_dir / "parallel-workstreams.yaml"
    pw = _load_yaml(pw_path) or {}
    dependencies = pw.get("dependencies") if isinstance(pw, dict) else None
    if not isinstance(dependencies, list):
        findings.append(
            Finding(
                code="integrations_crm_parallel_dependencies_missing",
                severity="blocker",
                message="parallel-workstreams.yaml missing 'dependencies' list",
                path=_posix(pw_path, root=paths.root),
            )
        )
        return findings

    def has_rule(kind: str, when_ws: str, when_state: str, req_ws: str, req_state: str) -> bool:
        for dependency in dependencies:
            if not isinstance(dependency, dict) or kind not in dependency:
                continue
            rule = dependency[kind]
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
        findings.append(
            Finding(
                code="integrations_dependency_gate_missing",
                severity="blocker",
                message="Missing dependency gate for edge_node:on_site_installation",
                path=_posix(pw_path, root=paths.root),
            )
        )
    if not has_rule("warning", "edge_node", "testing", "gateway", "testing"):
        findings.append(
            Finding(
                code="integrations_dependency_warning_missing",
                severity="blocker",
                message="Missing dependency warning for edge_node:testing",
                path=_posix(pw_path, root=paths.root),
            )
        )

    routing_path = crm_dir / "notification-routing.yaml"
    routing = _load_yaml(routing_path)
    if not isinstance(routing, dict):
        findings.append(
            Finding(
                code="integrations_crm_notification_routing_format",
                severity="blocker",
                message="notification-routing.yaml must be a mapping",
                path=_posix(routing_path, root=paths.root),
            )
        )

    return findings


def _check_product(
    *,
    paths: Paths,
    manifest_path: Path,
    taxonomy: dict[str, list[str]],
    validators: dict[str, Draft202012Validator],
    checked: dict[str, int],
) -> list[Finding]:
    findings: list[Finding] = []
    product_dir = manifest_path.parent
    product = _load_yaml(manifest_path) or {}
    if not isinstance(product, dict):
        return [
            Finding(
                code="manifest_format",
                severity="blocker",
                message="manifest.yaml must be a mapping",
                path=_posix(manifest_path, root=paths.root),
            )
        ]

    _validate_file(validators["manifest.schema.json"], product, path=manifest_path)
    checked["manifests"] = checked.get("manifests", 0) + 1

    product_id = product.get("product_id", product_dir.name)

    defaults = product.get("defaults") or {}
    if not (isinstance(defaults, dict) and defaults.get("region") == "AS923-1"):
        findings.append(
            Finding(
                code="policy_region_as9231",
                severity="blocker",
                message="defaults.region must be AS923-1",
                path=_posix(manifest_path, root=paths.root),
            )
        )

    if product_id == "SOIT-SCOMM-CF-CD-RAK-7266":
        if defaults.get("gateway_mode") != "basic_station":
            findings.append(
                Finding(
                    code="policy_gateway_mode_default",
                    severity="blocker",
                    message="RAK7266 defaults.gateway_mode must be basic_station",
                    path=_posix(manifest_path, root=paths.root),
                )
            )
        variants = product.get("variants") or []
        if not any(isinstance(variant, str) and "UDP_PACKET_FORWARDER" in variant for variant in variants):
            findings.append(
                Finding(
                    code="policy_gateway_variant_udp_required",
                    severity="blocker",
                    message="RAK7266 must support a UDP packet forwarder variant",
                    path=_posix(manifest_path, root=paths.root),
                )
            )

    if product_id == "SOIT-SCOMM-CF-MD-RAK4630-RAK5802-MFM384":
        modbus = defaults.get("modbus") if isinstance(defaults, dict) else None
        if not isinstance(modbus, dict):
            findings.append(
                Finding(
                    code="policy_modbus_defaults_missing",
                    severity="blocker",
                    message="MFM384 node must define defaults.modbus",
                    path=_posix(manifest_path, root=paths.root),
                )
            )
        else:
            expected = {"baudrate": 9600, "parity": "N", "databits": 8, "stopbits": 1}
            for key, expected_value in expected.items():
                if modbus.get(key) != expected_value:
                    findings.append(
                        Finding(
                            code="policy_modbus_defaults_9600_n_8_1",
                            severity="blocker",
                            message="MFM384 modbus defaults must be 9600-N-8-1",
                            path=_posix(manifest_path, root=paths.root),
                        )
                    )
                    break

    state_requirements = product.get("state_requirements") or {}
    if not isinstance(state_requirements, dict):
        return findings + [
            Finding(
                code="manifest_state_requirements_format",
                severity="blocker",
                message="state_requirements must be a mapping",
                path=_posix(manifest_path, root=paths.root),
            )
        ]

    known_states = set(taxonomy["states"])
    unknown_sr_states = sorted(state for state in state_requirements if state not in known_states)
    if unknown_sr_states:
        findings.append(
            Finding(
                code="taxonomy_unknown_state_reference",
                severity="blocker",
                message="Manifest references unknown states in state_requirements",
                path=_posix(manifest_path, root=paths.root),
                details={"unknown_states": unknown_sr_states},
            )
        )

    role_set = set(taxonomy["roles"])
    photo_tag_set = set(taxonomy["photo_tags"])
    severity_set = set(taxonomy["severities"])

    evidence_states = {"site_survey", "on_site_installation", "testing"}
    for state in evidence_states:
        req = state_requirements.get(state) or {}
        if not isinstance(req, dict):
            findings.append(
                Finding(
                    code="manifest_state_requirement_format",
                    severity="blocker",
                    message=f"state_requirements.{state} must be a mapping",
                    path=_posix(manifest_path, root=paths.root),
                )
            )
            continue
        evidence = req.get("required_evidence") or {}
        if not (isinstance(evidence, dict) and evidence.get("photos_min") == 4 and evidence.get("photos_max") == 5):
            findings.append(
                Finding(
                    code="policy_required_evidence_range",
                    severity="blocker",
                    message=f"{product_id}:{state} must require 4-5 evidence photos",
                    path=_posix(manifest_path, root=paths.root),
                )
            )

    fw_req = state_requirements.get("firmware_generate") or {}
    if isinstance(fw_req, dict) and fw_req.get("approvals") != ["RND_LEAD"]:
        findings.append(
            Finding(
                code="policy_firmware_approvals",
                severity="blocker",
                message="firmware_generate approvals must be exactly [RND_LEAD]",
                path=_posix(manifest_path, root=paths.root),
            )
        )

    for state, req in sorted(state_requirements.items()):
        if not isinstance(req, dict):
            continue

        approvals = req.get("approvals") or []
        if isinstance(approvals, list):
            unknown_approvers = sorted(role for role in approvals if isinstance(role, str) and role not in role_set)
            if unknown_approvers:
                findings.append(
                    Finding(
                        code="taxonomy_unknown_role_reference",
                        severity="blocker",
                        message="Manifest approvals include unknown role(s)",
                        path=_posix(manifest_path, root=paths.root),
                        details={"state": state, "unknown_roles": unknown_approvers},
                    )
                )

        evidence = req.get("required_evidence") or {}
        if isinstance(evidence, dict):
            required_photo_tags = evidence.get("required_photo_tags") or []
            if isinstance(required_photo_tags, list):
                unknown_photo_tags = sorted(
                    tag for tag in required_photo_tags if isinstance(tag, str) and tag not in photo_tag_set
                )
                if unknown_photo_tags:
                    findings.append(
                        Finding(
                            code="taxonomy_unknown_photo_tag_reference",
                            severity="warning",
                            message="Manifest required_photo_tags include unknown taxonomy tag(s)",
                            path=_posix(manifest_path, root=paths.root),
                            details={"state": state, "unknown_photo_tags": unknown_photo_tags},
                        )
                    )

        for doc in req.get("required_docs") or []:
            if isinstance(doc, str):
                target = product_dir / doc
                if not target.exists():
                    findings.append(
                        Finding(
                            code="crossref_required_doc_missing",
                            severity="blocker",
                            message=f"{product_id}:{state} missing required doc: {doc}",
                            path=_posix(target, root=paths.root),
                        )
                    )

        declared_checklist = req.get("required_checklist")
        if isinstance(declared_checklist, str):
            checklist_path = product_dir / declared_checklist
            if not checklist_path.exists():
                findings.append(
                    Finding(
                        code="crossref_required_checklist_missing",
                        severity="blocker",
                        message=f"{product_id}:{state} missing checklist: {declared_checklist}",
                        path=_posix(checklist_path, root=paths.root),
                    )
                )
            else:
                checklist_data = _load_yaml(checklist_path) or {}
                _validate_file(validators["checklist.schema.json"], checklist_data, path=checklist_path)

        declared_validation_paths = {
            value for value in req.get("validations") or [] if isinstance(value, str)
        }
        for rel_validation_path in sorted(declared_validation_paths):
            validation_path = product_dir / rel_validation_path
            if not validation_path.exists():
                findings.append(
                    Finding(
                        code="crossref_validation_missing",
                        severity="blocker",
                        message=f"{product_id}:{state} missing validation: {rel_validation_path}",
                        path=_posix(validation_path, root=paths.root),
                    )
                )
                continue
            validation_data = _load_yaml(validation_path) or {}
            _validate_file(validators["validation.schema.json"], validation_data, path=validation_path)
            checked["validations"] = checked.get("validations", 0) + 1
            if validation_data.get("when_state") != state:
                findings.append(
                    Finding(
                        code="crossref_validation_state_mismatch",
                        severity="blocker",
                        message="Validation when_state must match manifest state_requirements key",
                        path=_posix(validation_path, root=paths.root),
                        details={"manifest_state": state, "when_state": validation_data.get("when_state")},
                    )
                )
            sev = validation_data.get("severity")
            if isinstance(sev, str) and sev not in severity_set:
                findings.append(
                    Finding(
                        code="taxonomy_unknown_validation_severity",
                        severity="blocker",
                        message="Validation severity is not defined in severities.yaml",
                        path=_posix(validation_path, root=paths.root),
                        details={"severity": sev},
                    )
                )

    variant_map = _read_variant_map(product_dir)
    for variant_id in product.get("variants") or []:
        if isinstance(variant_id, str):
            if variant_id not in variant_map and not (product_dir / "variants" / f"{variant_id}.yaml").exists():
                findings.append(
                    Finding(
                        code="crossref_variant_file_missing",
                        severity="blocker",
                        message=f"{product_id}: missing variant file for {variant_id}",
                        path=_posix(manifest_path, root=paths.root),
                    )
                )

    states_dir = product_dir / "states"
    for state in taxonomy["states"]:
        state_dir = states_dir / state
        if not state_dir.exists():
            findings.append(
                Finding(
                    code="crossref_state_folder_missing",
                    severity="blocker",
                    message=f"{product_id}: missing state folder {state_dir.relative_to(paths.root)}",
                    path=_posix(state_dir, root=paths.root),
                )
            )
            continue
        checked["state_folders"] = checked.get("state_folders", 0) + 1

        statepack_path = state_dir / "statepack.yaml"
        if not statepack_path.exists():
            findings.append(
                Finding(
                    code="crossref_statepack_missing",
                    severity="blocker",
                    message=f"{product_id}:{state} missing statepack.yaml",
                    path=_posix(statepack_path, root=paths.root),
                )
            )
        else:
            statepack_data = _load_yaml(statepack_path) or {}
            _validate_file(validators["statepack.schema.json"], statepack_data, path=statepack_path)
            checked["statepacks"] = checked.get("statepacks", 0) + 1

            if statepack_data.get("state") != state:
                findings.append(
                    Finding(
                        code="crossref_statepack_state_mismatch",
                        severity="blocker",
                        message="statepack.state must match its state folder",
                        path=_posix(statepack_path, root=paths.root),
                        details={"folder_state": state, "statepack_state": statepack_data.get("state")},
                    )
                )

            statepack_roles = statepack_data.get("roles") or []
            unknown_roles = sorted(
                role for role in statepack_roles if isinstance(role, str) and role not in role_set
            )
            if unknown_roles:
                findings.append(
                    Finding(
                        code="taxonomy_unknown_statepack_role",
                        severity="blocker",
                        message="statepack roles contain unknown role(s)",
                        path=_posix(statepack_path, root=paths.root),
                        details={"unknown_roles": unknown_roles},
                    )
                )

            statepack_evidence = statepack_data.get("required_evidence") or {}
            if isinstance(statepack_evidence, dict):
                statepack_tags = statepack_evidence.get("required_photo_tags") or []
                if isinstance(statepack_tags, list):
                    unknown_statepack_tags = sorted(
                        tag for tag in statepack_tags if isinstance(tag, str) and tag not in photo_tag_set
                    )
                    if unknown_statepack_tags:
                        findings.append(
                            Finding(
                                code="taxonomy_unknown_statepack_photo_tag",
                                severity="warning",
                                message="statepack required_photo_tags contain unknown taxonomy tag(s)",
                                path=_posix(statepack_path, root=paths.root),
                                details={"unknown_photo_tags": unknown_statepack_tags},
                            )
                        )

        docs_dir = state_dir / "docs"
        if not docs_dir.exists() or not any(docs_dir.glob("*.md")):
            findings.append(
                Finding(
                    code="crossref_state_docs_missing",
                    severity="blocker",
                    message=f"{product_id}:{state} missing docs/*.md",
                    path=_posix(state_dir, root=paths.root),
                )
            )

        checklist_path = state_dir / "checklist.yaml"
        if checklist_path.exists():
            checklist_data = _load_yaml(checklist_path) or {}
            _validate_file(validators["checklist.schema.json"], checklist_data, path=checklist_path)
            checked["checklists"] = checked.get("checklists", 0) + 1

            req = state_requirements.get(state) if isinstance(state_requirements.get(state), dict) else {}
            declared_checklist = req.get("required_checklist") if isinstance(req, dict) else None
            expected_rel = f"states/{state}/checklist.yaml"
            if isinstance(declared_checklist, str) and declared_checklist != expected_rel:
                findings.append(
                    Finding(
                        code="crossref_required_checklist_path_mismatch",
                        severity="warning",
                        message="Manifest checklist path does not match state folder checklist",
                        path=_posix(manifest_path, root=paths.root),
                        details={"state": state, "declared": declared_checklist, "expected": expected_rel},
                    )
                )

        validations_dir = state_dir / "validations"
        if not validations_dir.exists() or not any(validations_dir.glob("*.yaml")):
            findings.append(
                Finding(
                    code="crossref_state_validations_missing",
                    severity="blocker",
                    message=f"{product_id}:{state} missing validations/*.yaml",
                    path=_posix(state_dir, root=paths.root),
                )
            )
        else:
            actual_rel_paths = {
                _posix(path.relative_to(product_dir), root=paths.root)
                for path in sorted(validations_dir.glob("*.yaml"))
            }
            req = state_requirements.get(state)
            if isinstance(req, dict):
                declared_paths = {
                    value for value in req.get("validations") or [] if isinstance(value, str)
                }
                missing_from_manifest = sorted(actual_rel_paths - declared_paths)
                missing_on_disk = sorted(declared_paths - actual_rel_paths)
                if missing_from_manifest:
                    findings.append(
                        Finding(
                            code="crossref_manifest_missing_validation_refs",
                            severity="warning",
                            message="Manifest is missing validation reference(s) present on disk",
                            path=_posix(manifest_path, root=paths.root),
                            details={"state": state, "paths": missing_from_manifest},
                        )
                    )
                if missing_on_disk:
                    findings.append(
                        Finding(
                            code="crossref_manifest_extra_validation_refs",
                            severity="blocker",
                            message="Manifest references validation file(s) missing on disk",
                            path=_posix(manifest_path, root=paths.root),
                            details={"state": state, "paths": missing_on_disk},
                        )
                    )

            seen_ids: set[str] = set()
            for validation_path in sorted(validations_dir.glob("*.yaml")):
                validation_data = _load_yaml(validation_path) or {}
                _validate_file(validators["validation.schema.json"], validation_data, path=validation_path)
                checked["validations"] = checked.get("validations", 0) + 1

                validation_id = validation_data.get("validation_id")
                if isinstance(validation_id, str):
                    if validation_id in seen_ids:
                        findings.append(
                            Finding(
                                code="crossref_validation_id_duplicate",
                                severity="blocker",
                                message="Duplicate validation_id in same state folder",
                                path=_posix(validation_path, root=paths.root),
                                details={"validation_id": validation_id},
                            )
                        )
                    else:
                        seen_ids.add(validation_id)

                if validation_data.get("when_state") != state:
                    findings.append(
                        Finding(
                            code="crossref_validation_folder_state_mismatch",
                            severity="blocker",
                            message="Validation when_state must match its folder state",
                            path=_posix(validation_path, root=paths.root),
                            details={"folder_state": state, "when_state": validation_data.get("when_state")},
                        )
                    )

    return findings


def _sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_ORDER.get(finding.severity, 99),
            finding.code,
            finding.path or "",
            finding.message,
            json.dumps(finding.details or {}, sort_keys=True),
        ),
    )


def _print_summary(findings: list[Finding], checked: dict[str, int]) -> None:
    blockers = sum(1 for finding in findings if finding.severity == "blocker")
    warnings = sum(1 for finding in findings if finding.severity == "warning")
    infos = sum(1 for finding in findings if finding.severity == "info")

    print("DPL Validation Summary")
    for key in sorted(checked):
        print(f"- checked.{key}: {checked[key]}")
    print(f"- findings.blocker: {blockers}")
    print(f"- findings.warning: {warnings}")
    print(f"- findings.info: {infos}")

    for finding in findings:
        location = f" ({finding.path})" if finding.path else ""
        print(f"[{finding.severity.upper()}] {finding.code}: {finding.message}{location}")


def _build_report(*, root: Path, findings: list[Finding], checked: dict[str, int], exit_code: int) -> dict[str, Any]:
    counts = {"blocker": 0, "warning": 0, "info": 0}
    for finding in findings:
        if finding.severity in counts:
            counts[finding.severity] += 1

    return {
        "version": 1,
        "root": root.as_posix(),
        "summary": {
            "checked": {key: checked[key] for key in sorted(checked)},
            "findings": counts,
            "exit_code": exit_code,
        },
        "findings": [asdict(finding) for finding in findings],
    }


def _write_json_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate SouthernIoT digital library")
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Repository root path (defaults to validator parent root)",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Optional path to write machine-readable validation report JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = args.root.resolve()
    paths = _paths_for_root(root)

    checked: dict[str, int] = {}
    findings: list[Finding] = []

    taxonomy: dict[str, list[str]] | None = None
    validators: dict[str, Draft202012Validator] | None = None

    try:
        taxonomy = _load_taxonomy(paths)
        checked["taxonomy_files"] = 4
    except Exception as exc:
        findings.append(
            Finding(
                code="taxonomy_load_failed",
                severity="blocker",
                message=str(exc),
                path=_posix(paths.root, root=paths.root),
            )
        )

    try:
        _, validators = _load_schema_store(paths)
        checked["schema_files"] = len(list(paths.schemas_dir.glob("*.schema.json")))
    except Exception as exc:
        findings.append(
            Finding(
                code="schema_load_failed",
                severity="blocker",
                message=str(exc),
                path=_posix(paths.schemas_dir, root=paths.root),
            )
        )

    if taxonomy and validators:
        findings.extend(
            _check_taxonomy_drift(
                paths=paths,
                taxonomy=taxonomy,
                validators_by_name=validators,
            )
        )

    if taxonomy:
        findings.extend(_check_integrations(paths, taxonomy["states"]))
        findings.extend(_check_nextcloud_artifacts(paths, taxonomy))

    if taxonomy and validators:
        try:
            manifests = _find_product_manifests(paths)
            checked["product_manifests_discovered"] = len(manifests)
            for manifest_path in manifests:
                try:
                    findings.extend(
                        _check_product(
                            paths=paths,
                            manifest_path=manifest_path,
                            taxonomy=taxonomy,
                            validators=validators,
                            checked=checked,
                        )
                    )
                except Exception as exc:
                    findings.append(
                        Finding(
                            code="product_validation_exception",
                            severity="blocker",
                            message=str(exc),
                            path=_posix(manifest_path, root=paths.root),
                        )
                    )
        except Exception as exc:
            findings.append(
                Finding(
                    code="manifest_discovery_failed",
                    severity="blocker",
                    message=str(exc),
                    path=_posix(paths.products_dir, root=paths.root),
                )
            )

    sorted_findings = _sort_findings(findings)
    exit_code = 2 if any(finding.severity == "blocker" for finding in sorted_findings) else 0
    _print_summary(sorted_findings, checked)

    if args.report_json:
        report = _build_report(root=root, findings=sorted_findings, checked=checked, exit_code=exit_code)
        _write_json_report(args.report_json, report)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
