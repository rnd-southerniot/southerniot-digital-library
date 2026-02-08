# SouthernIoT Digital Product Library (DPL)

This repository is the **source-of-truth** for SouthernIoT product implementation.
It is designed to drive:
- **CRM state workflow** (gated transitions)
- **AI agent orchestration** (retrieve + validate, never guess)
- **Field PWA checklists** (photos-only evidence collection)
- **R&D + Implementation execution** (repeatable SOPs)

## Defaults (Locked)
- LoRaWAN Region: **AS923-1**
- RAK7266 Gateway Modes: **Basic Station (default)** + **UDP Packet Forwarder (supported)**
- Selec MFM384 Modbus default: **9600-N-8-1**

## Key Concepts
- **Product manifest**: `/products/**/manifest.yaml`
- **Statepack**: `/products/**/states/<state>/statepack.yaml`
- **Checklist** (PWA-driven): `/products/**/states/<state>/checklist.yaml`
- **Validation rules**: `/products/**/states/<state>/validation_*.yaml`
- **Nextcloud artifacts**: `/integrations/nextcloud/artifact-index.yaml`

## CI Recommendation
Run `/tools/validate_library.py` in CI to prevent broken library updates.
