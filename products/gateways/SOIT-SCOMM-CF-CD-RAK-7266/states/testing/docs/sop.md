# SOP: testing (RAK7266)

## Goal
Commission the gateway and confirm it is online and forwarding traffic.

## Steps
1. Confirm gateway is online in the LoRaWAN backend (status page/screenshot).
2. Confirm RSSI/SNR and RF noise floor look acceptable for the site.
3. Confirm backhaul stability (packet loss / LTE signal quality).
4. Capture 4–5 evidence photos (LEDs, backhaul proof, backend status, RF environment).
5. Run validations in `validations/` and resolve blockers.

## Outputs
- Commissioning report (CRM comment + evidence)
