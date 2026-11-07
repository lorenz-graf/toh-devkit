# Dev cover: the two ID modes, DEV (6.2 kΩ) and CHIP (10 kΩ + emulated memory chip)

The dev cover must support **both** ways a cover can identify itself to the phone. The hardware is the same for both; only the ID mode jumper JP2 on the breakout board ([pcb/breakout/](pcb/breakout/)) differs (DEV = 6.2 kΩ, CHIP = 10 kΩ). Firmware and phone package support both at the same time, so switching is a resistor swap.

**Not tested yet:** this describes how I expect both modes to work, based on Jolla's spec and the symbiosis docs/code; nothing here has been tried on a phone. Overview of the whole cover: [README.md](README.md). Spec (ADC ranges, payload fields, timing): https://docs.sailfishos.org/Develop/Hardware/JP2601-TOH/

## Summary

| | **DEV mode: dev ID** | **CHIP mode: emulated memory chip** |
|---|---|---|
| ID → GND (breakout JP2) | **DEV: R1 6.2 kΩ** | **CHIP: R2 10 kΩ** |
| ID ADC on the phone | 600–799 | 800–999 |
| What the phone does | no memory chip read; "predefined data", VID/PID `0000/0000`, 5 V stays on | waits 100 ms after 5 V on, then reads the memory chip at I²C **0x50** (8-bit addresses, AT24C16 style) |
| Who must answer at 0x50 | nobody | **the RP2040**, within 100 ms of power-on, with a valid `JTOH` image |
| Cover info on D-Bus | VendorId/ProductId 0, no names, no website | whatever the payload says: VendorName, ProductName, **ProductWebsite** (`PS`), … |
| Config dir on the phone | `/usr/share/tohd-1/tohs/0000/0000/` | `/usr/share/tohd-1/tohs/<vid>/<pid>/` from the payload (planned: `0000/0001`) |
| 5 V after detection | stays on | stays on **only if the payload sets `PO` = true** |
| Depends on firmware? | **no**: detected even with no/crashed firmware | **yes**: no valid answer at 0x50 → cover not detected, 5 V likely off again |
| Use it for | flashing, debugging, new firmware, anything unstable | testing the "real product" path, the companion-app link (`PS`), demos |

**Rule: develop in DEV mode.** Switch to CHIP mode only once the firmware runs stably, and go back to DEV whenever the firmware is being reworked.

## What has to support both

### Hardware
- Breakout board: **both resistors fitted** (R1 6.2 kΩ, R2 10 kΩ), **JP2** (3-pad solder jumper, labelled DEV/CHIP) picks one. DEV is bridged at the factory. Switching = move the solder bridge (details: [pcb/breakout/README.md](pcb/breakout/README.md)). Never bridge all three pads (≈ 3.8 kΩ, unreserved value). Nothing else changes (contact board, cover, wiring, INT jumper)

### RP2040 firmware
- **Always** run both I²C targets, regardless of mode (in DEV mode nobody reads 0x50, so it does no harm):
  - **0x50**: memory-chip emulation, read-only image: `JTOH` header, CRC-32, VID, PID, CBOR payload at offset 0x10. Check the exact header layout in the spec ("Memory chip" section) and against Jolla's `toh-content` repo / symbiosis `create_toh_bin` before implementing
  - **own address (e.g. 0x42)**: our register protocol (status/event count, data, "enter bootloader")
  - The RP2040 has two I²C blocks (or use PIO), so both addresses can be served at once on the same pins
- Payload (planned): VID `0x0000` (reserved for development), PID `0x0001`, `VN`/`PN` names, `PS` = companion app / project URL, **`PO` = true**
- Must be answering at 0x50 well within 100 ms of power-on (RP2040 boots in a few ms; keep slow init after the I²C targets are up)

### Phone package (RPM)
- Installs the **same** YAML config into both `tohs/0000/0000/` (DEV mode) and `tohs/0000/0001/` (CHIP mode): `access: i2c-dev` for the polling service, `devices:` listing **both 0x42 and 0x50**, and the `user-unit` that starts/stops the polling service on attach/detach
- The polling service talks only to 0x42, so it works in both modes
- A future "install the companion app" helper (a small phone service that shows the cover's product link on attach) only gets a link in CHIP mode

## Switching modes

1. Cover off the phone
2. Move JP2 on the breakout board: DEV (6.2 kΩ) ↔ CHIP (10 kΩ)
3. CHIP mode only: firmware with the 0x50 image must be flashed and working (test on the desk first: logic analyzer or a second board reading 0x50)
4. Cover on, then check (below)

## Checking which mode the phone sees (over SSH, no root)

```
cat /sys/class/yft_pogo_pin/*adc_value      # A: 600–799, B: 800–999, nothing attached: ~1820
cat /sys/class/yft_pogo_pin/*int_state      # 0 = attached
cat /sys/class/yft_pogo_pin/*5v_out_state   # must stay 1 in both modes
gdbus call --system --dest org.sailfishos.tohd1 --object-path /org/sailfishos/tohd1 \
  --method org.freedesktop.DBus.ObjectManager.GetManagedObjects
# A: VendorId 0, ProductId 0.  B: VendorId 0, ProductId 1, ProductWebsite = the PS link
```

## If CHIP mode doesn't work: check first

- **Cover not detected / D-Bus shows nothing** → the phone got no valid image at 0x50: firmware not running, too slow (>100 ms), wrong header/CRC, or 0x50 not answering. Go back to DEV mode to confirm the rest still works, then look at the bus with the logic analyzer during attach
- **Detected, then the RP2040 goes dark** → payload without `PO` = true: symbiosis switched the 5 V off after detection
- **Detected, but the polling service doesn't start** → the config isn't in the dir matching the payload's VID/PID (`tohs/0000/0001/`), or 0x42 isn't listed under `devices:`
- **ADC reads 600–799 in CHIP mode** → JP2 still on DEV (bridge not cut). **ADC ~ 400–600 or 5 V switches off** → all three JP2 pads bridged (6.2 k ∥ 10 k)
- The general contact checks still apply first ([README.md](README.md), "If something goes wrong: check first": missing clips near the pads)
