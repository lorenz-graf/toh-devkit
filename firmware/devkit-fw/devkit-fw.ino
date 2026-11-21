// TOH DevKit firmware v0.4: RP2040-Zero as I2C target for the Jolla Phone 2026's TOH connector.
// Board: Waveshare RP2040-Zero, Arduino core "Raspberry Pi Pico/RP2040" by Earle Philhower (rp2040:rp2040).
// Build/flash: see ../README.md.
//
// Wiring (breakout header -> Zero): 5V -> 5V, GND -> GND, SDA -> GP26, SCL -> GP15 (both on the RP2040's I2C1 block).
// The phone has the pull-ups and switches them on only while a program has borrowed the bus.
//
// WHY NO Wire LIBRARY: the TOH bus is an I3C bus, and its controller does NOT support clock stretching (verified with
// a logic analyzer: it keeps clocking while the target holds SCL low). The RP2040's I2C block holds SCL low after a
// read address until the firmware puts the first byte into its TX FIFO. With the Wire library's interrupt handler
// that took ~9 us, so the phone read shifted/garbage bytes. Here core 1 does nothing but poll the I2C block from RAM
// and answers a read request within a fraction of a microsecond, shorter than the controller's own SCL low phase.
//
// Register protocol (address 0x42): write [reg, data...] to write from reg on; write [reg] then read N bytes to
// read from reg on. The register pointer auto-increments.
//   0x00-0x03  R   magic "TOHD"
//   0x04-0x05  R   firmware version major, minor
//   0x06-0x09  R   uptime in ms, uint32 little endian (snapshot taken when the pointer is set to 0x00-0x09)
//   0x10-0x12  RW  RGB LED red, green, blue (the Zero's WS2812 on GP16)
//   0x14       RW  LED on GP14 (through a 330 Ohm resistor to GND), brightness 0-255 (PWM)
//   0xF0       W   write 0xB0 = reboot into the USB bootloader (BOOTSEL), for flashing without the button
#include <hardware/i2c.h>
#include <hardware/gpio.h>
#include <Adafruit_NeoPixel.h>
// Diagnostics: build with DEBUG_SERIAL=1 to print counters over USB serial once a second
// (arduino-cli ... --build-property "compiler.cpp.extra_flags=-DDEBUG_SERIAL=1").
#ifndef DEBUG_SERIAL
#define DEBUG_SERIAL 0
#endif

const uint8_t ADDR = 0x42, PIN_SDA = 26, PIN_SCL = 15, PIN_LED = 16, PIN_GP14 = 14;
#define I2C_HW i2c1   // the block that owns PIN_SDA/PIN_SCL: i2c0 for e.g. GP0/1 or GP28/29, i2c1 for GP26/GP15
const uint8_t VER_MAJOR = 0, VER_MINOR = 4;
const uint8_t REG_UPTIME = 0x06, REG_LED = 0x10, REG_GP14 = 0x14, REG_BOOT = 0xF0, BOOT_MAGIC = 0xB0;

// The Zero's LED takes red, green, blue in this order (NEO_GRB showed green as red)
Adafruit_NeoPixel led(1, PIN_LED, NEO_RGB + NEO_KHZ800);
volatile uint8_t regs[256];
volatile bool ledDirty = true, gp14Dirty = true, bootReq = false;
volatile uint32_t nWrites = 0, nReads = 0, nAborts = 0, nLoops = 0;

static void __not_in_flash_func(snapshotUptime)() {
  uint32_t t = millis();
  for (int i = 0; i < 4; i++) regs[REG_UPTIME + i] = (t >> (8 * i)) & 0xFF;
}

// Core 1: poll the I2C block forever. Runs from RAM so a flash cache miss can't delay an answer.
static void __not_in_flash_func(i2cTargetLoop)() {
  i2c_hw_t *h = I2C_HW->hw;
  uint8_t ptr = 0;
  for (;;) {
#if DEBUG_SERIAL
    nLoops++;
#endif
    uint32_t raw = h->raw_intr_stat;
    // v0.4 lock-up fix: clear a pending TX abort BEFORE answering a read. While the abort flag is set, the TX FIFO
    // discards writes, so the answer got lost and the RP2040 held SCL low until a reset.
    if (raw & I2C_IC_RAW_INTR_STAT_TX_ABRT_BITS) { (void)h->clr_tx_abrt; nAborts++; }  // e.g. leftover byte flushed
    if (raw & I2C_IC_RAW_INTR_STAT_RD_REQ_BITS) {            // controller wants a byte: answer at once
      h->data_cmd = regs[ptr++];
      (void)h->clr_rd_req;
      nReads++;
    }
    while (h->status & I2C_IC_STATUS_RFNE_BITS) {            // received bytes
      uint32_t dc = h->data_cmd;
      uint8_t v = dc & 0xFF;
      if (dc & I2C_IC_DATA_CMD_FIRST_DATA_BYTE_BITS) {       // first byte after the address = register pointer
        ptr = v;
        if (ptr <= REG_UPTIME + 3) snapshotUptime();
        nWrites++;
      } else {
        if (ptr >= REG_LED && ptr <= REG_LED + 2) { regs[ptr] = v; ledDirty = true; }
        else if (ptr == REG_GP14) { regs[ptr] = v; gp14Dirty = true; }
        else if (ptr == REG_BOOT && v == BOOT_MAGIC) bootReq = true;
        ptr++;                                                 // writes to read-only registers are ignored
      }
    }
    if (raw & I2C_IC_RAW_INTR_STAT_STOP_DET_BITS) (void)h->clr_stop_det;
    if (raw & I2C_IC_RAW_INTR_STAT_START_DET_BITS) (void)h->clr_start_det;
    if (raw & I2C_IC_RAW_INTR_STAT_RESTART_DET_BITS) (void)h->clr_restart_det;
  }
}

void setup() {
#if DEBUG_SERIAL
  Serial.begin(115200);
#endif
  regs[0] = 'T'; regs[1] = 'O'; regs[2] = 'H'; regs[3] = 'D';
  regs[4] = VER_MAJOR; regs[5] = VER_MINOR;
  regs[REG_LED] = 0; regs[REG_LED + 1] = 0; regs[REG_LED + 2] = 8;  // dim blue = "running, nothing received yet"
  regs[REG_GP14] = 0;
  pinMode(PIN_GP14, OUTPUT);
  led.begin();
}

void setup1() {
  // 1 MHz settings: short spike filter and SDA hold time, so the answer goes out early
  i2c_init(I2C_HW, 1000000);
  i2c_set_slave_mode(I2C_HW, true, ADDR);
  gpio_set_function(PIN_SDA, GPIO_FUNC_I2C);
  gpio_set_function(PIN_SCL, GPIO_FUNC_I2C);
  gpio_pull_up(PIN_SDA);  // weak (~50 kOhm) internal pull-ups only keep the lines defined while the phone's are off
  gpio_pull_up(PIN_SCL);
  i2cTargetLoop();        // never returns
}

void loop1() {}

void loop() {
  if (ledDirty) {
    ledDirty = false;
    led.setPixelColor(0, led.Color(regs[REG_LED], regs[REG_LED + 1], regs[REG_LED + 2]));
    led.show();
  }
  if (gp14Dirty) {
    gp14Dirty = false;
    analogWrite(PIN_GP14, regs[REG_GP14]);  // default range 0-255
  }
#if DEBUG_SERIAL
  static uint32_t next = 0;
  if (millis() >= next) {
    next = millis() + 1000;
    i2c_hw_t *h = I2C_HW->hw;
    Serial.printf("t=%lu loops=%lu writes=%lu reads=%lu aborts=%lu | status=%02lx raw=%04lx abrt_src=%05lx txflr=%lu rxflr=%lu en=%lu | sda=%d scl=%d\n",
                  millis(), nLoops, nWrites, nReads, nAborts, h->status, h->raw_intr_stat, h->tx_abrt_source, h->txflr,
                  h->rxflr, h->enable_status, gpio_get(PIN_SDA), gpio_get(PIN_SCL));
  }
#endif
  if (bootReq) { delay(20); rp2040.rebootToBootloader(); }
}
