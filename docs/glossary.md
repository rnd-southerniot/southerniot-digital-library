# CRM + Statepack Glossary

| Term | Definition | Source |
| --- | --- | --- |
| Product Manifest | Product-level contract for defaults, variants, alerting, and per-state requirements. | `schemas/manifest.schema.json` |
| Statepack | Execution contract for one state: objective, roles, steps, inputs, evidence, outputs. | `schemas/statepack.schema.json` |
| Checklist | Field/PWA data-capture schema used at execution time. | `schemas/checklist.schema.json` |
| Validation Rule | Machine-checkable rule with severity, state, and blocking/warning behavior. | `schemas/validation.schema.json` |
| Workstream | Parallel delivery lane (`gateway` or `edge_node`) governed by dependency gates. | `integrations/crm/parallel-workstreams.yaml` |
| State Mapping | Explicit mapping between CRM state labels and library state IDs. | `integrations/crm/state-mapping.yaml` |
| Required Evidence | Minimum photo and tag requirements tied to state completion. | product `manifest.yaml` + `tags.yaml` |
| Artifact Index | Registry of external Nextcloud artifacts by immutable ID, hash, and path. | `integrations/nextcloud/artifact-index.yaml` |
| Variant | Deployable configuration flavor (for example gateway mode/backhaul option). | `products/**/variants/*.yaml` |
| Definition Of Done (State) | Combination of docs, checklist completion, validation results, approvals, and outputs for a state. | `manifest.yaml` `state_requirements` |
| Canonical Event Envelope | Immutable inbound event record persisted after schema validation and idempotency checks. | `schemas/crm-event.schema.json` |
| State Projection | Materialized latest-state read model derived from the ingestion ledger for CRM/support workflows. | `integrations/crm/backend-service-contract.md` |
| Search Index | Generated `.index/library_index.json` artifact used for deterministic retrieval over product-pack content. | `tools/build_search_index.py` |
| Export Job | Asynchronous request and execution record for field-pack artifact generation. | `tools/export_field_pack.py` |
| Thin-Slice Pilot | Controlled rollout path that exercises ingestion, projection, search, and export across one gateway and one edge-node flow before broad launch. | `docs/backend-thin-slice-pilot-plan.md` |
| Cutover Gate | Board-approved go/no-go checkpoint that requires shadow-mode parity evidence and rollback readiness. | `docs/backend-thin-slice-pilot-plan.md` |
