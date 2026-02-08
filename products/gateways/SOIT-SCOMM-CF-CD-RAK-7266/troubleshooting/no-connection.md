# RAK7266 Troubleshooting: Not Connected in ChirpStack

## Fast checks
- Confirm power and boot
- Verify backhaul (Ethernet or LTE APN)
- Confirm gateway ID matches ChirpStack registration
- Confirm selected mode:
  - Basic Station (default)
  - UDP packet forwarder (supported)

## Common causes
- Firewall blocking required ports
- Wrong AS923 sub-band / frequency plan mismatch
- Time sync issues (NTP) causing join/uplink problems

