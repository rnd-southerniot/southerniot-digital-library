# Onboarding Dry-Run Log

## Goal
Validate that a new maintainer can complete repository onboarding in under 30 minutes.

## Latest Dry Run
- Date: 2026-03-27
- Scenario: New maintainer starting from clean checkout with no prior local environment.
- Elapsed time: 27 minutes
- Result: Pass (under 30-minute target)

## Step Timing
1. Environment setup (`python3 -m venv`, install requirements): 8 min
2. Baseline checks (`validate_library.py`, `build_search_index.py`): 7 min
3. First documentation update and release-note linkage: 9 min
4. Final validation and git status check: 3 min

## Corrective Actions Applied
- Added `docs/runbooks/docs-launch-gate.md` and linked it from top-level docs.
- Updated contribution guidance to require artifact/checksum references in release notes.
- Added phase-2 launch workflow section in `README.md` to reduce navigation ambiguity.

## Follow-Up Owners
- `docs-core`: re-run dry run weekly and update this log if timing regresses.
- Product maintainers: report onboarding friction in release-note follow-up bullets when process gaps are discovered.
