from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "validator"


def _workspace_ignore(_: str, names: list[str]) -> set[str]:
    blocked = {
        ".git",
        ".venv",
        ".pytest_cache",
        "out",
        "__pycache__",
        ".agents",
        ".index",
    }
    return {name for name in names if name in blocked}


def _prepare_workspace(tmp_path: Path, fixture_dir: Path) -> Path:
    workspace = tmp_path / "workspace"
    shutil.copytree(REPO_ROOT, workspace, ignore=_workspace_ignore)

    for source in sorted(fixture_dir.rglob("*")):
        if source.is_dir() or source.name in {"expected.json", "remove_paths.txt"}:
            continue
        relative = source.relative_to(fixture_dir)
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    remove_paths = fixture_dir / "remove_paths.txt"
    if remove_paths.exists():
        for raw_path in remove_paths.read_text(encoding="utf-8").splitlines():
            relative_path = raw_path.strip()
            if not relative_path or relative_path.startswith("#"):
                continue
            target = workspace / relative_path
            if target.is_file():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)

    return workspace


def _run_validator(workspace: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    report_path = workspace / "out" / "validation-report.json"
    cmd = [
        sys.executable,
        str(workspace / "tools" / "validate_library.py"),
        "--root",
        str(workspace),
        "--report-json",
        str(report_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert report_path.exists(), f"Expected report file at {report_path}"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return proc, report


@pytest.mark.parametrize(
    "fixture_name",
    [
        "pass",
        "fail_taxonomy_drift",
        "fail_missing_core_schema",
        "fail_placeholder_hash",
        "fail_cross_file_reference",
    ],
)
def test_validator_golden_fixtures(tmp_path: Path, fixture_name: str) -> None:
    fixture_dir = FIXTURES_DIR / fixture_name
    expected_path = fixture_dir / "expected.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    workspace = _prepare_workspace(tmp_path, fixture_dir)
    proc, report = _run_validator(workspace)

    assert proc.returncode == expected["exit_code"], proc.stdout + "\n" + proc.stderr
    assert report["summary"]["exit_code"] == expected["exit_code"]

    finding_codes = {finding["code"] for finding in report["findings"]}
    for code in expected.get("must_include_codes", []):
        assert code in finding_codes, f"Missing expected finding code: {code}"
