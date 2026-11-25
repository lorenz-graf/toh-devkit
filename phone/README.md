# Phone side

One RPM with everything the phone needs for the TOH DevKit:

| Part | Installed as | What it does |
|---|---|---|
| `cmd/toh-i2c/` | `/usr/bin/toh-i2c` | command-line tool: one I²C transfer on the TOH bus, no root |
| `cmd/toh-devkitd/` | `/usr/libexec/toh-devkit/toh-devkitd` | session D-Bus service `io.github.lorenz_graf.TohDevkit`, started on demand (`app/io.github.lorenz_graf.TohDevkit.service`), exits after 5 idle minutes |
| `app/toh-devkit.qml` | app "TOH DevKit" (`sailfish-qml`) | GP14 LED switch + brightness, colour field + brightness for the RGB LED |
| `devkit.yaml` | `/usr/share/tohd-1/tohs/0000/0000/devkit.yaml` | symbiosis config for DEV mode: allows the two programs on the bus, lists 0x42 and 0x50 |

`internal/tohbus/` is the shared code: borrow the bus from symbiosis (`BorrowI2cDevAccess` on the system D-Bus, returns an fd), one `I2C_RDWR` transfer, return the bus. The phone's Python has no D-Bus module, hence Go (static binaries, like Jolla's own `inari-blue-notifier-daemon`).

## Build (PC)

Needs Go, Python 3 with Pillow (app icon) and `rpmbuild` (Arch: `pacman -S rpm-tools`):

```
./build-rpm.sh        # -> ../build/toh-devkit-<version>-<release>.aarch64.rpm
```

## Install

Copy the RPM to the phone and tap it in the file manager (developer mode on). Then **take the cover off and put it back on**: symbiosis reads the config only when a cover is attached. Remove it in Settings → Apps, or `devel-su pkcon remove toh-devkit`.

An update stops the running service (symbiosis refuses a program whose file was replaced); the next call starts the new one.

## Use

```
toh-i2c 0x42 w 0x00 r 6           # 54 4f 48 44 00 03 = "TOHD", version 0.3
toh-i2c 0x42 w 0x10 0 40 0        # RGB LED green
toh-i2c 0x42 w 0x14 255           # GP14 LED full
toh-i2c -d 50 -n 5 0x42 w 0 r 6   # wait 50 ms after borrowing, up to 5 tries
toh-i2c hold 30                   # keep the bus borrowed (5 V + pull-ups on) for 30 s, e.g. to measure SDA/SCL
toh-i2c bench 2                   # speed test (firmware 0.5+): kB/s per transfer size, write and read, every byte checked
gdbus call --session --dest io.github.lorenz_graf.TohDevkit --object-path /io/github/lorenz_graf/TohDevkit \
  --method io.github.lorenz_graf.TohDevkit.Info           # ('TOHD 0.3, up 7 s',)
```

Register map: top of [../firmware/devkit-fw/devkit-fw.ino](../firmware/devkit-fw/devkit-fw.ino).
