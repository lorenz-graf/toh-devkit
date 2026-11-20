# Phone side

- `toh-i2c/`: command-line tool (Go, static aarch64 binary) that borrows the TOH I²C bus from symbiosis and runs one transfer. No root needed once it's allowed in the YAML. Build on the PC:
  `cd toh-i2c && CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -ldflags="-s -w" -o ../../build/toh-i2c .`
- `devkit.yaml`: symbiosis config for DEV mode (`0000/0000`): allows `/usr/local/bin/toh-i2c` on the bus and lists 0x42 and 0x50.

## Install (root, once)

Copy `build/toh-i2c` and `phone/devkit.yaml` to `~` on the phone, then:

```
devel-su sh -c 'install -m 755 ~defaultuser/toh-i2c /usr/local/bin/toh-i2c && mkdir -p /usr/share/tohd-1/tohs/0000/0000 && install -m 644 ~defaultuser/devkit.yaml /usr/share/tohd-1/tohs/0000/0000/devkit.yaml'
```

Then take the cover off and put it back on (symbiosis reads the YAML on attach). Undo: `devel-su rm -r /usr/share/tohd-1/tohs/0000 /usr/local/bin/toh-i2c`

## Use

```
toh-i2c 0x42 w 0x00 r 6        # 54 4f 48 44 00 01 = "TOHD", version 0.1
toh-i2c 0x42 w 0x10 40 0 0     # LED red
```
