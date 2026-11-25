package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"time"

	"toh-devkit/internal/tohbus"
)

// Bench registers of the DevKit firmware (v0.5+), see firmware/devkit-fw/devkit-fw.ino.
const (
	regSink    = 0x80 // write port, checks the pattern 0, 1, 2, ...
	regSource  = 0x81 // read port, returns 0, 1, 2, ...
	regBCount  = 0x84 // uint32 LE bytes received at regSink, then uint32 LE pattern errors
	regBReset  = 0x8C
	bResetMagc = 0x5A
)

var benchSizes = []int{1, 16, 32, 64, 128, 255, 256, 512, 1024, 2048, 4096, 8192}

// bench measures how fast payload bytes go to and from the firmware's bench ports, per transfer size.
// Write: one I2C write [regSink, payload...] per transfer. Read: write [regSource], repeated start, read payload.
// Every byte is checked: the firmware counts what arrived and pattern errors, reads are compared here.
func bench(fd int, addr uint16, per time.Duration) error {
	// The first read after a Zero restart can be garbage: retry until the magic and a bench-capable version show up.
	var id []byte
	var err error
	for t := 0; t < 5; t++ {
		if id, err = tohbus.Xfer(fd, addr, []byte{0}, 6); err == nil && bytes.Equal(id[:4], []byte("TOHD")) {
			break
		}
		time.Sleep(50 * time.Millisecond)
	}
	if err != nil || !bytes.Equal(id[:4], []byte("TOHD")) {
		return fmt.Errorf("no DevKit firmware at 0x%02x (%v, got % x)", addr, err, id)
	}
	if id[4] == 0 && id[5] < 5 {
		return fmt.Errorf("firmware %d.%d has no bench registers, needs 0.5+", id[4], id[5])
	}
	fmt.Printf("firmware %d.%d at 0x%02x, %v per size and direction\n", id[4], id[5], addr, per)
	fmt.Printf("%6s | %10s %8s %10s | %10s %8s %10s\n", "size", "write kB/s", "xfer/s", "errors", "read kB/s", "xfer/s", "errors")

	pat := make([]byte, 1+benchSizes[len(benchSizes)-1])
	pat[0] = regSink
	for i := 1; i < len(pat); i++ {
		pat[i] = byte(i - 1)
	}
	for _, n := range benchSizes {
		// ---- write ----
		wcol := ""
		if _, err := tohbus.Xfer(fd, addr, []byte{regBReset, bResetMagc}, 0); err != nil {
			return fmt.Errorf("reset counters: %v", err)
		}
		xf, fails, sent := 0, 0, 0
		var firstErr error
		start := time.Now()
		for time.Since(start) < per {
			if _, err := tohbus.Xfer(fd, addr, pat[:1+n], 0); err != nil {
				fails++
				if firstErr == nil {
					firstErr = err
				}
				if xf == 0 && fails >= 3 {
					break // size not accepted at all
				}
				continue
			}
			xf++
			sent += n
		}
		el := time.Since(start).Seconds()
		st, err := tohbus.Xfer(fd, addr, []byte{regBCount}, 8)
		if xf == 0 {
			wcol = fmt.Sprintf("%10s %8s %10s", "failed", "-", "-")
		} else if err != nil {
			wcol = fmt.Sprintf("%10.1f %8.0f %10s", float64(sent)/el/1000, float64(xf)/el, "counter?")
		} else {
			got, perr := binary.LittleEndian.Uint32(st[0:4]), binary.LittleEndian.Uint32(st[4:8])
			e := fmt.Sprintf("%d", perr)
			if int(got) != sent {
				e = fmt.Sprintf("%d,%+d B", perr, int(got)-sent)
			}
			if fails > 0 {
				e += fmt.Sprintf(",%dx", fails)
			}
			wcol = fmt.Sprintf("%10.1f %8.0f %10s", float64(sent)/el/1000, float64(xf)/el, e)
		}
		// ---- read ----
		rcol := ""
		xf, fails = 0, 0
		got, bad := 0, 0
		var rErr error
		start = time.Now()
		for time.Since(start) < per {
			r, err := tohbus.Xfer(fd, addr, []byte{regSource}, n)
			if err != nil {
				fails++
				if rErr == nil {
					rErr = err
				}
				if xf == 0 && fails >= 3 {
					break
				}
				continue
			}
			xf++
			got += n
			for i, b := range r {
				if b != byte(i) {
					bad++
				}
			}
		}
		el = time.Since(start).Seconds()
		if xf == 0 {
			rcol = fmt.Sprintf("%10s %8s %10s", "failed", "-", "-")
		} else {
			e := fmt.Sprintf("%d", bad)
			if fails > 0 {
				e += fmt.Sprintf(",%dx", fails)
			}
			rcol = fmt.Sprintf("%10.1f %8.0f %10s", float64(got)/el/1000, float64(xf)/el, e)
		}
		fmt.Printf("%6d | %s | %s\n", n, wcol, rcol)
		if firstErr != nil {
			fmt.Printf("       write error: %v\n", firstErr)
		}
		if rErr != nil {
			fmt.Printf("       read error: %v\n", rErr)
		}
	}
	fmt.Println("errors: wrong bytes (write: pattern errors in the firmware, ±B = bytes lost/extra), Nx = failed transfers")
	return nil
}
