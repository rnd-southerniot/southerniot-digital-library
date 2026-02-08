# SOP: initialized (RAK4630 + RAK5802 + MFM384)

## Goal
Create the edge-node workstream in CRM and lock variant + meter context.

## Steps
1. Create/confirm CRM workstream: `edge_node`.
2. Select `variant_id` and confirm defaults: `AS923-1` and Modbus `9600-N-8-1`.
3. Capture meter context: model, CT ratio, expected range, location.
4. Confirm gateway dependency: node installation is blocked until gateway is `ready_for_installation`.

## Outputs
- CRM comment: initialization summary + selected variant
