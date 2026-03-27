# SouthernIoT DPL Agent Guide

## Purpose
Keep delivery knowledge reusable and audit-ready by treating repository content as production artifacts.

## Ownership Model
- `docs-core` owns cross-cutting documentation (`README.md`, `CONTRIBUTING.md`, `DECISIONS.md`, `docs/`).
- Product maintainers own their product packs under `products/**`.
- Schema/tool maintainers own `schemas/**` and `tools/**`.
- Every issue has one direct owner; cross-team updates require linked release notes and validator proof.

## Required Updates Per Change
- Product/state behavior change:
  - update `manifest.yaml` and/or state files
  - update release notes in `products/<type>/<product_id>/release-notes/`
  - include artifact checksum linkage from `integrations/nextcloud/artifact-index.yaml`
  - run validator
- Architecture/process change:
  - update `docs/architecture.md` and/or `docs/glossary.md`
  - add a decision entry in `DECISIONS.md`
- Taxonomy change:
  - update root taxonomy files (`states.yaml`, `roles.yaml`, `severities.yaml`, `tags.yaml`)
  - confirm CRM mappings stay aligned

## Definition Of Done (Documentation Work)
- Changes are concise, production-oriented, and reference authoritative files.
- `./.venv/bin/python tools/validate_library.py` returns zero blockers.
- A maintainer can trace what changed, why, and who owns follow-up.

## Phase-2 Cadence
- `docs-core` executes a weekly launch-gate sweep via `docs/runbooks/docs-launch-gate.md`.
- Product maintainers keep release-note entries current for each affected pack and include artifact ID plus checksum.
- Onboarding readiness is tracked in `docs/runbooks/onboarding-dry-run.md` and must stay under 30 minutes.
