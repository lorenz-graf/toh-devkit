// toh-devkitd: session D-Bus service between apps and the TOH DevKit's RP2040 (I2C address 0x42).
// Started on demand by D-Bus activation (io.github.lorenz_graf.TohDevkit.service) and exits after a few
// idle minutes. Each call borrows the TOH bus from symbiosis only for its own transfer (see internal/tohbus),
// so toh-i2c and other tools can use the bus in between.
//
// Interface io.github.lorenz_graf.TohDevkit at /io/github/lorenz_graf/TohDevkit:
//
//	Info() -> s                     "TOHD 0.2, up 123 s", or a D-Bus error if the cover isn't reachable
//	GetState() -> ai                [red, green, blue, gp14 led], each 0-255
//	SetRgb(i red, i green, i blue)  the Zero's RGB LED
//	SetLed(i brightness)            the LED on GP14 (PWM)
//	Transfer(y addr, ay write, i read) -> ay   raw transfer, for experiments
//
// Register map: firmware/devkit-fw/devkit-fw.ino.
package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/godbus/dbus/v5"
	"github.com/godbus/dbus/v5/introspect"

	"toh-devkit/internal/tohbus"
)

const (
	busName = "io.github.lorenz_graf.TohDevkit"
	objPath = "/io/github/lorenz_graf/TohDevkit"
	addr    = 0x42
	regLED  = 0x10 // red, green, blue
	regGP14 = 0x14
	idleFor = 5 * time.Minute
)

type service struct {
	sys  *dbus.Conn
	mu   sync.Mutex
	last time.Time
}

func dbusErr(err error) *dbus.Error {
	name := busName + ".Error.Failed"
	if _, ok := err.(tohbus.ErrNotAttached); ok {
		name = busName + ".Error.NotAttached"
	}
	return dbus.NewError(name, []any{err.Error()})
}

func (s *service) xfer(wr []byte, rd int) ([]byte, *dbus.Error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.last = time.Now()
	r, err := tohbus.Transfer(s.sys, addr, wr, rd)
	if err != nil {
		return nil, dbusErr(err)
	}
	return r, nil
}

func clamp(v int32) byte {
	if v < 0 {
		return 0
	}
	if v > 255 {
		return 255
	}
	return byte(v)
}

func (s *service) Info() (string, *dbus.Error) {
	r, e := s.xfer([]byte{0x00}, 10)
	if e != nil {
		return "", e
	}
	if string(r[:4]) != "TOHD" {
		return "", dbus.NewError(busName+".Error.Failed", []any{fmt.Sprintf("unexpected answer % x", r[:4])})
	}
	up := binary.LittleEndian.Uint32(r[6:10])
	return fmt.Sprintf("TOHD %d.%d, up %d s", r[4], r[5], up/1000), nil
}

func (s *service) GetState() ([]int32, *dbus.Error) {
	r, e := s.xfer([]byte{regLED}, 5) // 0x10-0x14
	if e != nil {
		return nil, e
	}
	return []int32{int32(r[0]), int32(r[1]), int32(r[2]), int32(r[4])}, nil
}

func (s *service) SetRgb(r, g, b int32) *dbus.Error {
	_, e := s.xfer([]byte{regLED, clamp(r), clamp(g), clamp(b)}, 0)
	return e
}

func (s *service) SetLed(v int32) *dbus.Error {
	_, e := s.xfer([]byte{regGP14, clamp(v)}, 0)
	return e
}

func (s *service) Transfer(a byte, wr []byte, rd int32) ([]byte, *dbus.Error) {
	if rd < 0 || rd > 256 {
		return nil, dbus.NewError(busName+".Error.Failed", []any{"read count 0-256"})
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.last = time.Now()
	r, err := tohbus.Transfer(s.sys, uint16(a), wr, int(rd))
	if err != nil {
		return nil, dbusErr(err)
	}
	return r, nil
}

func main() {
	sys, err := dbus.SystemBus()
	if err != nil {
		fmt.Fprintln(os.Stderr, "system bus:", err)
		os.Exit(1)
	}
	ses, err := dbus.SessionBus()
	if err != nil {
		fmt.Fprintln(os.Stderr, "session bus:", err)
		os.Exit(1)
	}
	s := &service{sys: sys, last: time.Now()}
	ses.Export(s, objPath, busName)
	node := &introspect.Node{Name: objPath, Interfaces: []introspect.Interface{
		introspect.IntrospectData,
		{Name: busName, Methods: introspect.Methods(s)},
	}}
	ses.Export(introspect.NewIntrospectable(node), objPath, "org.freedesktop.DBus.Introspectable")
	reply, err := ses.RequestName(busName, dbus.NameFlagDoNotQueue)
	if err != nil || reply != dbus.RequestNameReplyPrimaryOwner {
		fmt.Fprintln(os.Stderr, "name already taken or error:", err)
		os.Exit(1)
	}
	for range time.Tick(30 * time.Second) {
		s.mu.Lock()
		idle := time.Since(s.last) > idleFor
		s.mu.Unlock()
		if idle {
			os.Exit(0) // D-Bus activation starts it again on the next call
		}
	}
}
