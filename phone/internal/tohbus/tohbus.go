// Package tohbus runs I2C transfers on the Jolla Phone 2026's TOH bus without root: it borrows the bus from
// symbiosis (system D-Bus org.sailfishos.tohd1, BorrowI2cDevAccess), runs one combined transfer (write, then
// repeated-start read) with the I2C_RDWR ioctl and returns the bus again.
// The calling executable must be listed under access: i2c-dev in the cover's YAML, the address under devices:.
package tohbus

import (
	"fmt"
	"runtime"
	"unsafe"

	"github.com/godbus/dbus/v5"
	"golang.org/x/sys/unix"
)

const (
	i2cRDWR = 0x0707 // ioctl I2C_RDWR
	i2cMRD  = 0x0001 // i2c_msg flag: read
	iface   = "org.sailfishos.tohd1.Toh"
)

// struct i2c_msg and struct i2c_rdwr_ioctl_data from <linux/i2c.h>, 64-bit layout
type i2cMsg struct {
	addr, flags, len uint16
	_                uint16
	buf              uintptr
}
type i2cRdwr struct {
	msgs  uintptr
	nmsgs uint32
	_     uint32
}

// ErrNotAttached means symbiosis has no cover (or refused the borrow).
type ErrNotAttached struct{ Err error }

func (e ErrNotAttached) Error() string {
	return fmt.Sprintf("borrow: %v (cover attached? executable listed under access: i2c-dev?)", e.Err)
}

// Borrow borrows the TOH bus from symbiosis. Call release() when done (returns the bus, closes the fd).
func Borrow(sys *dbus.Conn) (fd int, release func(), err error) {
	toh := sys.Object("org.sailfishos.tohd1", "/org/sailfishos/tohd1/toh")
	var ufd dbus.UnixFD
	if err := toh.Call(iface+".BorrowI2cDevAccess", 0).Store(&ufd); err != nil {
		return -1, nil, ErrNotAttached{err}
	}
	return int(ufd), func() {
		unix.Close(int(ufd))
		toh.Call(iface+".ReturnI2cDevAccess", 0)
	}, nil
}

// Transfer borrows the bus, runs one transfer (see Xfer) and returns the bus.
func Transfer(sys *dbus.Conn, addr uint16, wr []byte, rd int) ([]byte, error) {
	fd, release, err := Borrow(sys)
	if err != nil {
		return nil, err
	}
	defer release()
	return Xfer(fd, addr, wr, rd)
}

// Xfer writes wr (if any) and then reads rd bytes (if rd > 0) from addr, as one transaction, on a borrowed fd.
func Xfer(fd int, addr uint16, wr []byte, rd int) ([]byte, error) {
	if len(wr) == 0 && rd == 0 {
		return nil, fmt.Errorf("nothing to do")
	}
	rbuf := make([]byte, rd)
	var msgs []i2cMsg
	if len(wr) > 0 {
		msgs = append(msgs, i2cMsg{addr: addr, len: uint16(len(wr)), buf: uintptr(unsafe.Pointer(&wr[0]))})
	}
	if rd > 0 {
		msgs = append(msgs, i2cMsg{addr: addr, flags: i2cMRD, len: uint16(rd), buf: uintptr(unsafe.Pointer(&rbuf[0]))})
	}
	data := i2cRdwr{msgs: uintptr(unsafe.Pointer(&msgs[0])), nmsgs: uint32(len(msgs))}
	_, _, e := unix.Syscall(unix.SYS_IOCTL, uintptr(fd), i2cRDWR, uintptr(unsafe.Pointer(&data)))
	runtime.KeepAlive(wr)
	runtime.KeepAlive(rbuf)
	runtime.KeepAlive(msgs)
	runtime.KeepAlive(&data)
	if e != 0 {
		return nil, fmt.Errorf("transfer at 0x%02x: %v (no answer, or address not listed under devices:)", addr, e)
	}
	return rbuf, nil
}
