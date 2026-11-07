# Breakout board for the dev cover (v3)

Sits on the breadboard. The 6 wires from the contact board ([../contact/](../contact/), via the cover's wire slot) are soldered into the top row of holes; a 6-pin 2.54 mm male header on the bottom row plugs into the breadboard. Render: `../../renders/breakout.png`.

| Header pin | Signal | Note |
|---|---|---|
| 5V | phone 5 V after D1 | feeds the RP2040-Zero's 5V pin (live out of the box via JP4) |
| GND | GND | |
| SDA, SCL | I²C | no pull-ups (the phone has them) |
| INT | INT | tied to GND by JP1 (= "cover attached"). Cut JP1's bridge if the MCU should drive INT later |
| ID | ID | to GND through R1 6.2 kΩ (DEV mode) or R2 10 kΩ (CHIP mode), chosen by JP2; see below and [ID-modes.md](../../ID-modes.md) |

- **v3: through-hole or SMD.** D1, R1, R2 each have SMD pads (D1S: SMA, R1S/R2S: 1206) centred between their through-hole pads, in parallel (same nets). Fit one of the two per position, not both. D1S's cathode (pad 1) points toward the header like D1's; the silkscreen band between D1S and D1's cathode hole marks it for both. The SMD footprints have no courtyard (the overlap with the THT part is intended) and no silkscreen of their own. Bare render: `../../renders/breakout-bare.png`. v2 (THT only) is what was ordered: `dev-toh-breakout-v2-gerbers-ordered.zip`
- D1 1N5817 (Schottky) in the 5 V line: anode = phone side (top), cathode band (K) = header side. Stops the RP2040's USB 5 V from flowing back into the phone
- **ID mode selector JP2** (3-pad solder jumper at the top right, labelled DEV / CHIP): both resistors are fitted permanently; JP2 connects ID to one of them.
  - **DEV** (factory default, left + middle pad bridged): R1 **6.2 kΩ** = dev ID, works without firmware. Develop here
  - **CHIP**: cut the DEV bridge (knife between left and middle pad, check with the multimeter that ID–R1 is open), then bridge middle + right pad with solder: R2 **10 kΩ** = memory-chip mode, needs RP2040 firmware answering at 0x50 with `PO` = true
  - Back to DEV: remove the CHIP blob (solder wick), bridge left + middle again
  - Never bridge all three (that's 6.2 k ∥ 10 k ≈ 3.8 kΩ: unreserved value, the phone switches 5 V off)
- **5V MEAS** (bottom left): J3 (2-pin header) with **JP4** (solder jumper, **bridged** at the factory) in parallel. As shipped, 5 V just works through JP4; J3 can stay empty. **To measure** what the RP2040 and modules draw (limit 1 A): cut JP4 once (knife between the pads, check with the multimeter that it's open), then put the multimeter (current range) across J3. **From then on J3 must be bridged** (jumper cap or female–female Dupont wire) for normal use, or JP4 re-bridged with solder
- **JP3 "NO USB"** (2-pad solder jumper next to D1, **open** by default): bridges D1, so the modules get the full 5 V instead of ~4.6 V (e.g. the RDM630 wants 4.75–5.25 V). **Only while the RP2040 is NOT on USB**: bridged, nothing stops USB 5 V from flowing back into the phone. Open it again (solder wick) before plugging USB back in
- VIN (pin 1) is deliberately not brought out
- Parts: D1 1N5817 (diode kit) or SS14 (SMA), R1 6.2 kΩ + R2 10 kΩ (KUBOWAI kit; or 1206/0805), 1×6 + 1×2 male header (spare strip from an RP2040-Zero pack), jumper cap or a female–female Dupont wire for J3 (only needed after JP4 is cut)
- Wire holes: 1.0 mm, for the 28 AWG silicone wire (strip, push through, solder)

## Files

- `make_board.py` generates `dev-toh-breakout.kicad_pcb` + `.kicad_pro`; edit the script, not the board. DRC: `kicad-cli pcb drc --severity-all -o drc.rpt dev-toh-breakout.kicad_pcb` (0 errors)
- `dev-toh-breakout-gerbers.zip`: current design (v3), for an order. `dev-toh-breakout-v2-gerbers-ordered.zip`: what was ordered 2026-11-07 (same export commands as [../contact/README.md](../contact/README.md))

## Ordering (JLCPCB)

Separate item in the same order as the contact board: 2 layers, **1.6 mm**, HASL (lead-free) is fine, 5 pcs.
