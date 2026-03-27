# DPL Design Decisions (SouthernIoT)

## 1) Git-first, schema-validated library
- The Digital Product Library (DPL) is the source-of-truth; all procedures and requirements must be stored as files in this repo.
- CI validates the repository against JSON Schemas to prevent drift and stop invalid commits.

## 2) Deterministic “library contract” for AI guidance
- AI guidance must be **retrieval-first**: it can only recommend steps that exist in the library.
- AI must validate the chosen product + state + variant against schemas and validator rules before outputting guidance.
- If required inputs/evidence/approvals are missing, guidance must stop and request the missing items.

## 3) Authoritative CRM state machine and workstreams
- The authoritative state progression is stored in `states.yaml` and mirrored into integration mapping YAMLs.
- Parallel workstreams (`gateway`, `edge_node`) are first-class and include dependency gates:
  - `edge_node:on_site_installation` is **BLOCKED** unless `gateway >= ready_for_installation`
  - `edge_node:testing` is **WARNING** unless `gateway >= testing`

## 4) Nextcloud artifacts are referenced, not downloaded
- The library stores immutable references to Nextcloud artifacts via:
  - `artifact_id` (immutable ID)
  - `sha256` (content hash)
  - `nextcloud_path` (path reference)
- Tools may include artifact references in exports but must not download content by default.

## 5) Role-aware packaging
- Content and outputs are tagged by role (`CTO`, `RND_*`, `Field`, `Support`, etc.).
- Field packs can be exported with role filters to reduce noise in offline operation.

## 6) Locked defaults
- LoRaWAN region default: `AS923-1`
- RAK7266 gateway mode default: `basic_station` (UDP packet forwarder supported as a variant)
- MFM384 Modbus default: `9600-N-8-1`

## 7) Evidence and approvals are policy, not prose
- Evidence photo counts/tags for `site_survey`, `on_site_installation`, `testing` are enforced by validator rules.
- Firmware approvals are enforced: `firmware_generate` requires `approvals: [RND_LEAD]`.

## 8) Restart rationale and ownership model
- The repository was intentionally restarted as a clean baseline to remove drift between ad-hoc docs, CRM behavior, and executable validation rules.
- Ownership is explicit by artifact class:
  - product maintainers own product packs and release notes
  - schema/tool maintainers own validation contracts and automation
  - docs-core owns cross-cutting architecture/process documentation
- Any architecture or process change must include both:
  - decision-log update in this file
  - release-note entry in affected product packs when operational behavior changes

## 9) Phase-1 MVP is contract-first ingestion, retrieval, and export
- The updated MVP architecture is intentionally limited to three runtime surfaces:
  - event ingestion
  - deterministic document search
  - asynchronous field-pack export
- Runtime services consume contracts authored in this repository; they do not redefine taxonomy, state transitions, or product-pack requirements.
- AI stays retrieval-only for the MVP and must not generate write-path decisions or mutate delivery state outside validated service contracts.
- The backend audit model is split into:
  - immutable event ledger for traceability
  - materialized projections for CRM/support read paths
  - export job records for offline package delivery
- MVP release readiness requires:
  - validator and contract checks in CI
  - one end-to-end pilot across existing gateway and edge-node product packs
  - runbooks for contract failures and export-job triage

## 10) Phase-2 thin-slice pilot is the required production bridge
- Phase-2 backend rollout must follow a thin-slice pilot before broad launch:
  - one gateway and one edge-node workstream in shadow mode first
  - explicit cutover gate with board go/no-go evidence
  - documented rollback triggers for ingestion error rate, projection lag, and export backlog
- Pilot plan of record is `docs/backend-thin-slice-pilot-plan.md`.
- Service contract and DB implementation details remain in `integrations/crm/backend-service-contract.md`.

## 10) Phase-2 docs launch gate and release-note artifact binding
- Documentation release readiness is now treated as an explicit launch gate, not an implicit PR convention.
- A dedicated runbook (`docs/runbooks/docs-launch-gate.md`) defines:
  - ownership rotation (`docs-core` weekly coordinator; product maintainers per-pack release-note owner)
  - cadence (per-change plus weekly sweep)
  - required checks (cross-doc consistency, validator proof, onboarding timing, and decision logging)
- Release-note entries for active products must include artifact checksum linkage (`artifact_id` + `sha256`) from `integrations/nextcloud/artifact-index.yaml`.
- Onboarding readiness is measured with a timed dry-run log (`docs/runbooks/onboarding-dry-run.md`) and kept below 30 minutes through recorded corrective actions.

## 10) Phase-2 launch gate splits CI into required independent checks with retained evidence
- Launch readiness is enforced through four independent required checks in `Validate DPL Library`:
  - `validator`
  - `fixtures`
  - `index-build`
  - `export-smoke`
- Validation and export-smoke jobs must publish audit artifacts for each run:
  - `out/validation-report.json`
  - `out/release-smoke/*.zip` and `out/release-smoke/SHA256SUMS.txt`
- Branch protection must require all four checks on `main` and block merges on any failure.
- Evidence collection for launch approval is operationalized in runbooks and tracked in owning issues.
