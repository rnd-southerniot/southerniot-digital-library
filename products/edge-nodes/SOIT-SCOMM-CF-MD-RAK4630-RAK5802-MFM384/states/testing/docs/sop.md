# SOP: testing (RAK4630 + RAK5802 + MFM384)

## Goal
Confirm uplinks are seen and decoded correctly against expected meter readings.

## Steps
1. Confirm gateway is in `testing` (recommended) before starting node testing.
2. Trigger uplink and capture backend screenshot.
3. Confirm decoded payload fields match meter display within tolerance.
4. Capture 4–5 photos (uplink seen, decoded payload, meter screen, gateway RSSI/SNR).
5. Run validations in `validations/` and resolve blockers.

## Outputs
- Commissioning report (CRM comment + evidence)
