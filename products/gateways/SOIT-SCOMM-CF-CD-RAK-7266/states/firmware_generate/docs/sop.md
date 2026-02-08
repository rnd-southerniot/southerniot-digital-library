# SOP: firmware_generate (RAK7266)

## Goal
Generate or select the correct gateway configuration bundle for the chosen variant.

## Policy
- Requires approval: `RND_LEAD` only.
- Artifacts must be referenced via Nextcloud (`artifact_id`, `sha256`, `nextcloud_path`).

## Steps
1. Confirm selected `variant_id` and deployment mode (`basic_station` default).
2. Request/configure backend parameters (server URL, TLS, auth) as applicable.
3. Produce a configuration bundle artifact and upload to Nextcloud.
4. Record immutable reference (artifact id + sha256 + path) in CRM.
5. Run validations in `validations/` before marking complete.

## Outputs
- Firmware/config bundle reference in CRM
