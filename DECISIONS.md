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
