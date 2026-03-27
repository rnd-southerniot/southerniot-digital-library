#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"
EXAMPLES_DIR = ROOT / "integrations" / "crm" / "examples"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_validators() -> dict[str, Draft202012Validator]:
    schemas: list[tuple[Path, dict]] = []
    for schema_path in sorted(SCHEMAS_DIR.glob("*.schema.json")):
        schemas.append((schema_path, _load_json(schema_path)))

    store: dict[str, dict] = {}
    for schema_path, schema in schemas:
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ValueError(f"Schema missing $id: {schema_path}")
        store[schema_id] = schema

    registry = Registry().with_resources(
        [(schema_id, Resource.from_contents(schema)) for schema_id, schema in store.items()]
    )

    validators: dict[str, Draft202012Validator] = {}
    for schema_path, schema in schemas:
        validators[schema_path.name] = Draft202012Validator(schema, registry=registry)
    return validators


def _validate_examples(validators: dict[str, Draft202012Validator]) -> list[str]:
    checks = {
        "crm-event-state-update.success.json": "crm-event.schema.json",
        "crm-event-validation-result.failure.json": "crm-event.schema.json",
        "crm-event-device-lifecycle.success.json": "crm-event.schema.json",
        "crm-event-gateway-lifecycle.success.json": "crm-event.schema.json",
        "crm-event-chirpstack-uplink.success.json": "crm-event.schema.json",
        "error-envelope-validation.failure.json": "error-envelope.schema.json",
        "error-envelope-integration.failure.json": "error-envelope.schema.json",
    }

    failures: list[str] = []
    for example_name, schema_name in checks.items():
        example_path = EXAMPLES_DIR / example_name
        if not example_path.exists():
            failures.append(f"missing example: {example_path.as_posix()}")
            continue

        instance = _load_json(example_path)
        validator = validators.get(schema_name)
        if validator is None:
            failures.append(f"missing validator for schema: {schema_name}")
            continue

        errors = sorted(validator.iter_errors(instance), key=lambda e: e.json_path)
        if errors:
            failures.append(f"{example_name}: {errors[0].message}")

    return failures


def main() -> int:
    try:
        validators = _load_validators()
        failures = _validate_examples(validators)
    except Exception as exc:
        print(f"[CRM-CONTRACT] FAIL: {exc}")
        return 2

    if failures:
        print("[CRM-CONTRACT] FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 2

    print("[CRM-CONTRACT] PASS: all CRM event and error-envelope examples are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
