# Firmware (RP2040-Zero)

`devkit-fw/`: I²C target at **0x42** for the TOH bus. Register map at the top of `devkit-fw.ino`. v0.5: magic `TOHD`, version, uptime, the Zero's RGB LED (0x10–0x12), an LED on GP14 (330 Ω to GND) (0x14, PWM), and bench registers (0x80 write port, 0x81 read port, 0x84–0x8B counters, 0x8C reset) for `toh-i2c bench`.

**The TOH bus doesn't support clock stretching** (checked with a logic analyzer): the phone keeps clocking while a target holds SCL low. So the firmware doesn't use the Arduino Wire library (its interrupt handler answered a read after ~9 µs, and the phone read garbage). Instead, core 1 polls the RP2040's I²C block from RAM and answers at once.

Known issue: the first read after the Zero restarts can return garbage, so check what you read (e.g. the `TOHD` magic) and retry.

Fixed in v0.4: after a garbled read the Zero could lock up holding SCL low until RESET. A pending TX abort is now cleared before a read is answered; while that flag was set, the RP2040's TX FIFO discarded the answer. Verified with the same fix in the TOH IR firmware (60 of 60 reads correct, no lock-up).

## Wiring (breadboard)

| Breakout header | RP2040-Zero |
|---|---|
| 5V | 5V |
| GND | GND |
| SDA | GP26 |
| SCL | GP15 |

No pull-ups (the phone has them). INT and ID stay unconnected.

On a breadboard, only the Zero's two long pin rows are usable. The pads on the short edge (GP9–GP13) would sit in the same breadboard strips and short each other, so leave them unused there; they're only usable on a board of their own.

## Build and flash (PC)

Needs `arduino-cli` with the Earle Philhower core and the NeoPixel library:

```
arduino-cli config add board_manager.additional_urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
arduino-cli core update-index && arduino-cli core install rp2040:rp2040
arduino-cli lib install "Adafruit NeoPixel"
arduino-cli compile --fqbn rp2040:rp2040:waveshare_rp2040_zero --output-dir ../build/fw devkit-fw
```

Flash: take the cover off the phone, hold the Zero's **BOOT** button while plugging USB-C into the PC (a drive `RPI-RP2` appears), then copy `build/fw/devkit-fw.ino.uf2` onto that drive. The Zero reboots into the firmware; its LED glows dim blue. Later flashes without the button: `toh-i2c 0x42 w 0xf0 0xb0` from the phone reboots it into the bootloader.
