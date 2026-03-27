# Branch Protection Baseline

This baseline keeps mainline releases reliable while keeping the process simple.

## Branch Rules (`main`)

Enable branch protection on `main` with:

- Require pull request before merging.
- Require at least 1 approval.
- Dismiss stale approvals on new commits.
- Require conversation resolution before merging.
- Require status checks to pass before merging.
- Restrict force pushes and branch deletions.

## Required Status Checks

Add these required checks:

- `Validate DPL Library / validator`
- `Validate DPL Library / fixtures`
- `Validate DPL Library / index-build`
- `Validate DPL Library / export-smoke`

When release tagging is used, only cut tags from commits that already passed the above check.

## Evidence Retention Baseline

- Keep CI artifacts for at least 30 days.
- Required evidence artifacts per run:
  - `validation-report-<run_id>-<attempt>` from `out/validation-report.json`
  - `release-smoke-<run_id>-<attempt>` containing `out/release-smoke/*.zip` and `out/release-smoke/SHA256SUMS.txt`

## Secrets Separation Policy

- Use repository/environment secrets only (`Settings -> Secrets and variables`).
- Never store credentials in repo files, workflow YAML, or release notes.
- Prefer `GITHUB_TOKEN` for GitHub release publication; do not introduce personal access tokens unless explicitly needed.
- Keep deployment credentials (for Docker/Proxmox/VM targets) in environment-scoped secrets with least privilege.

## Rollback Guardrails

- If a problematic commit reaches `main`, revert with a new commit; do not rewrite history.
- If a bad field-pack tag was published, delete the GitHub Release + tag, then publish a new fixed tag.
