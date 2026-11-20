// toh-i2c: talk to I2C devices on the Jolla Phone 2026's TOH bus without root (see internal/tohbus).
//
// Usage:
//
//	toh-i2c [-d ms] [-n count] <addr> [w <byte>...] [r <count>]
//	toh-i2c hold <seconds>
//
//	toh-i2c 0x42 w 0x00 r 6        read 6 bytes from register 0x00
//	toh-i2c 0x42 w 0x10 255 0 0    write 3 bytes from register 0x10 on
//	toh-i2c -d 50 -n 5 0x42 w 0 r 6   wait 50 ms after borrowing, then try up to 5 times (100 ms apart)
//	toh-i2c hold 30                keep the bus borrowed (5 V and pull-ups on) for 30 s, e.g. to measure SDA/SCL
//
// Prints read bytes as hex. Exit code 0 = success.
package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/godbus/dbus/v5"

	"toh-devkit/internal/tohbus"
)

func die(f string, a ...any) { fmt.Fprintf(os.Stderr, "toh-i2c: "+f+"\n", a...); os.Exit(1) }

func num(s string, max uint64) uint64 {
	v, err := strconv.ParseUint(s, 0, 32)
	if err != nil || v > max {
		die("bad number %q", s)
	}
	return v
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: toh-i2c [-d ms] [-n count] <addr> [w <byte>...] [r <count>]\n       toh-i2c hold <seconds>")
	os.Exit(2)
}

func main() {
	a := os.Args[1:]
	delay, tries := 0, 1
	for len(a) >= 2 && (a[0] == "-d" || a[0] == "-n") {
		if a[0] == "-d" {
			delay = int(num(a[1], 10000))
		} else {
			tries = int(num(a[1], 1000))
		}
		a = a[2:]
	}
	if len(a) < 2 {
		usage()
	}
	sys, err := dbus.SystemBus()
	if err != nil {
		die("system bus: %v", err)
	}
	if a[0] == "hold" {
		secs := num(a[1], 3600)
		_, release, err := tohbus.Borrow(sys)
		if err != nil {
			die("%v", err)
		}
		fmt.Printf("bus borrowed (5 V and pull-ups on) for %d s\n", secs)
		time.Sleep(time.Duration(secs) * time.Second)
		release()
		fmt.Println("returned")
		return
	}
	addr := uint16(num(a[0], 0x7f))
	var wr []byte
	rd := 0
	for i := 1; i < len(a); i++ {
		switch a[i] {
		case "w":
			for i+1 < len(a) && a[i+1] != "r" {
				i++
				wr = append(wr, byte(num(a[i], 0xff)))
			}
		case "r":
			if i+1 >= len(a) {
				die("r needs a count")
			}
			i++
			rd = int(num(a[i], 256))
		default:
			die("unexpected %q", a[i])
		}
	}
	fd, release, err := tohbus.Borrow(sys)
	if err != nil {
		die("%v", err)
	}
	defer release()
	time.Sleep(time.Duration(delay) * time.Millisecond)
	var r []byte
	for t := 1; ; t++ {
		r, err = tohbus.Xfer(fd, addr, wr, rd)
		if err == nil || t >= tries {
			break
		}
		time.Sleep(100 * time.Millisecond)
	}
	if err != nil {
		release()
		die("%v", err)
	}
	if rd > 0 {
		h := make([]string, len(r))
		for i, b := range r {
			h[i] = fmt.Sprintf("%02x", b)
		}
		fmt.Println(strings.Join(h, " "))
	}
}
