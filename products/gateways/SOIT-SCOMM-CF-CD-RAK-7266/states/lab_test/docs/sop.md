# SOP: lab_test (RAK7266)

## Goal
Verify the gateway boots and services are healthy before shipping to site.

## Steps
1. Power on using the correct power method for the variant.
2. Confirm LEDs and device boots cleanly.
3. Confirm backhaul link (ethernet DHCP or LTE attach).
4. Confirm packet forwarding path is operational:
   - Basic Station (default) preferred
   - UDP PF only if variant is `udp_packet_forwarder`
5. Attach lab test log + screenshots to CRM.

## Outputs
- Lab test log
