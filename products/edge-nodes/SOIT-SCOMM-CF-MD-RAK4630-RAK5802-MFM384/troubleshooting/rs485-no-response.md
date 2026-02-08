# Troubleshooting: RS-485 No Response (MFM384)

## Confirm settings
- 9600-N-8-1 (default)
- Slave ID matches meter configuration

## Wiring checks
- A/B not swapped
- Common GND connected
- Termination only at bus ends
- Use twisted pair; shield in noisy environments

## Typical issues
- Duplicate slave IDs on same bus
- Floating ground causing intermittent failures
- Wrong register offset/map

