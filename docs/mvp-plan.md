# DPL MVP Plan

## Goal
Deliver a phase-1 backend that proves the updated DPL architecture end to end without widening scope beyond the core contracts already in this repository.

## MVP Boundary
- In scope:
  - event ingestion for CRM, ChirpStack, and lifecycle payloads
  - deterministic search over generated DPL index data
  - asynchronous field-pack export from repository content
  - state projection reads for CRM/support visibility
- Out of scope:
  - generated AI guidance in the backend response path
  - dynamic authoring or mutation of product-pack content outside Git
  - analytics, recommendation scoring, and broad multi-tenant administration

## Architecture Summary
- Git remains the source of truth for taxonomy, schemas, product packs, and integration mappings.
- CI validates repository content before runtime artifacts are published.
- Runtime services consume three contract surfaces:
  - `POST /v1/ingestion/events`
  - `GET /v1/search/documents`
  - `POST /v1/exports/field-pack`
- Runtime persistence is split between:
  - immutable event ledger
  - materialized state projections
  - export job queue/state

## Delivery Phases
### Phase 0: Contract Freeze
- Confirm `schemas/crm-event.schema.json` and `schemas/error-envelope.schema.json` as the only inbound/outbound service contracts for MVP failures and event payloads.
- Keep `integrations/crm/state-mapping.yaml`, `integrations/crm/parallel-workstreams.yaml`, and `integrations/crm/notification-routing.yaml` aligned with `states.yaml`.
- Make `tools/validate_library.py` and `tools/validate_crm_contracts.py` required CI gates.
- Exit criteria:
  - contract examples pass validation
  - validator report is written on every CI run

### Phase 1: Ingestion Service
- Build `POST /v1/ingestion/events` as the first production endpoint.
- Required behavior:
  - validate payloads against `crm-event.schema.json`
  - enforce `event_id` idempotency
  - persist canonical event envelope to the immutable ingestion log
  - emit deterministic errors using `error-envelope.schema.json`
- Data stores:
  - `event_ingestion_log`
  - `contract_failures`
- Exit criteria:
  - replayed events are idempotent
  - invalid events never bypass contract validation

### Phase 2: State Projections
- Create projection updaters for latest gateway/device state.
- Keep projection logic derived from the immutable ledger, not from ad-hoc UI mutations.
- Data stores:
  - `device_lifecycle_state`
  - `gateway_lifecycle_state`
- Exit criteria:
  - CRM can read current per-device/per-gateway status
  - workstream gates can be evaluated from projected state

### Phase 3: Search API
- Reuse `tools/build_search_index.py` to build `.index/library_index.json`.
- Build `GET /v1/search/documents` as a thin deterministic query layer over the generated index.
- Search response rules:
  - return paths and metadata only
  - support `q`, `product_id`, `state`, and `role` filters
  - keep ranking simple and explainable
- Exit criteria:
  - CRM or assistant clients can retrieve exact file paths for a product/state query
  - no generated procedural text is returned by the API

### Phase 4: Export API
- Reuse `tools/export_field_pack.py` behind `POST /v1/exports/field-pack`.
- Treat export as an asynchronous job with artifact metadata on completion.
- Data store:
  - `export_jobs`
- Exit criteria:
  - users can request a field-pack export for one or more variants
  - completed jobs expose artifact URI and checksum

### Phase 5: Pilot and Hardening
- Run one gateway and one edge-node pilot flow across the full state path needed for field deployment readiness.
- Add smoke tests for:
  - event ingestion
  - index build plus search query
  - export request plus artifact completion
- Add runbooks for contract failures and stuck export jobs.
- Exit criteria:
  - one real project path works end to end
  - operations can triage failures without reading source code

## Sequencing
1. Freeze contracts and examples.
2. Implement ingestion and immutable persistence.
3. Add projection workers and read models.
4. Expose search over generated index artifacts.
5. Expose export job API over field-pack tooling.
6. Run pilot, close blockers, and release MVP.

## Acceptance Criteria
- Repository validation and CRM contract checks are required before deployment.
- Valid CRM/lifecycle events are accepted and persisted exactly once.
- Invalid requests return deterministic error envelopes.
- Search returns document metadata from the DPL, not synthesized instructions.
- Field-pack export completes from repository content with artifact checksum output.
- CRM state/workstream behavior remains aligned with `states.yaml` and CRM mapping YAMLs.

## Ownership
- `docs-core` owns this plan and architecture alignment.
- Schema/tool maintainers own contract validators and generated artifact tooling.
- Product maintainers own product-pack completeness required for search and export usefulness.
- Backend maintainers own runtime implementation of ingestion, projections, search, and export services.
