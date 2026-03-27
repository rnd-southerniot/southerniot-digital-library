# SouthernIoT Backend Service Contract (Phase 1 to Phase 2 Thin Slice)

## 1) CTO Architecture Alignment

This backend scope implements the phase-1 architecture from [SOU-22](/SOU/issues/SOU-22):

- Git-first contract source: schemas remain in `schemas/`, API contract in `integrations/crm/`.
- Deterministic integration behavior: all incoming events must satisfy `crm-event.schema.json`.
- Explicit failure behavior: all validation/integration failures use `error-envelope.schema.json`.
- Minimal surface area for phase 1: ingestion, search, and export only.

## 2) Service Boundaries

### Ingestion service (`/v1/ingestion/events`)
- Responsibility: receive CRM, ChirpStack, and lifecycle events and persist canonical envelope.
- Input contract: `schemas/crm-event.schema.json`.
- Output contract: `202 accepted` or deterministic error envelope.
- Notes: asynchronous processing with idempotent `event_id` uniqueness.

### Search service (`/v1/search/documents`)
- Responsibility: deterministic lookup over `.index/library_index.json` for CRM and assistant prompts.
- Input: query + optional state/role/product filters.
- Output: ranked paths and metadata only (no generation).

### Export service (`/v1/exports/field-pack`)
- Responsibility: queue role-aware field-pack export jobs for selected product variants.
- Input: project + package list.
- Output: asynchronous job acceptance + eventual artifact location.

## 3) DB Schema Proposals (Draft)

| Table | Purpose | Key fields |
| --- | --- | --- |
| `event_ingestion_log` | Canonical immutable ingest ledger | `event_id (pk)`, `event_type`, `project_id`, `workstream`, `state`, `payload_json`, `ingested_at`, `source_system`, `trace_id` |
| `device_lifecycle_state` | Materialized latest device status for CRM and support | `device_eui (pk)`, `project_id`, `product_id`, `state`, `lifecycle_status`, `last_event_id`, `updated_at` |
| `gateway_lifecycle_state` | Materialized latest gateway status | `gateway_id (pk)`, `project_id`, `product_id`, `state`, `lifecycle_status`, `last_event_id`, `updated_at` |
| `export_jobs` | Export queue + execution state | `export_job_id (pk)`, `project_id`, `request_json`, `status`, `artifact_uri`, `checksum_sha256`, `created_at`, `updated_at` |
| `contract_failures` | Deterministic error telemetry | `failure_id (pk)`, `request_id`, `error_code`, `category`, `service`, `source_event_id`, `details_json`, `created_at` |

## 4) Milestones

- M1 (March 27-28, 2026): Contract foundation
  - Extend CRM event schema
  - Add deterministic error envelope schema
  - Add OpenAPI draft + JSON examples
- M2 (March 29-31, 2026): Ingestion adapter implementation
  - Event idempotency and persistence model
  - ChirpStack uplink + lifecycle mapping adapters
- M3 (April 1-3, 2026): Search/export boundary implementation
  - Search API from generated index
  - Export job API with queue contract
- M4 (April 4-5, 2026): Production readiness
  - Contract tests in CI
  - Backfill runbooks and on-call failure triage doc

## 5) Execution Log

- 2026-03-27: Added phase-1 API contract draft and schema extensions for CRM lifecycle + ChirpStack events.
- 2026-03-27: Added deterministic error envelope schema for validator/tooling and integration services.
- 2026-03-27: Added contract examples and validator command for compatibility checks.

## 6) Risk Register

| Risk | Impact | Mitigation | Owner |
| --- | --- | --- | --- |
| ChirpStack payload drift across versions | Event ingestion breakage | Include `source.version`; keep mapper tests by ChirpStack version | Backend |
| Duplicate event replay from CRM/webhooks | State inconsistency | enforce `event_id` uniqueness + idempotent writes | Backend |
| Weak error code governance | Hard-to-debug incidents | strict `error.code` enum policy in service layer and tests | Backend + CTO |
| Export queue latency spikes | Field operations delay | async queue with worker autoscaling and retry policy | Backend + DevOps |

## 7) Validation Command

- Contract validation command:
  - `python tools/validate_crm_contracts.py`
- This checks:
  - CRM event examples against `schemas/crm-event.schema.json`
  - Error examples against `schemas/error-envelope.schema.json`

## 8) Phase-2 API Surface (Clean Contract)

| Endpoint | Method | Request contract | Success contract | Failure contract |
| --- | --- | --- | --- | --- |
| `/v1/ingestion/events` | `POST` | `schemas/crm-event.schema.json` | `202 accepted` with `event_id`, `received_at` | `schemas/error-envelope.schema.json` |
| `/v1/search/documents` | `GET` | query params: `q`, `product_id`, `state`, `role` | `200` deterministic metadata list | `schemas/error-envelope.schema.json` |
| `/v1/exports/field-pack` | `POST` | OpenAPI `FieldPackExportRequest` | `202` with `export_job_id`, `status=queued` | `schemas/error-envelope.schema.json` |
| `/v1/exports/field-pack/{export_job_id}` | `GET` | path param `export_job_id` | `200` status + `artifact_uri` + `checksum_sha256` when complete | `schemas/error-envelope.schema.json` |

Implementation note: the status endpoint is required for CRM polling and incident triage even when workers are asynchronous.

## 9) DB Schema Proposal (Implementation-Oriented)

```sql
create table event_ingestion_log (
  event_id text primary key,
  event_type text not null,
  project_id text not null,
  workstream text,
  state text,
  payload_json jsonb not null,
  source_system text not null,
  trace_id text,
  ingested_at timestamptz not null default now()
);

create index event_ingestion_log_project_idx
  on event_ingestion_log (project_id, ingested_at desc);

create table device_lifecycle_state (
  device_eui text primary key,
  project_id text not null,
  product_id text not null,
  state text not null,
  lifecycle_status text not null,
  last_event_id text not null references event_ingestion_log(event_id),
  updated_at timestamptz not null default now()
);

create table gateway_lifecycle_state (
  gateway_id text primary key,
  project_id text not null,
  product_id text not null,
  state text not null,
  lifecycle_status text not null,
  last_event_id text not null references event_ingestion_log(event_id),
  updated_at timestamptz not null default now()
);

create table export_jobs (
  export_job_id text primary key,
  project_id text not null,
  request_json jsonb not null,
  status text not null,
  artifact_uri text,
  checksum_sha256 text,
  error_json jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index export_jobs_project_status_idx
  on export_jobs (project_id, status, updated_at desc);

create table contract_failures (
  failure_id bigserial primary key,
  request_id text,
  error_code text not null,
  category text not null,
  service text not null,
  source_event_id text,
  details_json jsonb not null,
  created_at timestamptz not null default now()
);
```

## 10) Phase-2 Milestone Linkage

- Thin-slice pilot plan source: `docs/backend-thin-slice-pilot-plan.md`.
- Owner track for backend implementation: `backend-core`.
- Target cutover gate: April 17, 2026 board readiness review.

## 11) Additional Risks for Production Rollout

| Risk | Impact | Mitigation | Owner |
| --- | --- | --- | --- |
| Projection reader load spike during CRM polling | Elevated DB load, stale reads | add bounded polling interval + indexed read paths | Backend + CRM |
| Queue drain stalls after worker deploy | Export SLA miss | add job heartbeat + stale-job recovery sweep | Backend + DevOps |
