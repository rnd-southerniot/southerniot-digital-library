# SOP: firmware_generate (RAK4630 + RAK5802 + MFM384)

## Goal
Generate the correct firmware for the variant and meter profile.

## Policy
- Requires approval: `RND_LEAD` only.
- Artifacts must be referenced via Nextcloud (`artifact_id`, `sha256`, `nextcloud_path`).

## Steps
1. Confirm region (`AS923-1`) and Modbus defaults (`9600-N-8-1`).
2. Confirm codec version and register map version (see `modbus/`).
3. Build firmware and upload artifact to Nextcloud.
4. Record immutable reference in CRM and attach device profile reference.

## Outputs
- Firmware bundle reference + device profile reference in CRM
