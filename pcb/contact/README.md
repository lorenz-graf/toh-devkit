# Contact PCB for the dev cover (v2)

Sits in the contact-board indent of the cTOH-M dev cover ([../../model/](../../model/)). Check image: [pcb-check.png](../../renders/pcb-check.png).

- **Bottom (B.Cu, faces the phone):** 7 contact pads, 2.3 mm (like Jolla's Inari Blue), at the pin positions. Flush with the cover's inner surface because the board is as thick as the indent is deep (0.6 mm)
- **Top (F.Cu, faces the cover floor):** traces to 7 wire pads (1 × 1 mm) that sit over the cover's 9 × 3 mm wire slot. Solder the wires there; they leave through the slot. Labels on the top are readable from outside through the slot
- **Vias** (0.3 mm, tented) connect the two sides
- **v2: made for all cover projects, 1 A on the power lines.** VIN (pin 1), GND (pin 2) and 5V (pin 7) are 0.5 mm wide (IPC-2221: ~1 A with a few °C rise; signals stay 0.2 mm) and get 1.2 mm wire pads for thicker wire. VIN and 5V run on the phone side through the free upper strip, each with its own via next to its wire pad. So the same board serves the dev cover (power from the phone) and battery covers like the chonk (up to 1 A into the phone through pin 1). Outline and contact pads are unchanged from v1
- Outline: indent minus 0.2 mm (L-shape, ≈ 27.1 × 10.45 mm)
- Wire pads, as seen from outside: top row `5V SCL ID VIN`, bottom row `GND INT SDA`. **VIN (pin 1): leave unconnected on the dev cover** (only battery/charging covers use it)
- ID: the 6.2 kΩ dev resistor goes on the breadboard (ID → GND)

## Files

- `make_board.py`: generates `dev-toh-contact.kicad_pcb` + `.kicad_pro` (JLCPCB-compatible rules) with KiCad 10's Python module. All positions are in the script (phone coords u/v; X = 100 − u, Y = 100 − v, top view = seen from behind the phone). Edit the script, not the board, then rerun
- Check: `kicad-cli pcb drc --severity-all -o drc.rpt dev-toh-contact.kicad_pcb` (must be 0)
- `fab/` + `dev-toh-contact-gerbers.zip`: Gerbers + Excellon drill for the order. Remake:
  `kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts --no-x2 -o fab/ dev-toh-contact.kicad_pcb` and `kicad-cli pcb export drill --format excellon --excellon-separate-th -o fab/ dev-toh-contact.kicad_pcb`, then zip the `.g*` + `.drl` files

## Ordering (JLCPCB)

Upload the zip; set: 2 layers, **thickness 0.6 mm**, **surface finish ENIG**, 5 pcs, any colour. Vias are already tented in the files. JLCPCB prints an order number on the silkscreen unless you pay to remove it or set a position; on a board this small, pick "remove" or accept it on the top side.
