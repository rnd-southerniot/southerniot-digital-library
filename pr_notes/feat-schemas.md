# PR: Strict JSON Schemas (drift prevention)

## Summary
- Upgrades all JSON Schemas in `schemas/` to draft 2020-12 with `$id` for stable refs.
- Tightens contracts using `additionalProperties: false`, enums for authoritative states/roles/severities, and conditional requirements by workstream.
- Locks defaults that are non-negotiable (region `AS923-1`; Modbus `9600-N-8-1`).

## Review Notes
- Product pack YAMLs may require small edits to comply with stricter schemas (handled in product-pack PRs).

## Risks / Rollback
- Medium risk: stricter validation may block non-conforming content until updated.
- Rollback: revert schema changes if validation becomes too restrictive.
