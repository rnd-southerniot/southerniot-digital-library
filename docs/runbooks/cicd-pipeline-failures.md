# CI/CD Pipeline Failure Runbook

Use this runbook for failures in `Validate DPL Library` or `Release Field Pack`.

## 1. Triage

1. Open the failed workflow run and identify the first failing step.
2. Capture run metadata in your ticket/update:
- workflow name
- run URL
- failing step
- commit SHA/tag
3. Reproduce locally from a clean environment:

```bash
make clean
make ci
```

## 2. Failure Classes

### Validation failure (`tools/validate_library.py`)

- Usually taxonomy/schema/statepack drift.
- Fix invalid file(s), re-run `make ci`, then push.

### Index build failure (`tools/build_search_index.py`)

- Usually malformed YAML/JSON/CSV or filesystem path issues.
- Fix source document or parser expectations, then re-run `make ci`.

### Export smoke failure (`make export-smoke`)

- Usually invalid product/variant IDs, missing state files, or zip/checksum generation errors.
- Reproduce locally:

```bash
make clean
make export-smoke
```

- Confirm both outputs exist before re-pushing:
  - `out/release-smoke/*.zip`
  - `out/release-smoke/SHA256SUMS.txt`

### Field-pack export failure (`tools/export_field_pack.py`)

- Usually invalid product/variant IDs or missing expected state files.
- Validate manifest + variant IDs and re-run:

```bash
.venv/bin/python tools/export_field_pack.py \
  --project-id CI-REPRO \
  --product-id SOIT-SCOMM-CF-CD-RAK-7266 \
  --variant AS9231_BASIC_STATION_POE \
  --out out/repro
```

### Release publication failure

- If artifact build passed but release step failed, retry the workflow first.
- If tag/release metadata is wrong, follow rollback below and re-tag.

## 3. Rollback Procedures

### A. Bad commit merged to `main`

1. Revert with a new commit:

```bash
git revert <bad_sha>
git push origin main
```

2. Confirm `Validate DPL Library` passes on the revert commit.

### B. Bad field-pack release tag

1. Delete release and tag in GitHub UI (or via CLI).
2. Create a fix commit and wait for green CI on `main`.
3. Re-cut a new tag (for example `field-pack-v1.0.1`) and push:

```bash
git tag field-pack-v1.0.1
git push origin field-pack-v1.0.1
```

4. Verify new `SHA256SUMS.txt` matches uploaded zip assets.

## 4. Escalation

- If blocked for more than 30 minutes, escalate in the owning issue with:
- failing workflow link
- current blocker
- required support (code owner, infra admin, repo admin)

## 5. Launch-Gate Reliability Evidence

When proving launch readiness for required checks, capture this evidence in the owning issue comment:

1. Last 10 default-branch runs where all required checks are green.
2. At least 2 green PR runs from fresh branches.
3. Artifact names for each run:
   - `validation-report-<run_id>-<attempt>`
   - `release-smoke-<run_id>-<attempt>`

Example GitHub CLI commands:

```bash
# default branch
gh run list --workflow "Validate DPL Library" --branch main --limit 20

# PR runs
gh run list --workflow "Validate DPL Library" --event pull_request --limit 20
```
