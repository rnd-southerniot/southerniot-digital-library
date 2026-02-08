# SOP: lab_test (RAK4630 + RAK5802 + MFM384)

## Goal
Confirm Modbus polling and payload decoding before field deployment.

## Steps
1. Bench-connect RS-485 to an MFM384 (or test setup) and verify A/B wiring.
2. Poll registers per `modbus/register-map.csv`.
3. Validate decoded payload per `modbus/codec.yaml` and `modbus/test-vectors.json`.
4. Attach logs/results to CRM.

## Outputs
- Lab test log + test vector results
